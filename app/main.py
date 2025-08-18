import os
import subprocess
import sys
import traceback
from datetime import datetime

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

        # 아이콘 기본값 처리
        icon_path = "resources/icon.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 중앙 위젯
        central = QWidget()
        self.setCentralWidget(central)

        self.src_input = QLineEdit()
        self.src_btn = QPushButton("원본 폴더 경로")
        self.dst_input = QLineEdit()
        self.dst_btn = QPushButton("대상 폴더 경로")
        self.files_input = QLineEdit()
        self.run_btn = QPushButton("복사 실행(Enter)")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("원본 폴더:"))
        h1 = QHBoxLayout()
        h1.addWidget(self.src_input)
        h1.addWidget(self.src_btn)
        self.src_list_btn = QPushButton("이미지 선택")
        self.src_list_btn.clicked.connect(self.select_src_files)
        h1.addWidget(self.src_list_btn)
        layout.addLayout(h1)

        h2 = QHBoxLayout()
        h2.addWidget(self.dst_input)
        h2.addWidget(self.dst_btn)
        self.dst_list_btn = QPushButton("파일보기")
        self.dst_list_btn.clicked.connect(self.show_dst_files)
        h2.addWidget(self.dst_list_btn)
        layout.addLayout(h2)

        # --- 파일명 입력 라인 ---
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("파일명 입력(콤마(,) 구분):"))
        layout.addLayout(h3)

        # input, 초기화 버튼
        h4 = QHBoxLayout()
        
        # input
        self.files_input = QLineEdit()
        h4.addWidget(self.files_input)
         # Enter 키 입력 시 run_copy 실행
        self.files_input.returnPressed.connect(self.run_copy)

        # 초기화 버튼
        clear_btn = QPushButton("초기화")
        clear_btn.clicked.connect(self.clear_input)
        h4.addWidget(clear_btn)

        layout.addLayout(h4)

        # h5 로그
        h5 = QHBoxLayout()
        h5.addWidget(self.run_btn)
        layout.addLayout(h5)
        layout.addWidget(QLabel("로그:"))
        layout.addWidget(self.log_output)
        central.setLayout(layout)

        # 메뉴
        menu_bar = self.menuBar()

        # 파일 메뉴
        file_menu = menu_bar.addMenu("파일")
        default_action = QAction("기본 경로 불러오기", self)
        close_action = QAction("닫기", self)

        file_menu.addAction(default_action)
        file_menu.addAction(close_action)

        # 설정 메뉴
        config_menu = menu_bar.addMenu("설정")
        self.explorer_action = QAction("복사 후 폴더 띄우기", self)
        self.explorer_action.setCheckable(True)  # 체크박스처럼 만들기
        self.explorer_action.setChecked(True)    # 기본 체크 여부

        # 체크 상태 변경 시 로그 찍기
        self.explorer_action.toggled.connect(self.on_explorer_toggled)
        
        config_menu.addAction(self.explorer_action)

        # 오른쪽 끝에 띄우기 위해 스페이서 위젯
        info_menu = menu_bar.addMenu("정보")
        info_action = QAction("버전확인", self)
        info_menu.addAction(info_action)

        # 시그널 연결
        self.src_btn.clicked.connect(self.choose_src_folder)
        self.dst_btn.clicked.connect(self.choose_dst_folder)
        self.run_btn.clicked.connect(self.run_copy)
        default_action.triggered.connect(self.load_default_config)
        close_action.triggered.connect(self.close)

        info_action.triggered.connect(self.show_version_dialog)

        # 프로그램 시작 로그
        append_log(self.log_output, "🟢 프로그램 시작")

        # prevConfig.json 없으면 초기 설정
        self.initialize_config()

    # 콜백 함수
    def on_explorer_toggled(self, checked: bool):
        if checked:
            self.log("✅ 폴더 띄우기 옵션 체크됨")
        else:
            self.log("❌ 폴더 띄우기 옵션 체크 해제됨")

    # 키 이벤트 재정의
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.run_copy()

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

    # --- 기본 경로 불러오기 ---
    def load_default_config(self):
        config = load_previous_config()
        if config:
            self.src_input.setText(config.get("source_dir", DEFAULT_SRC))
            self.dst_input.setText(config.get("target_dir", DEFAULT_DST))
            self.files_input.setText(config.get("file_names", ""))
            self.log("🟢 prevConfig.json 내용을 불러왔습니다")
        else:
            self.log("⚠️ prevConfig.json이 없습니다")

    # --- 초기 설정 (첫 실행) ---

    def initialize_config(self):
        if not os.path.exists("prevConfig.json"):
            # 알림창
            QMessageBox.information(
                self,
                "초기 설정 필요",
                "prevConfig.json이 없습니다.\n초기 설정을 진행합니다.\n원본 폴더와 대상 폴더를 선택해주세요.",
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

            # JSON 생성
            config = {
                "source_dir": src_folder,
                "target_dir": dst_folder,
                "file_names": "",
            }
            save_config(config)
            self.config = config

            # 입력창 반영
            self.src_input.setText(src_folder)
            self.dst_input.setText(dst_folder)
            self.files_input.setText("")

            self.log("🟢 초기 설정 완료: prevConfig.json 생성됨")
        else:
            self.config = load_previous_config()
            self.src_input.setText(self.config.get("source_dir", DEFAULT_SRC))
            self.dst_input.setText(self.config.get("target_dir", DEFAULT_DST))
            self.files_input.setText(self.config.get("file_names", ""))

    # --- 복사 실행 ---
    def run_copy(self):
        source = self.src_input.text()
        target = self.dst_input.text()
        file_names = [
            s.strip() for s in self.files_input.text().split(",") if s.strip()
        ]
        if not source or not target or not file_names:
            self.log("❌ 파일명을 입력해주세요.")
            return
        copy_images(file_names, source, target, self.log)
        target_path = os.path.abspath(target)
        save_config(
            {
                "source_dir": source,
                "target_dir": target_path,
                "file_names": self.files_input.text(),
            }
        )
        if self.explorer_action.isChecked() and sys.platform == "win32":
            subprocess.Popen(f'explorer "{target_path}"')
        self.log("✅ 작업 완료!")

    # --- 전역 예외 처리 ---
    def excepthook(exc_type, exc_value, exc_tb):
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            append_log(sys.app_window.log_output, "❌ 예외 발생:\n" + tb_str)
        except:
            print("❌ 예외 발생:\n" + tb_str)
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = excepthook

    # --- 원본 폴더 다중 파일 선택 ---
    def select_src_files(self):
        folder = self.src_input.text()
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
        folder = self.dst_input.text()
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


# --- 실행 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageCopyApp()
    sys.app_window = window  # 전역에서 예외 처리용
    window.show()
    sys.exit(app.exec())
