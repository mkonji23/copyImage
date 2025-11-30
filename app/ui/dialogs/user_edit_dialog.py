from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QMessageBox


class DialogUserEdit(QDialog):
    def __init__(self, parent=None, user_data=None):
        super().__init__(parent)
        self.setWindowTitle("사용자 정보 입력")
        self.resize(300, 200)

        self.user_data = user_data or {}

        layout = QVBoxLayout()

        form = QFormLayout()
        self.name_input = QLineEdit()
        self.title_input = QLineEdit()
        self.id_input = QLineEdit()
        form.addRow("이름:", self.name_input)
        form.addRow("오답노트 제목:", self.title_input)
        form.addRow("오답노트 번호:", self.id_input)
        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("저장")
        self.cancel_btn = QPushButton("취소")
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        # 값 세팅
        if self.user_data:
            self.name_input.setText(self.user_data.get("name", ""))
            self.title_input.setText(self.user_data.get("note_title", ""))
            self.id_input.setText(self.user_data.get("note_id", ""))

        # 이벤트
        self.save_btn.clicked.connect(self.on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def on_save(self):
        name = self.name_input.text().strip()
        title = self.title_input.text().strip()
        note_id = self.id_input.text().strip()

        if not name:
            QMessageBox.warning(self, "오류", "이름은 필수입니다.")
            return

        self.user_data = {"name": name, "note_title": title, "note_id": note_id}
        self.accept()

    def get_data(self):
        return self.user_data
