import sys
import json
from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QWidget
)
from PySide6.QtCore import Qt

class ImageLayoutDialog(QDialog):
    def __init__(self, default_count=2):
        super().__init__()
        self.setWindowTitle("이미지 PDF 레이아웃 설정")
        self.resize(400, 400)

        self.inputs = {}
        self.offset_inputs = []

        layout = QVBoxLayout()

        # ImageInPage 입력
        self.inputs['ImageInPage'] = QLineEdit(str(default_count))
        self.inputs['h_margin'] = QLineEdit("20")
        self.inputs['v_margin'] = QLineEdit("10")

        layout.addLayout(self._row("이미지 개수(ImageInPage)", self.inputs['ImageInPage']))
        layout.addLayout(self._row("왼쪽 여백 전체(h_margin)", self.inputs['h_margin']))
        layout.addLayout(self._row("위/아래 여백 전체(v_margin)", self.inputs['v_margin']))

        # ImageInPage 값이 바뀌면 offset 입력창 업데이트
        self.inputs['ImageInPage'].textChanged.connect(self.update_offset_inputs)

        # ScrollArea로 동적 offset 입력창
        self.scroll = QScrollArea()
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll)
        # 초기 offset 입력창 생성
        self.update_offset_inputs()

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

    def update_offset_inputs(self):
        try:
            count = int(self.inputs['ImageInPage'].text())
            if count < 1:
                count = 1
        except ValueError:
            count = 1

        # 기존 위젯 제거
        for i in reversed(range(self.scroll_layout.count())):
            item = self.scroll_layout.itemAt(i)
            if item:
                w = item.layout()
                if w:
                    while w.count():
                        child = w.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                    self.scroll_layout.removeItem(w)

        self.offset_inputs = []

        # 새 입력창 생성
        for i in range(count):
            x_input = QLineEdit("0")
            y_input = QLineEdit("0")
            self.offset_inputs.append((x_input, y_input))
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(f"{i+1}번째 이미지 X offset"))
            row_layout.addWidget(x_input)
            row_layout.addWidget(QLabel("Y offset"))
            row_layout.addWidget(y_input)
            self.scroll_layout.addLayout(row_layout)

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

        with open("image_layout_config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        print("✅ 저장 완료:", config)
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = ImageLayoutDialog(default_count=2)  # 기본값 3개
    dlg.exec()
