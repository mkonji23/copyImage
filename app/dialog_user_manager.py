import os
import sys
from copy import deepcopy
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QCheckBox,
    QWidget,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from config import load_previous_config, save_config
import openpyxl


class DialogUserManager(QDialog):
    def __init__(self, parent=None, parent_app=None):
        super().__init__(parent)
        self.setWindowTitle("오답노트 사용자 관리")
        self.resize(750, 420)
        self.parent_app = parent_app  # 메인 앱 호출용

        # 설정 로드
        self.config = load_previous_config() or {"users": []}
        self.users = self.config.get("users", [])
        self.modified_rows = set()
        self.modified = False
        self.selected_user = None

        # 레이아웃
        main_layout = QVBoxLayout()
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton("신규")
        self.del_btn = QPushButton("삭제")
        self.import_btn = QPushButton("엑셀 불러오기")
        self.select_btn = QPushButton("선택")
        self.save_btn = QPushButton("저장")
        self.pdf_btn = QPushButton("PDF 저장")
        self.close_btn = QPushButton("닫기")

        for b in [
            self.add_btn,
            self.del_btn,
            self.import_btn,
            self.select_btn,
            self.save_btn,
            self.pdf_btn,
            self.close_btn,
        ]:
            btn_layout.addWidget(b)

        main_layout.addLayout(btn_layout)

        # 테이블
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["", "이름", "오답노트 제목", "오답노트 번호"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().resizeSection(0, 40)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)  # 전체 행 선택
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        header = self.table.horizontalHeader()
        header_widget = QWidget(self.table)
        layout = QHBoxLayout(header_widget)
        layout.setAlignment(Qt.AlignCenter | Qt.AlignBottom)  # 아래로 내려주기
        layout.setContentsMargins(0, 0, 0, 0)  # 아래 여백
        header_widget.setLayout(layout)
        header_widget.setFixedWidth(40)
        header_widget.setParent(self.table)
        header_widget.move(header.sectionPosition(0), 0)
        header_widget.show()

        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

        # 이벤트
        self.add_btn.clicked.connect(self.add_row)
        self.del_btn.clicked.connect(self.delete_selected)
        self.import_btn.clicked.connect(self.import_excel)
        self.select_btn.clicked.connect(self.select_row)
        self.save_btn.clicked.connect(self.save_all)
        self.pdf_btn.clicked.connect(self.export_pdf)
        self.close_btn.clicked.connect(self.close)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.table.cellDoubleClicked.connect(self.start_edit_cell)
        self.table.cellClicked.connect(self.on_cell_click_row)  # 클릭 시 전체 체크

        # 초기 로드
        self.load_table()

    # -------------------- 테이블 --------------------
    def load_table(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for user in self.users:
            self.add_table_row(user)
        self.table.blockSignals(False)

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
        w.setLayout(l)
        self.table.setCellWidget(row, 0, w)

        name = user.get("name", "") if user else ""
        title = user.get("note_title", "") if user else ""
        numbers = user.get("note_numbers", "") if user else ""

        self.table.setItem(row, 1, QTableWidgetItem(name))
        self.table.setItem(row, 2, QTableWidgetItem(title))
        self.table.setItem(row, 3, QTableWidgetItem(numbers))

    # -------------------- 셀 수정 표시 --------------------
    def on_cell_changed(self, row, col):
        if col > 0:
            self.modified = True
            self.modified_rows.add(row)
            self.mark_row_as_modified(row)

    def mark_row_as_modified(self, row):
        for col in range(1, 4):
            item = self.table.item(row, col)
            if item:
                item.setBackground(QColor(255, 255, 200))

    def clear_modified_marks(self):
        for row in list(self.modified_rows):
            for col in range(1, 4):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QColor(255, 255, 255))
        self.modified_rows.clear()
        self.modified = False

    # -------------------- 편집 --------------------
    def start_edit_cell(self, row, col):
        if col > 0:
            self.table.editItem(self.table.item(row, col))

    def add_row(self):
        self.add_table_row()
        self.modified = True
        row = self.table.rowCount() - 1
        self.mark_row_as_modified(row)

    def delete_selected(self):
        remove_rows = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                remove_rows.append(row)
        if not remove_rows:
            QMessageBox.information(self, "안내", "삭제할 사용자를 선택하세요.")
            return
        for row in sorted(remove_rows, reverse=True):
            self.table.removeRow(row)
        self.modified = True
        QMessageBox.information(self, "삭제됨", "선택된 사용자가 삭제되었습니다.")

    def import_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "엑셀 파일 선택", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return
        try:
            wb = openpyxl.load_workbook(file_path)
            sheet = wb.active
            imported_users = []
            for i, row in enumerate(sheet.iter_rows(values_only=True)):
                if i == 0:
                    continue
                name, note_title, note_numbers = row[:3]
                if not name:
                    continue
                imported_users.append(
                    {"name": str(name), "note_title": str(note_title or ""), "note_numbers": str(note_numbers or "")}
                )
            if not imported_users:
                QMessageBox.warning(self, "안내", "엑셀에서 사용자 데이터를 찾지 못했습니다.")
                return
            reply = QMessageBox.question(
                self,
                "데이터 불러오기",
                "기존 데이터를 덮어쓰시겠습니까?\n(아니오를 선택하면 병합됩니다.)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.users = imported_users
            else:
                existing_names = {u["name"] for u in self.users}
                for u in imported_users:
                    if u["name"] not in existing_names:
                        self.users.append(u)
            self.modified = True
            self.load_table()
            QMessageBox.information(self, "완료", f"{len(imported_users)}명의 사용자 불러옴")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"엑셀 불러오기 실패: {e}")

    def select_row(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "안내", "선택된 사용자가 없습니다.")
            return
        name = self.table.item(row, 1).text().strip()
        note_title = self.table.item(row, 2).text().strip()
        note_numbers = self.table.item(row, 3).text().strip()
        if not name:
            QMessageBox.warning(self, "안내", "이름이 비어있습니다.")
            return
        self.selected_user = {"name": name, "note_title": note_title, "note_numbers": note_numbers}
        self.accept()

    def save_all(self):
        new_users = []
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 1).text().strip()
            title = self.table.item(row, 2).text().strip()
            numbers = self.table.item(row, 3).text().strip()
            if name:
                new_users.append({"name": name, "note_title": title, "note_numbers": numbers})
        self.users = new_users
        self.config["users"] = self.users
        save_config(self.config)
        self.clear_modified_marks()
        QMessageBox.information(self, "저장 완료", "모든 변경사항이 저장되었습니다.")

    def closeEvent(self, event):
        if self.modified:
            reply = QMessageBox.question(
                self,
                "저장되지 않은 변경사항",
                "저장하지 않은 변경사항이 있습니다. 저장 후 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            if reply == QMessageBox.Yes:
                self.save_all()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    # -------------------- 체크박스 --------------------
    def on_header_checkbox_clicked(self, state):
        check = state == Qt.Checked
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(check)

    def on_cell_click_row(self, row, col):
        # 클릭 시 체크박스 toggle
        if col != 0:
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(not checkbox.isChecked())

    # -------------------- PDF 저장 --------------------
    def export_pdf(self):
        checked_users = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox and checkbox.isChecked():
                user = {
                    "name": self.table.item(row, 1).text(),
                    "note_title": self.table.item(row, 2).text(),
                    "note_numbers": [num.strip() for num in self.table.item(row, 3).text().split(",") if num.strip()],
                }
                checked_users.append(user)
        if not checked_users:
            QMessageBox.warning(self, "알림", "체크된 사용자가 없습니다.")
            return
        if self.parent_app:
            self.parent_app.save_images_to_pdf_for_dialog_users(checked_users)
        else:
            QMessageBox.information(self, "알림", "PDF 생성용 부모 앱이 연결되어 있지 않습니다.")


# -------------------- 테스트 실행 --------------------
if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dlg = DialogUserManager()
    dlg.exec()
