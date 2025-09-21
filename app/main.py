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
    QWidgetAction,
)


class ImageCopyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("이미지 파일 복사기")
        self.resize(500, 450)

        if getattr(sys, "frozen", False):
            # onefile 실행 시 임시 폴더
            base_path = sys._MEIPASS
        else:
            # 개발 환경
            base_path = os.path.abspath(".")
        # 아이콘 기본값 처리
        icon_path = os.path.join(base_path, "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 중앙 위젯
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        # 경로 버튼
        self.path_config_btn = QPushButton("경로 설정 열기")
        self.path_config_btn.clicked.connect(self.open_path_dialog)
        layout.addWidget(self.path_config_btn)

        self.files_input = QLineEdit()
        self.run_btn = QPushButton("pdf 폴더 열기")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        # 설정
        self.btn_pdf_setting = QPushButton("PDF설정")
        self.btn_pdf_setting.clicked.connect(self.open_config_dialog)
        # 출력버튼
        self.pdf_btn = QPushButton("PDF로 저장")
        self.pdf_btn.clicked.connect(self.save_images_to_pdf_with_template)
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

        # h5 로그
        h5 = QHBoxLayout()
        h5.addWidget(self.run_btn)
        layout.addLayout(h5)
        # pdf버튼
        # h5 로그
        h6 = QHBoxLayout()
        layout.addLayout(h6)
        h6.addWidget(self.btn_pdf_setting)
        h6.addWidget(self.pdf_btn)
        layout.addWidget(QLabel("로그:"))
        layout.addWidget(self.log_output)
        central.setLayout(layout)

        # 메뉴
        menu_bar = self.menuBar()

        # 파일 메뉴
        file_menu = menu_bar.addMenu("파일")
        default_action = QAction("경로 초기화", self)
        template_action = QAction("PDF 템플릿 설정", self)
        close_action = QAction("닫기", self)

        file_menu.addAction(default_action)
        file_menu.addAction(template_action)
        file_menu.addAction(close_action)

        # 설정 메뉴

        # 오른쪽 끝에 띄우기 위해 스페이서 위젯
        info_menu = menu_bar.addMenu("정보")
        info_action = QAction("버전확인", self)
        info_menu.addAction(info_action)

        # 시그널 연결
        self.run_btn.clicked.connect(self.open_folder)
        close_action.triggered.connect(self.close)

        info_action.triggered.connect(self.show_version_dialog)

        # 프로그램 시작 로그
        append_log(self.log_output, "🟢 프로그램 시작")

        # prevConfig.json 없으면 초기 설정
        self.initialize_config()

    # 닫기 이벤트
    def closeEvent(self, event):
        print("닫기 버튼 눌림!")
        self.save_local_config
        # event.accept()  # 닫기 허용
        # event.ignore()  # 닫기 막기
        event.accept()  # 보통 닫기 허용

    # 키 이벤트 재정의
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.open_folder()

    def clear_input(self):
        self.files_input.clear()

    # --- 로그 ---
    def log(self, message):
        append_log(self.log_output, message)

    # --- 폴더 선택 ---
    def choose_src_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "원본 폴더 선택")
        if folder:
            self.src_input.setText(folder)

    def choose_dst_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "대상 폴더 선택")
        if folder:
            self.dst_input.setText(folder)

    # 설정 창 열기
    def open_path_dialog(self):
        dlg = PathDialog(self)
        if dlg.exec():  # 확인 버튼 클릭 시 True 반환
            self.log("경로 설정 저장 완료!")

    def open_config_dialog(self):
        dialog = DialogPdfConfig(self)
        if dialog.exec():  # OK 눌렀을 때만
            # ✅ 업데이트된 값 가져오기
            self.log("pdf 설정  완료!")

    # --- 초기 설정 (첫 실행) ---
    def initialize_config(self):
        if not os.path.exists("prevConfig.json"):
            # 알림창
            QMessageBox.information(
                self,
                "초기 설정",
                "prevConfig.json이 없습니다.\n초기 설정을 진행합니다.\n원본 폴더,대상 폴더, pdf 템플릿을, 선택해주세요.\n이후에 재설정이 가능합니다.",
            )

            # 원본 폴더 선택
            src_folder = QFileDialog.getExistingDirectory(
                self, "원본 폴더 선택 (초기 설정)"
            )
            if not src_folder:
                src_folder = DEFAULT_SRC

            # 대상 폴더 선택
            dst_folder = QFileDialog.getExistingDirectory(
                self, "대상 폴더 선택 (초기 설정)"
            )
            if not dst_folder:
                dst_folder = DEFAULT_DST

            # 템플릿 선택
            file_path, _ = QFileDialog.getOpenFileName(
                self, "템플릿 선택", "", "PDF Files (*.pdf)"
            )

            # JSON 생성
            config = {
                "source_dir": src_folder,
                "target_dir": dst_folder,
                "template_dir": file_path,
                "file_names": "",
            }
            save_config(config)
            self.config = config

            # 입력창 반영
            self.files_input.setText("")

            self.log("🟢 초기 설정 완료: prevConfig.json 생성됨")
        else:
            self.config = load_previous_config()
            # self.pdf_input.setText(self.config.get("template_dir", ""))
            # self.src_input.setText(self.config.get("source_dir", DEFAULT_SRC))
            # self.dst_input.setText(self.config.get("target_dir", DEFAULT_DST))
            self.files_input.setText(self.config.get("file_names", ""))

    # --- 폴더 열기 ---
    def open_folder(self):
        self.config = load_previous_config()
        target = self.config.get("target_dir", DEFAULT_DST)
        target_path = os.path.abspath(target)
        subprocess.Popen(f'explorer "{target_path}"')

    # --- 현재 세팅 저장 ---
    def save_local_config(self):
        self.config = load_previous_config()
        source = self.config.get("source_dir", DEFAULT_SRC)
        target = self.config.get("target_dir", DEFAULT_DST)
        pdf = self.config.get("template_dir", "")
        target_path = os.path.abspath(target)

        save_config(
            {
                "source_dir": source,
                "target_dir": target_path,
                "template_dir": pdf,
                "file_names": self.files_input.text(),
            }
        )

    # --- 전역 예외 처리 ---
    def excepthook(exc_type, exc_value, exc_tb):
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            append_log(sys.app_window.log_output, "❌ 예외 발생:\n" + tb_str)
        except Exception:
            append_log("❌ 예외 발생:\n" + tb_str)

        # 원래 excepthook 호출
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    # --- 원본 폴더 다중 파일 선택 ---
    def select_src_files(self):
        self.config = load_previous_config()
        folder = self.config.get("source_dir", DEFAULT_SRC)
        print(folder)
        if not folder or not os.path.exists(folder):
            self.log("⚠️ 원본 폴더가 존재하지 않습니다")
            return

        # 다중 파일 선택
        files, _ = QFileDialog.getOpenFileNames(self, "원본 파일 선택", folder)
        if files:
            # 파일명만 추출 (확장자 포함 가능)
            names = [os.path.splitext(os.path.basename(f))[0] for f in files]
            self.files_input.setText(", ".join(names))
            self.log(f"🟢 {len(names)}개 파일 선택됨")

    def show_dst_files(self):
        self.config = load_previous_config()
        folder = self.config.get("target_dir", DEFAULT_DST)
        if not folder or not os.path.exists(folder):
            self.log("⚠️ 대상 폴더가 존재하지 않습니다")
            return

        files = os.listdir(folder)
        if not files:
            self.log("⚠️ 대상 폴더가 비어있습니다")
            return

        # 다이얼로그 생성
        dialog = QDialog(self)
        dialog.setWindowTitle("대상 폴더 파일 목록")
        dialog.resize(400, 300)

        layout = QVBoxLayout(dialog)

        # 리스트 위젯
        list_widget = QListWidget()
        for f in files:
            name, ext = os.path.splitext(f)
            list_widget.addItem(f"{f}")
        layout.addWidget(list_widget)

        # 총 파일 개수 라벨
        count_label = QLabel(f"총 파일 개수: {len(files)}")
        layout.addWidget(count_label)

        # 버튼 레이아웃
        btn_layout = QHBoxLayout()

        # 탐색기 열기 버튼
        open_btn = QPushButton("해당 경로 열기")

        def open_explorer():
            if os.name == "nt":
                subprocess.Popen(f'explorer "{os.path.abspath(folder)}"')
            else:
                self.log("❌ Windows에서만 지원되는 기능입니다")

        open_btn.clicked.connect(open_explorer)
        btn_layout.addWidget(open_btn)

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

        dialog.exec()

    def show_version_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("버전 정보")
        dialog.resize(300, 150)

        layout = QVBoxLayout(dialog)

        # 버전 및 날짜 표시
        version = "v1.0.0"
        date_str = "2025-08-17"
        layout.addWidget(QLabel(f"안뇽~~"))
        layout.addWidget(QLabel(f"프로그램 버전: {version}"))
        layout.addWidget(QLabel(f"빌드 날짜: {date_str}"))

        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def save_images_to_pdf_with_template(self):
        self.config = load_previous_config()
        source_dir = self.config.get(
            "source_dir", ""
        )  # 또는 self.files_input_dir.text()
        input_files = [
            f.strip() for f in self.files_input.text().split(",") if f.strip()
        ]

        # 허용할 이미지 확장자
        allowed_exts = (".jpg", ".jpeg", ".png", ".bmp", ".gif")

        files = []
        for f in input_files:
            found = False
            # 파일 이름에 확장자가 이미 있으면 그대로 체크
            if os.path.splitext(f)[1].lower() in allowed_exts:
                full_path = os.path.join(source_dir, f)
                if os.path.isfile(full_path):
                    files.append(full_path)
                    found = True
            else:
                # 확장자가 없으면 allowed_exts 순서대로 붙여서 체크
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
        # 저장 경로
        folder = self.config.get("target_dir", DEFAULT_DST)
        if not os.path.exists(folder):
            os.makedirs(folder)

        pdf_path = os.path.join(folder, "이미지_모음.pdf")
        counter = 1
        while os.path.exists(pdf_path):
            pdf_path = os.path.join(folder, f"이미지_모음_{counter}.pdf")
            counter += 1

        self.log(f"🟢 PDF 생성 시작: {pdf_path}")

        # 템플릿 첫 페이지 가져오기
        template_path = self.config.get("template_dir", "")
        if not template_path or not os.path.isfile(template_path):
            self.log("❌ 템플릿 경로가 없습니다.")
            return
        template_reader = PdfReader(template_path)
        template_page = template_reader.pages[0]

        writer = PdfWriter()

        # A4 기준
        page_w, page_h = A4
        cfg = self.config
        h_margin = cfg.get("h_margin", 20)
        v_margin = cfg.get("v_margin", 30)
        target_w = cfg.get("target_w", 300)
        target_h = cfg.get("target_h", 160)
        img_h = (page_h - (2 + 1) * v_margin) / 2  # 2행 기준

        for i, img_file in enumerate(files):
            idx_in_page = i % 2  # 한 페이지 2장

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

        self.save_local_config
        self.log(f"✅ PDF 저장 완료: {pdf_path}")

        # PDF 열기
        if sys.platform == "win32":
            os.startfile(pdf_path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", pdf_path])
        elif sys.platform == "linux":
            subprocess.Popen(["xdg-open", pdf_path])


# --- 실행 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageCopyApp()
    sys.app_window = window  # 전역에서 예외 처리용
    window.show()
    sys.exit(app.exec())
