import sys
import json
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QWidget
)

# pdf템플릿 이미지 위치 지정하는 dialog
class ImageLayoutDialog(QDialog):
    def __init__(self, image_count=3):
        super().__init__()
        self.setWindowTitle("이미지 PDF 레이아웃 설정")
        self.resize(400, 400)

        self.image_count = image_count
        self.inputs = {}

        layout = QVBoxLayout()

        # 기본 설정
        self.inputs['ImageInPage'] = QLineEdit("2")
        self.inputs['h_margin'] = QLineEdit("20")
        self.inputs['v_margin'] = QLineEdit("10")

        layout.addLayout(self._row("이미지 개수", self.inputs['ImageInPage']))
        layout.addLayout(self._row("왼쪽 여백 전체", self.inputs['h_margin']))
        layout.addLayout(self._row("위/아래 여백", self.inputs['v_margin']))

        # ScrollArea로 동적 x_offset, y_offset 입력창
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        self.offset_inputs = []

        for i in range(self.image_count):
            x_input = QLineEdit("0")
            y_input = QLineEdit("0")
            self.offset_inputs.append((x_input, y_input))
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(f"{i+1}번째 이미지 X offset(가로)"))
            row_layout.addWidget(x_input)
            row_layout.addWidget(QLabel("Y offset(세로)"))
            row_layout.addWidget(y_input)
            scroll_layout.addLayout(row_layout)

        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 저장 버튼
        btn_save = QPushButton("저장")
        btn_save.clicked.connect(self.save_config)
        layout.addWidget(btn_save)

        self.setLayout(layout)

    def _row(self, label, widget):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        layout.addWidget(widget)
        return layout

    def save_config(self):
        config = {
            "ImageInPage": int(self.inputs['ImageInPage'].text()),
            "h_margin": float(self.inputs['h_margin'].text()),
            "v_margin": float(self.inputs['v_margin'].text()),
            "offsets": []
        }
        for x_input, y_input in self.offset_inputs:
            config['offsets'].append({
                "x_offset": float(x_input.text()),
                "y_offset": float(y_input.text())
            })

        # JSON 저장 예시
        with open("image_layout_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        print("✅ 저장 완료:", config)
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = ImageLayoutDialog(image_count=5)  # 이미지 5장 기준
    dlg.exec()
