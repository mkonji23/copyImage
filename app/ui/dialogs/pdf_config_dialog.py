from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QLabel,
    QFrame,
    QSlider,
    QHBoxLayout,
    QSpinBox,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsRectItem,
    QWidget,
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QColor, QBrush, QPainter
from config import load_previous_config, save_config


# pdf 설정
class DialogPdfConfig(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PDF 이미지 설정")
        self.resize(700, 500)  # 크기 키움 (미리보기 공간 확보)

        # ✅ 이전 저장값 불러오기
        self.prev_config = load_previous_config() or {}

        # 전체 레이아웃을 수평으로 분할
        self.main_layout = QHBoxLayout()

        # 왼쪽 설정 부분
        self.left_layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        # 🔹 불러온 값 or 기본값 세팅
        self.target_w_input = self.create_slider_spinbox_group(
            "이미지 가로 (target_w):", self.prev_config.get("target_w", 300), 100, 800
        )
        self.target_h_input = self.create_slider_spinbox_group(
            "이미지 세로 (target_h):", self.prev_config.get("target_h", 160), 50, 600
        )

        # --- 구분선 ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.form_layout.addRow(line)

        # --- 구분 제목 ---
        self.form_layout.addRow(QLabel("좌우/상하 여백 설정"))

        # 여백 설정 슬라이더 + 스핀박스
        self.h_margin_input = self.create_slider_spinbox_group(
            "좌우 여백 (h_margin):", self.prev_config.get("h_margin", 20), -200, 200
        )
        self.v_margin_input = self.create_slider_spinbox_group(
            "상하 여백 (v_margin):", self.prev_config.get("v_margin", 20), -200, 200
        )

        # --- 구분선 ---
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        self.form_layout.addRow(line2)

        # --- 구분 제목 ---
        self.form_layout.addRow(QLabel("이미지 위치 미세 조정 (x: 오른쪽+, y: 위로+)"))

        # 오프셋 설정 슬라이더 + 스핀박스
        self.target_x_offset1 = self.create_slider_spinbox_group(
            "이미지1 좌우(x-offset):", self.prev_config.get("x_offset1", 0), -200, 200
        )
        self.target_y_offset1 = self.create_slider_spinbox_group(
            "이미지1 상하(y-offset):", self.prev_config.get("y_offset1", -50), -200, 200
        )
        self.target_x_offset2 = self.create_slider_spinbox_group(
            "이미지2 좌우(x-offset):", self.prev_config.get("x_offset2", 0), -200, 200
        )
        self.target_y_offset2 = self.create_slider_spinbox_group(
            "이미지2 상하(y-offset):", self.prev_config.get("y_offset2", 10), -200, 200
        )

        self.left_layout.addLayout(self.form_layout)

        # 저장 버튼
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self._save_config)
        self.left_layout.addWidget(save_btn)

        # 왼쪽 레이아웃을 메인 레이아웃에 추가
        self.main_layout.addLayout(self.left_layout, 1)  # 비율 1

        # 오른쪽 미리보기 부분
        self.preview_layout = QVBoxLayout()
        self.preview_label = QLabel("미리보기 (대략적인 위치)")
        self.preview_layout.addWidget(self.preview_label)

        # 그래픽스 뷰 생성
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.preview_layout.addWidget(self.view)

        # 메인 레이아웃에 미리보기 추가
        self.main_layout.addLayout(self.preview_layout, 1)  # 비율 1

        self.setLayout(self.main_layout)

        # 모든 위젯 초기화 후 미리보기 업데이트
        self.update_preview()

        # 모든 슬라이더 값 변경 시 미리보기 업데이트 연결
        self.target_w_input.valueChanged.connect(self.update_preview)
        self.target_h_input.valueChanged.connect(self.update_preview)
        self.h_margin_input.valueChanged.connect(self.update_preview)
        self.v_margin_input.valueChanged.connect(self.update_preview)
        self.target_x_offset1.valueChanged.connect(self.update_preview)
        self.target_y_offset1.valueChanged.connect(self.update_preview)
        self.target_x_offset2.valueChanged.connect(self.update_preview)
        self.target_y_offset2.valueChanged.connect(self.update_preview)

    def create_slider_spinbox_group(self, label, default_value, min_val, max_val):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(default_value)
        spinbox.setFixedWidth(70)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_value)

        # 슬라이더 <-> 스핀박스 동기화
        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)

        layout.addWidget(QLabel(label))
        layout.addWidget(slider)
        layout.addWidget(spinbox)

        # 폼 레이아웃에 한 줄 추가
        self.form_layout.addRow(container)

        return spinbox  # ✅ 스핀박스를 리턴 (값 저장/로드용)

    def update_preview(self):
        self.scene.clear()
        page_w, page_h = 595, 842  # A4 pt
        self.scene.setSceneRect(0, 0, page_w, page_h)

        # 페이지 테두리
        border_pen = QPen(QColor(150, 150, 150))
        border_pen.setStyle(Qt.DashLine)
        self.scene.addRect(0, 0, page_w, page_h, border_pen)

        cfg = {
            "target_w": self.target_w_input.value(),
            "target_h": self.target_h_input.value(),
            "h_margin": self.h_margin_input.value(),
            "v_margin": self.v_margin_input.value(),
            "x_offset1": self.target_x_offset1.value(),
            "y_offset1": self.target_y_offset1.value(),
            "x_offset2": self.target_x_offset2.value(),
            "y_offset2": self.target_y_offset2.value(),
        }

        target_w = cfg["target_w"]
        target_h = cfg["target_h"]
        h_margin = cfg["h_margin"]
        v_margin = cfg["v_margin"]
        x_offset1 = cfg["x_offset1"]
        y_offset1 = cfg["y_offset1"]
        x_offset2 = cfg["x_offset2"]
        y_offset2 = cfg["y_offset2"]

        img_h = (page_h - (2 + 1) * v_margin) / 2

        # PDF 기준 y 계산
        pdf_positions = [
            {
                "x": h_margin + x_offset1,
                "y": page_h - v_margin - (0 + 1) * img_h - 0 * v_margin + y_offset1,
            },
            {
                "x": h_margin + x_offset2,
                "y": page_h - v_margin - (1 + 1) * img_h - 1 * v_margin + y_offset2,
            },
        ]

        pen = QPen(Qt.black)
        brush = QBrush(QColor(100, 150, 255, 100))

        for pos in pdf_positions:
            qt_x = pos["x"]
            qt_y = page_h - pos["y"] - target_h  # PDF → Qt 좌표 변환
            self.scene.addRect(qt_x, qt_y, target_w, target_h, pen, brush)

        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def _save_config(self):
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
