# dialogs.py
from PySide6.QtWidgets import (
    QDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
)
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from config import DEFAULT_DST, DEFAULT_SRC, load_previous_config, save_config
import os


class PathDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("경로 설정")
        self.resize(500, 200)

        layout = QVBoxLayout()

        # --- PDF 템플릿 ---
        h0 = QHBoxLayout()
        self.label_pdf = QLabel("템플릿경로(PDF):")
        h0.addWidget(self.label_pdf)
        self.pdf_input = QLineEdit()
        h0.addWidget(self.pdf_input)
        self.pdf_btn = QPushButton("선택")
        self.pdf_btn.clicked.connect(self.choose_pdf_file)
        h0.addWidget(self.pdf_btn)
        self.pdf_open_btn = QPushButton("폴더 열기")
        self.pdf_open_btn.clicked.connect(lambda: self.open_path(self.pdf_input.text()))
        h0.addWidget(self.pdf_open_btn)
        layout.addLayout(h0)

        # --- 원본 폴더 ---
        h1 = QHBoxLayout()
        self.src_dir = QLabel("원본 폴더:")
        h1.addWidget(self.src_dir)
        self.src_input = QLineEdit()
        h1.addWidget(self.src_input)
        self.src_btn = QPushButton("선택")
        self.src_btn.clicked.connect(self.choose_src_folder)
        h1.addWidget(self.src_btn)
        self.src_open_btn = QPushButton("폴더 열기")
        self.src_open_btn.clicked.connect(lambda: self.open_path(self.src_input.text()))
        h1.addWidget(self.src_open_btn)
        layout.addLayout(h1)

        # --- 대상 폴더 ---
        h2 = QHBoxLayout()
        self.dsr_dir = QLabel("대상 폴더:")
        h2.addWidget(self.dsr_dir)
        self.dst_input = QLineEdit()
        h2.addWidget(self.dst_input)
        self.dst_btn = QPushButton("선택")
        self.dst_btn.clicked.connect(self.choose_dst_folder)
        h2.addWidget(self.dst_btn)
        self.dst_open_btn = QPushButton("폴더 열기")
        self.dst_open_btn.clicked.connect(lambda: self.open_path(self.dst_input.text()))
        h2.addWidget(self.dst_open_btn)
        layout.addLayout(h2)

        # --- 확인 / 취소 버튼 ---
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("확인")
        ok_btn.clicked.connect(self.confirm_config)
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.set_default_config()

    # --- 폴더/파일 선택 ---
    def choose_pdf_file(self):
        initial_path = self.pdf_input.text()
        file_path, _ = QFileDialog.getOpenFileName(self, "PDF 선택", initial_path, "PDF Files (*.pdf)")
        if file_path:
            self.pdf_input.setText(file_path)

    def choose_src_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "원본 폴더 선택", self.src_input.text())
        if folder:
            self.src_input.setText(folder)

    def choose_dst_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "대상 폴더 선택", self.dst_input.text())
        if folder:
            self.dst_input.setText(folder)

    # --- OS 탐색기에서 폴더 열기 ---
    def open_path(self, path: str):
        if path and os.path.exists(path):
            folder_path = path if os.path.isdir(path) else os.path.dirname(path)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
        else:
            QMessageBox.warning(self, "경고", "유효한 경로가 아닙니다.")

    # --- 설정 로드 / 저장 ---
    def set_default_config(self):
        self.config = load_previous_config()
        self.pdf_input.setText(self.config.get("template_dir", ""))
        self.src_input.setText(self.config.get("source_dir", DEFAULT_SRC))
        self.dst_input.setText(self.config.get("target_dir", DEFAULT_DST))

    def confirm_config(self):
        save_config(
            {
                "source_dir": self.src_input.text(),
                "target_dir": self.dst_input.text(),
                "template_dir": self.pdf_input.text(),
            }
        )
        self.accept()
