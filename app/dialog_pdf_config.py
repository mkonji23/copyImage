import os
import traceback
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QFormLayout,QLabel, QFrame
from log_utils import append_log
from preview_dialog import PreviewDialog
from config import load_previous_config, save_config

class DialogPdfConfig(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDF 이미지 설정")
        self.resize(300, 200)

        # ✅ 이전 저장값 불러오기
        self.prev_config = load_previous_config() or {}

        layout = QVBoxLayout()
        form = QFormLayout()
        preview_btn = QPushButton("미리보기")
        preview_btn.clicked.connect(self.show_preview)
        layout.addWidget(preview_btn)
        # 🔹 불러온 값 or 기본값 세팅
        self.h_margin_input = QLineEdit(str(self.prev_config.get("h_margin", 20)))
        self.v_margin_input = QLineEdit(str(self.prev_config.get("v_margin", 30)))
        self.target_w_input = QLineEdit(str(self.prev_config.get("target_w", 300)))
        self.target_h_input = QLineEdit(str(self.prev_config.get("target_h", 160)))
        # 첫번째 두번째 이미지
        self.target_x_offset1 = QLineEdit(str(self.prev_config.get("x_offset1", 0)))
        self.target_y_offset1 = QLineEdit(str(self.prev_config.get("y_offset1", -50)))
        self.target_x_offset2 = QLineEdit(str(self.prev_config.get("x_offset2", 0)))
        self.target_y_offset2 = QLineEdit(str(self.prev_config.get("y_offset2", 10)))
           # --- 또는 구분선 ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)  # 수평선
        line.setFrameShadow(QFrame.Sunken)

        # --- 또는 구분선 ---
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)  # 수평선
        line2.setFrameShadow(QFrame.Sunken)

        form.addRow("이미지 가로 (target_w):", self.target_w_input)
        form.addRow("이미지 세로 (target_h):", self.target_h_input)
        form.addRow(line)  # 폼 레이아웃에 추가
        # --- 구분 제목 ---
        form.addRow(QLabel("크면 왼쪽여백 증가, 크면 위쪽 여백 증가"))  # 제목처럼 보이게
        form.addRow("좌우 여백 (h_margin):", self.h_margin_input)
        form.addRow("상하 여백 (v_margin):", self.v_margin_input)

        # --- 구분 제목 ---
        form.addRow(line2)  # 폼 레이아웃에 추가
        form.addRow(QLabel("x값은 증가 오른쪽, y값은 증가 위로"))  # 제목처럼 보이게
        form.addRow("이미지1 좌우(x-offset):", self.target_x_offset1)
        form.addRow("이미지1 상하(y-offset):", self.target_y_offset1)
        form.addRow("이미지2 좌우(x-offset):", self.target_x_offset2)
        form.addRow("이미지2 상하(y-offset):", self.target_y_offset2)


        layout.addLayout(form)

        # 저장 버튼
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_config)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def save_config(self):
        new_config = {
            **self.prev_config,  # 기존 값 유지
            "h_margin": int(self.h_margin_input.text()),
            "v_margin": int(self.v_margin_input.text()),
            "target_w": int(self.target_w_input.text()),
            "target_h": int(self.target_h_input.text()),
            "x_offset1": int(self.target_x_offset1.text()),
            "y_offset1": int(self.target_y_offset1.text()),
            "x_offset2": int(self.target_x_offset2.text()),
            "y_offset2": int(self.target_y_offset2.text()),
        }
        save_config(new_config)  # ✅ 파일에 저장
        self.accept()
        
    def show_preview(self):
        try:
            cfg = {
                "h_margin": int(self.h_margin_input.text()),
                "v_margin": int(self.v_margin_input.text()),
                "target_w": int(self.target_w_input.text()),
                "target_h": int(self.target_h_input.text()),
                "x_offset1": int(self.target_x_offset1.text()),
                "y_offset1": int(self.target_y_offset1.text()),
                "x_offset2": int(self.target_x_offset2.text()),
                "y_offset2": int(self.target_y_offset2.text()),
            }

            folder = self.prev_config.get("target_dir", "")
            template_path = self.prev_config.get("template_dir", "")
            if not folder:
                raise ValueError("📂 대상 폴더(target_dir)가 설정되지 않았습니다.")
            if not template_path:
                raise ValueError("📑 템플릿 파일(template_dir)이 지정되지 않았습니다.")

            sample_images = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith((".jpg", ".png"))
            ]
            if not sample_images:
                raise FileNotFoundError("❌ 대상 폴더에 JPG/PNG 이미지가 없습니다.")

            dlg = PreviewDialog(cfg, sample_images, template_path, self)
            dlg.exec()

        except Exception as e:
            error_msg = f"⚠️ 미리보기 생성 실패: {e}\n{traceback.format_exc()}"
            append_log(self.parent().log_output, error_msg)
