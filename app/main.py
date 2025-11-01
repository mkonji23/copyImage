from copy import deepcopy
import os
import re
import subprocess
import sys
import traceback
from dialogs import PathDialog
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfReader, PdfWriter
import io

# ✅ ConfigDialog는 이미 따로 정의되어 있다고 가정
from dialog_pdf_config import DialogPdfConfig  # <- 따로 만든 클래스 import
from dialog_user_manager import DialogUserManager
from config import DEFAULT_DST, DEFAULT_SRC, load_previous_config, save_config
from copy_utils import copy_images
from log_utils import append_log
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ImageCopyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("이미지 파일 복사기")
        self.resize(500, 450)

        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")

        # 아이콘 기본값 처리
        icon_path = os.path.join(base_path, "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 중앙 위젯
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # --- 파일명 입력 라인 ---
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("파일명 입력(콤마(,) 구분):"))
        layout.addLayout(h3)

        # input, 초기화 버튼
        h4 = QHBoxLayout()

        # input
        self.files_input = QLineEdit()
        h4.addWidget(self.files_input)
        # Enter 키 입력 시 pdf 실행
        self.files_input.returnPressed.connect(self.save_images_to_pdf_with_template)

        # 이미지 선택 버튼
        image_sel_btn = QPushButton("이미지 선택")
        image_sel_btn.clicked.connect(self.select_src_files)
        h4.addWidget(image_sel_btn)

        # 초기화 버튼
        clear_btn = QPushButton("초기화")
        clear_btn.clicked.connect(self.clear_input)
        h4.addWidget(clear_btn)

        layout.addLayout(h4)

        # 폴더 열기 버튼
        h5 = QHBoxLayout()
        self.run_btn = QPushButton("pdf 폴더 열기")
        self.run_btn.clicked.connect(self.open_folder)
        h5.addWidget(self.run_btn)
        layout.addLayout(h5)

        self.run_btn = QPushButton("PDF 위치")
        self.run_btn.clicked.connect(self.open_config_dialog)
        h5.addWidget(self.run_btn)
        layout.addLayout(h5)

        # PDF 저장 버튼
        h6 = QHBoxLayout()
        self.pdf_btn = QPushButton("PDF로 저장")
        self.pdf_btn.clicked.connect(self.save_images_to_pdf_with_template)
        h6.addWidget(self.pdf_btn)
        layout.addLayout(h6)

        layout.addWidget(QLabel("로그:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)
        central.setLayout(layout)

        # --- 메뉴 ---
        menu_bar = self.menuBar()

        # 🔹 설정 메뉴 (기존 "파일" → "설정")
        settings_menu = menu_bar.addMenu("설정")

        # 각 메뉴 액션 생성
        path_config_action = QAction("경로 설정 열기", self)
        path_answer_action = QAction("오답노트 설정", self)
        pdf_config_action = QAction("PDF 설정", self)
        close_action = QAction("닫기", self)

        # 메뉴에 추가
        settings_menu.addAction(path_config_action)
        settings_menu.addAction(path_answer_action)
        settings_menu.addAction(pdf_config_action)
        settings_menu.addSeparator()
        settings_menu.addSeparator()
        settings_menu.addAction(close_action)

        # 시그널 연결
        path_config_action.triggered.connect(self.open_path_dialog)
        path_answer_action.triggered.connect(self.open_config_user)
        pdf_config_action.triggered.connect(self.open_config_dialog)
        close_action.triggered.connect(self.close)

        # 🔹 정보 메뉴
        info_menu = menu_bar.addMenu("정보")
        info_action = QAction("버전확인", self)
        info_menu.addAction(info_action)
        info_action.triggered.connect(self.show_version_dialog)

        # 프로그램 시작 로그
        append_log(self.log_output, "🟢 프로그램 시작")

        # prevConfig.json 없으면 초기 설정
        self.initialize_config()

    # 닫기 이벤트
    def closeEvent(self, event):
        print("닫기 버튼 눌림!")
        self.save_local_config()
        event.accept()

    # 키 이벤트 재정의
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.open_folder()

    def clear_input(self):
        self.files_input.clear()

    def log(self, message):
        append_log(self.log_output, message)

    def open_path_dialog(self):
        dlg = PathDialog(self)
        if dlg.exec():
            self.log("경로 설정 저장 완료!")

    def open_config_dialog(self):
        dialog = DialogPdfConfig(self)
        if dialog.exec():
            self.log("PDF 설정 완료!")

    # 사용자 설정
    def open_config_user(self):
        dialog = DialogUserManager(parent=self, parent_app=self)
        if dialog.exec():
            self.log("사용자 설정 완료!")

    def initialize_config(self):
        if not os.path.exists("prevConfig.json"):
            QMessageBox.information(
                self,
                "초기 설정",
                "prevConfig.json이 없습니다.\n초기 설정을 진행합니다.\n원본 폴더, 대상 폴더, PDF 템플릿을 선택해주세요.",
            )

            src_folder = QFileDialog.getExistingDirectory(self, "원본 폴더 선택 (초기 설정)")
            if not src_folder:
                src_folder = DEFAULT_SRC

            dst_folder = QFileDialog.getExistingDirectory(self, "대상 폴더 선택 (초기 설정)")
            if not dst_folder:
                dst_folder = DEFAULT_DST

            file_path, _ = QFileDialog.getOpenFileName(self, "템플릿 선택", "", "PDF Files (*.pdf)")

            config = {
                "source_dir": src_folder,
                "target_dir": dst_folder,
                "template_dir": file_path,
                "file_names": "",
            }
            self.config.update(config)
            save_config(self.config)
            self.files_input.setText("")
            self.log("🟢 초기 설정 완료: prevConfig.json 생성됨")
        else:
            self.config = load_previous_config()
            self.files_input.setText(self.config.get("file_names", ""))

    def open_folder(self):
        self.config = load_previous_config()
        target = self.config.get("target_dir", DEFAULT_DST)
        target_path = os.path.abspath(target)
        subprocess.Popen(f'explorer "{target_path}"')

    def save_local_config(self):
        self.config = load_previous_config()
        source = self.config.get("source_dir", DEFAULT_SRC)
        target = self.config.get("target_dir", DEFAULT_DST)
        pdf = self.config.get("template_dir", "")
        target_path = os.path.abspath(target)

        self.config.update(
            {
                "source_dir": source,
                "target_dir": target_path,
                "template_dir": pdf,
                "file_names": self.files_input.text(),
            }
        )
        save_config(self.config)

    def select_src_files(self):
        self.config = load_previous_config()
        folder = self.config.get("source_dir", DEFAULT_SRC)
        if not folder or not os.path.exists(folder):
            self.log("⚠️ 원본 폴더가 존재하지 않습니다")
            return

        files, _ = QFileDialog.getOpenFileNames(self, "원본 파일 선택", folder)
        if files:
            names = [os.path.splitext(os.path.basename(f))[0] for f in files]
            self.files_input.setText(", ".join(names))
            self.log(f"🟢 {len(names)}개 파일 선택됨")

    def show_version_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("버전 정보")
        dialog.resize(300, 150)
        layout = QVBoxLayout(dialog)
        version = "v1.0.0"
        date_str = "2025-08-17"
        layout.addWidget(QLabel("안뇽~~"))
        layout.addWidget(QLabel(f"프로그램 버전: {version}"))
        layout.addWidget(QLabel(f"빌드 날짜: {date_str}"))
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        dialog.exec()

    def save_images_to_pdf_with_template(self):
        self.config = load_previous_config()
        source_dir = self.config.get("source_dir", "")
        input_files = [f.strip() for f in self.files_input.text().split(",") if f.strip()]

        allowed_exts = (".jpg", ".jpeg", ".png", ".bmp", ".gif")

        files = []
        for f in input_files:
            found = False
            if os.path.splitext(f)[1].lower() in allowed_exts:
                full_path = os.path.join(source_dir, f)
                if os.path.isfile(full_path):
                    files.append(full_path)
                    found = True
            else:
                for ext in allowed_exts:
                    full_path = os.path.join(source_dir, f + ext)
                    if os.path.isfile(full_path):
                        files.append(full_path)
                        found = True
                        break
            if not found:
                self.log(f"파일 없음: {f}")

        if not files:
            self.log("❌ 유효한 이미지 파일이 없습니다")
            return

        folder = self.config.get("target_dir", DEFAULT_DST)
        if not os.path.exists(folder):
            os.makedirs(folder)

        pdf_path = os.path.join(folder, "이미지_모음.pdf")
        counter = 1
        while os.path.exists(pdf_path):
            pdf_path = os.path.join(folder, f"이미지_모음_{counter}.pdf")
            counter += 1

        self.log(f"🟢 PDF 생성 시작: {pdf_path}")

        template_path = self.config.get("template_dir", "")
        if not template_path or not os.path.isfile(template_path):
            self.log("❌ 템플릿 경로가 없습니다.")
            return

        template_reader = PdfReader(template_path)
        template_page = template_reader.pages[0]
        writer = PdfWriter()

        page_w, page_h = A4
        cfg = self.config
        h_margin = cfg.get("h_margin", 20)
        v_margin = cfg.get("v_margin", 30)
        target_w = cfg.get("target_w", 300)
        target_h = cfg.get("target_h", 160)
        img_h = (page_h - (2 + 1) * v_margin) / 2

        for i, img_file in enumerate(files):
            idx_in_page = i % 2

            if idx_in_page == 0:
                packet = io.BytesIO()
                c = canvas.Canvas(packet, pagesize=A4)

            row = idx_in_page
            x = h_margin
            y = page_h - v_margin - (row + 1) * img_h - row * v_margin

            if idx_in_page == 0:
                x_offset = cfg.get("x_offset1", 0)
                y_offset = cfg.get("y_offset1", -50)
            else:
                x_offset = cfg.get("x_offset2", 0)
                y_offset = cfg.get("y_offset2", 10)

            try:
                img = ImageReader(img_file)
                iw, ih = img.getSize()
                ratio = min(target_w / iw, target_h / ih)
                draw_w = iw * ratio
                draw_h = ih * ratio
                draw_x = x + (target_w - draw_w) / 2 + x_offset
                draw_y = y + (target_h - draw_h) / 2 + y_offset
                c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
            except Exception as e:
                print(f"⚠️ 이미지 삽입 실패: {img_file} ({e})")

            if idx_in_page == 1 or i == len(files) - 1:
                c.save()
                packet.seek(0)
                overlay_pdf = PdfReader(packet)
                base_page = deepcopy(template_page)
                base_page.merge_page(overlay_pdf.pages[0])
                writer.add_page(base_page)

        with open(pdf_path, "wb") as f:
            writer.write(f)

        self.save_local_config()
        self.log(f"✅ PDF 저장 완료: {pdf_path}")

        if sys.platform == "win32":
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", pdf_path])
        elif sys.platform == "linux":
            subprocess.Popen(["xdg-open", pdf_path])

    def save_images_to_pdf_for_dialog_users(self, users):
        """
        Dialog 전용 PDF 생성
        users = [
            {
                "name": "홍길동",
                "note_title": "오답노트1",
                "note_numbers": ["001", "002", "003"]
            },
            ...
        ]
        """
        source_dir = self.config.get("source_dir", "")
        template_path = self.config.get("template_dir", "")
        if not template_path or not os.path.isfile(template_path):
            self.log("❌ 템플릿 경로가 없습니다.")
            return

        template_reader = PdfReader(template_path)
        template_page = template_reader.pages[0]
        page_w, page_h = A4
        cfg = self.config
        h_margin = cfg.get("h_margin", 20)
        v_margin = cfg.get("v_margin", 30)
        target_w = cfg.get("target_w", 300)
        target_h = cfg.get("target_h", 160)
        img_h = (page_h - (2 + 1) * v_margin) / 2
        allowed_exts = (".jpg", ".jpeg", ".png", ".bmp", ".gif")

        for user in users:
            try:
                user_folder = os.path.join(cfg.get("target_dir", DEFAULT_DST), user["name"])
                os.makedirs(user_folder, exist_ok=True)

                # 파일명
                base_pdf_name = f"{user['name']}_{user['note_title']}.pdf"
                pdf_path = os.path.join(user_folder, base_pdf_name)
                counter = 1
                while os.path.exists(pdf_path):
                    pdf_path = os.path.join(user_folder, f"{user['name']}_{user['note_title']}_{counter}.pdf")
                    counter += 1

                writer = PdfWriter()

                for i, note_number in enumerate(user["note_numbers"]):
                    note_number = note_number.strip()
                    if not note_number:
                        continue

                    # 이미지 파일 확인 (jpg 기준)
                    img_file = os.path.join(source_dir, f"{note_number}.jpg")
                    if not os.path.isfile(img_file):
                        self.log(f"⚠️ 이미지 파일 없음: {img_file}")
                        continue

                    idx_in_page = i % 2  # 페이지 당 2개 이미지
                    if idx_in_page == 0:
                        packet = io.BytesIO()
                        c = canvas.Canvas(packet, pagesize=A4)

                    row = idx_in_page
                    x = h_margin
                    y = page_h - v_margin - (row + 1) * img_h - row * v_margin

                    x_offset = cfg.get("x_offset1", 0) if idx_in_page == 0 else cfg.get("x_offset2", 0)
                    y_offset = cfg.get("y_offset1", -50) if idx_in_page == 0 else cfg.get("y_offset2", 10)

                    try:
                        img = ImageReader(img_file)
                        iw, ih = img.getSize()
                        ratio = min(target_w / iw, target_h / ih)
                        draw_w = iw * ratio
                        draw_h = ih * ratio
                        draw_x = x + (target_w - draw_w) / 2 + x_offset
                        draw_y = y + (target_h - draw_h) / 2 + y_offset
                        c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
                    except Exception as e:
                        self.log(f"⚠️ 이미지 삽입 실패: {img_file} ({e})")
                        continue

                    if idx_in_page == 1 or i == len(user["note_numbers"]) - 1:
                        c.save()
                        packet.seek(0)
                        overlay_pdf = PdfReader(packet)
                        base_page_copy = deepcopy(template_page)
                        base_page_copy.merge_page(overlay_pdf.pages[0])
                        writer.add_page(base_page_copy)

                with open(pdf_path, "wb") as f:
                    writer.write(f)
                self.log(f"✅ PDF 다중생성 완료: {pdf_path}")
            except Exception as e:
                self.log(f"❌ 사용자 {user['name']} PDF 생성 실패: {e}")
        QMessageBox.information(self, "알림", "PDF 생성완료.")


# --- 실행 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageCopyApp()
    sys.app_window = window
    window.show()
    sys.exit(app.exec())
