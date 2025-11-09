import os
import sys
from functools import partial

import openpyxl
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLineEdit,
)

from config import (
    DEFAULT_DST,
    DEFAULT_SRC,
    load_previous_config,
    save_config,
)
from dialog_pdf_config import DialogPdfConfig
from dialogs import PathDialog
from log_utils import append_log
from pdf_generator import save_images_to_pdf_for_dialog_users


class WrongAnswerManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("copycopyWA")
        self.resize(800, 600)

        # 아이콘 설정
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        icon_path = os.path.join(base_path, "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 설정 로드
        self.config = load_previous_config() or {"users": []}
        self.users = self.config.get("users", [])
        self.modified_rows = set()
        self.modified = False

        # --- 메뉴 ---
        self.setup_menus()

        # --- 중앙 위젯 ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- 버튼 ---
        # 첫 번째 줄 버튼
        btn_layout_1 = QHBoxLayout()
        self.add_btn = QPushButton("신규")
        self.del_btn = QPushButton("삭제")
        self.save_btn = QPushButton("저장")
        self.pdf_btn = QPushButton("PDF 저장")
        self.refresh_btn = QPushButton("새로고침")

        for btn in [self.add_btn, self.del_btn, self.save_btn, self.pdf_btn, self.refresh_btn]:
            btn_layout_1.addWidget(btn)
        main_layout.addLayout(btn_layout_1)

        # 구분선
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)

        # 두 번째 줄 버튼
        btn_layout_2 = QHBoxLayout()
        btn_layout_2.addWidget(QLabel("데이터 관리:"))
        self.excel_export_btn = QPushButton("엑셀 Export")
        self.excel_import_btn = QPushButton("엑셀 Import")
        btn_layout_2.addWidget(self.excel_export_btn)
        btn_layout_2.addWidget(self.excel_import_btn)
        btn_layout_2.addStretch()  # 버튼들을 왼쪽으로 정렬
        main_layout.addLayout(btn_layout_2)

        # --- 테이블 ---
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["", "이름", "오답노트 제목", "오답노트 번호"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().resizeSection(0, 40)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        main_layout.addWidget(self.table)

        # --- 로그 ---
        main_layout.addWidget(QLabel("로그:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        # --- 이벤트 연결 ---
        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.delete_selected)
        self.save_btn.clicked.connect(self.save_all)
        self.pdf_btn.clicked.connect(self.export_pdf)
        self.refresh_btn.clicked.connect(self.load_table)
        self.excel_export_btn.clicked.connect(self.export_excel)
        self.excel_import_btn.clicked.connect(self.import_excel)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.cellClicked.connect(self.on_cell_click_row)

        # --- 초기화 ---
        self.load_table()
        self.log("🟢 프로그램 시작")
        self.initialize_config()

    def setup_menus(self):
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("설정")

        path_config_action = QAction("경로 설정 열기", self)
        pdf_config_action = QAction("PDF 설정", self)
        close_action = QAction("닫기", self)

        settings_menu.addAction(path_config_action)
        settings_menu.addAction(pdf_config_action)
        settings_menu.addSeparator()
        settings_menu.addAction(close_action)

        path_config_action.triggered.connect(self.open_path_dialog)
        pdf_config_action.triggered.connect(self.open_config_dialog)
        close_action.triggered.connect(self.close)

        info_menu = menu_bar.addMenu("정보")
        info_action = QAction("버전확인", self)
        info_menu.addAction(info_action)
        info_action.triggered.connect(self.show_version_dialog)

    def log(self, message):
        append_log(self.log_output, message)

    # -------------------- 테이블 관리 --------------------
    def load_table(self, from_config=True):
        if from_config:
            # config에서 users를 다시 로드하여 최신 저장 상태를 반영
            self.config = load_previous_config()
            self.users = self.config.get("users", [])
            self.log("🔄 데이터를 새로고침했습니다.")

        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for user in self.users:
            self.add_table_row(user)
        self.table.blockSignals(False)
        
        # UI의 색상과 수정 상태를 초기화합니다.
        self.clear_modified_marks()

    def add_table_row(self, user=None):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 체크박스
        checkbox = QCheckBox()
        w = QWidget()
        l = QHBoxLayout(w)
        l.addWidget(checkbox)
        l.setAlignment(Qt.AlignCenter)
        l.setContentsMargins(0, 0, 0, 0)
        self.table.setCellWidget(row, 0, w)

        name = user.get("name", "") if user else ""
        title = user.get("note_title", "") if user else ""
        numbers = user.get("note_numbers", "") if user else ""

        self.table.setItem(row, 1, QTableWidgetItem(name))
        self.table.setItem(row, 2, QTableWidgetItem(title))
        
        # 오답노트 번호 위젯 (LineEdit + Button)
        note_widget = self.create_note_number_widget(numbers, row)
        self.table.setCellWidget(row, 3, note_widget)

    def create_note_number_widget(self, text, row):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 0, 2, 0)
        
        line_edit = QLineEdit(text)
        line_edit.textChanged.connect(lambda: self.on_cell_changed(row, 3))
        
        button = QPushButton()
        button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        button.setFixedSize(24, 24)
        button.clicked.connect(partial(self.select_note_images_for_row, row))
        
        layout.addWidget(line_edit)
        layout.addWidget(button)
        widget.setLayout(layout)
        return widget

    def select_note_images_for_row(self, row):
        self.config = load_previous_config()
        folder = self.config.get("source_dir", DEFAULT_SRC)
        if not os.path.exists(folder):
            self.log(f"⚠️ 원본 폴더가 존재하지 않습니다: {folder}")
            QMessageBox.warning(self, "경고", "설정에서 원본 폴더를 먼저 지정해주세요.")
            return

        files, _ = QFileDialog.getOpenFileNames(self, "이미지 파일 선택", folder, "Image Files (*.png *.jpg *.bmp)")
        if files:
            names = [os.path.splitext(os.path.basename(f))[0] for f in files]
            widget = self.table.cellWidget(row, 3)
            line_edit = widget.findChild(QLineEdit)
            line_edit.setText(", ".join(names))
            self.log(f"🟢 {len(names)}개 파일 선택됨 (행: {row + 1})")

    def on_cell_changed(self, row, col):
        self.modified = True
        self.modified_rows.add(row)
        self.mark_row_as_modified(row)

    def mark_row_as_modified(self, row):
        for col in range(1, 3): # 이름, 제목
            item = self.table.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 200))
        # 오답노트 번호 위젯 배경색
        widget = self.table.cellWidget(row, 3)
        if widget:
            widget.setStyleSheet("background-color: #FFFFC8;")


    def clear_modified_marks(self):
        for row in list(self.modified_rows):
            # 테이블 행이 유효한지 확인
            if row < self.table.rowCount():
                for col in range(1, 3):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QColor(255, 255, 255))
                widget = self.table.cellWidget(row, 3)
                if widget:
                    widget.setStyleSheet("")
        self.modified_rows.clear()
        self.modified = False

    def on_cell_click_row(self, row, col):
        if col != 0:
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(not checkbox.isChecked())

    # -------------------- 데이터 관리 --------------------
    def add_row(self):
        self.add_table_row()
        self.modified = True
        row = self.table.rowCount() - 1
        self.mark_row_as_modified(row)

    def delete_selected(self):
        rows_to_remove = [
            r for r in range(self.table.rowCount())
            if self.table.cellWidget(r, 0).findChild(QCheckBox).isChecked()
        ]
        if not rows_to_remove:
            QMessageBox.information(self, "안내", "삭제할 행을 선택하세요.")
            return

        for row in sorted(rows_to_remove, reverse=True):
            self.table.removeRow(row)
        self.modified = True
        self.log(f"🗑️ {len(rows_to_remove)}개 행 삭제됨")

    def save_all(self, silent=False):
        new_users = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 1)
            name = name_item.text().strip() if name_item else ""
            
            if name:
                title_item = self.table.item(row, 2)
                title = title_item.text().strip() if title_item else ""
                
                note_widget = self.table.cellWidget(row, 3)
                numbers = note_widget.findChild(QLineEdit).text().strip()
                
                new_users.append({"name": name, "note_title": title, "note_numbers": numbers})

        self.users = new_users
        self.config["users"] = self.users
        save_config(self.config)
        self.clear_modified_marks()
        self.log("💾 모든 변경사항이 저장되었습니다.")
        if not silent:
            QMessageBox.information(self, "저장 완료", "모든 변경사항이 저장되었습니다.")

    def export_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "엑셀 파일로 저장", "", "Excel Files (*.xlsx)")
        if not file_path:
            return

        try:
            wb = openpyxl.Workbook()
            sheet = wb.active
            sheet.title = "사용자 데이터"
            
            # 헤더 추가
            headers = ["이름", "오답노트 제목", "오답노트 번호"]
            sheet.append(headers)

            # 데이터 추가
            for row in range(self.table.rowCount()):
                name = self.table.item(row, 1).text()
                title = self.table.item(row, 2).text()
                numbers = self.table.cellWidget(row, 3).findChild(QLineEdit).text()
                sheet.append([name, title, numbers])
            
            wb.save(file_path)
            self.log(f"📄 엑셀 파일로 저장 완료: {file_path}")
            QMessageBox.information(self, "저장 완료", "엑셀 파일로 성공적으로 저장했습니다.")

        except Exception as e:
            self.log(f"❌ 엑셀 저장 실패: {e}")
            QMessageBox.critical(self, "오류", f"엑셀 저장 중 오류가 발생했습니다: {e}")

    def import_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return

        try:
            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active
            imported_users = [
                {"name": str(row[0]), "note_title": str(row[1] or ""), "note_numbers": str(row[2] or "")}
                for i, row in enumerate(sheet.iter_rows(values_only=True)) if i > 0 and row[0]
            ]
            if not imported_users:
                QMessageBox.warning(self, "안내", "엑셀에서 사용자 데이터를 찾지 못했습니다.")
                return

            reply = QMessageBox.question(
                self,
                "데이터 가져오기",
                "기존 데이터를 유지하고 엑셀 데이터를 추가하시겠습니까?\n('아니오'를 선택하면 기존 데이터가 삭제됩니다.)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            
            if reply == QMessageBox.No: # 전체 삭제 후 import
                self.users = imported_users
            else: # 기존 데이터 유지하고 추가 (중복 이름 제외)
                existing_names = {u["name"] for u in self.users}
                for u in imported_users:
                    if u["name"] not in existing_names:
                        self.users.append(u)
            
            self.load_table(from_config=False) #<-- 수정된 부분
            self.log(f"📊 {len(imported_users)}명의 사용자를 엑셀에서 불러왔습니다.")
            QMessageBox.information(self, "완료", f"{len(imported_users)}명의 사용자를 불러왔습니다.")
        except Exception as e:
            self.log(f"❌ 엑셀 불러오기 실패: {e}")
            QMessageBox.critical(self, "오류", f"엑셀 불러오기 실패: {e}")

    def export_pdf(self):
        if self.modified:
            self.save_all(silent=True)
            self.log("💾 PDF 저장을 위해 변경사항을 자동으로 저장했습니다.")

        checked_users = []
        for row in range(self.table.rowCount()):
            if self.table.cellWidget(row, 0).findChild(QCheckBox).isChecked():
                name_item = self.table.item(row, 1)
                name = name_item.text() if name_item else ""
                
                title_item = self.table.item(row, 2)
                title = title_item.text() if title_item else ""

                note_widget = self.table.cellWidget(row, 3)
                numbers_text = note_widget.findChild(QLineEdit).text()
                numbers = [num.strip() for num in numbers_text.split(",") if num.strip()]
                
                if name and numbers:
                    checked_users.append({"name": name, "note_title": title, "note_numbers": numbers})

        if not checked_users:
            QMessageBox.warning(self, "알림", "PDF로 저장할 사용자를 선택하세요.")
            return

        self.config = load_previous_config()
        save_images_to_pdf_for_dialog_users(
            config=self.config,
            users=checked_users,
            log_callback=self.log,
            parent_widget=self,
        )

    # -------------------- 메뉴 액션 및 기타 --------------------
    def open_path_dialog(self):
        dlg = PathDialog(self)
        if dlg.exec():
            self.log("경로 설정 저장 완료!")

    def open_config_dialog(self):
        dialog = DialogPdfConfig(self)
        if dialog.exec():
            self.log("PDF 설정 완료!")

    def initialize_config(self):
        if not os.path.exists("prevConfig.json"):
            QMessageBox.information(self, "초기 설정", "초기 설정을 진행합니다.\n원본/대상 폴더를 선택해주세요.")
            src = QFileDialog.getExistingDirectory(self, "원본 폴더 선택") or DEFAULT_SRC
            dst = QFileDialog.getExistingDirectory(self, "대상 폴더 선택") or DEFAULT_DST
            self.config.update({"source_dir": src, "target_dir": dst})
            save_config(self.config)
            self.log("🟢 초기 설정 완료")

    def show_version_dialog(self):
        QMessageBox.information(self, "버전 정보", "오답노트 관리 프로그램 v1.1.0")

    def closeEvent(self, event):
        if self.modified:
            reply = QMessageBox.question(self, "저장되지 않은 변경사항", "저장하지 않은 변경사항이 있습니다. 저장하시겠습니까?", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_all(silent=True)
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WrongAnswerManager()
    window.show()
    sys.exit(app.exec())