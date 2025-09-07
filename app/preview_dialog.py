from PySide6.QtWidgets import QLabel, QDialog, QVBoxLayout, QPushButton
from PySide6.QtGui import QPixmap
from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt
from pdf2image import convert_from_path

class PreviewDialog(QDialog):
    def __init__(self, cfg, sample_images, template_path=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDF 배치 미리보기")
        self.resize(600, 800)

        layout = QVBoxLayout(self)
        self.label = QLabel()
        layout.addWidget(self.label)

        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        # 🔹 A4 해상도 (픽셀 단위, 72dpi 기준)
        page_w, page_h = (595, 842)

        # 🔹 PDF → 이미지 변환 (첫 페이지만 사용)
        if template_path and template_path.lower().endswith(".pdf"):
            try:
                pages = convert_from_path(template_path, dpi=72)
                base = pages[0].convert("RGB")
                base = base.resize((page_w, page_h))  # A4 크기에 맞춤
            except Exception as e:
                print(f"⚠️ 템플릿 불러오기 실패: {e}")
                base = Image.new("RGB", (page_w, page_h), "white")
        else:
            base = Image.new("RGB", (page_w, page_h), "white")

        preview = base.copy()
        draw = ImageDraw.Draw(preview)

        target_w = cfg.get("target_w", 300)
        target_h = cfg.get("target_h", 160)
        h_margin = cfg.get("h_margin", 20)
        v_margin = cfg.get("v_margin", 30)

        for i, img_path in enumerate(sample_images[:2]):  # 샘플 2장만
            img = Image.open(img_path)
            img.thumbnail((target_w, target_h))

            if i == 0:
                x = h_margin + cfg.get("x_offset1", 0)
                y = v_margin + cfg.get("y_offset1", -50)
            else:
                x = h_margin + cfg.get("x_offset2", 0)
                y = page_h // 2 + v_margin + cfg.get("y_offset2", 10)

            preview.paste(img, (x, y))

        # QLabel에 표시
        qim = ImageQt(preview)
        pix = QPixmap.fromImage(qim)
        self.label.setPixmap(pix)
