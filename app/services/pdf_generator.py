import io
import os
import subprocess
import sys
from copy import deepcopy

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from PySide6.QtWidgets import QMessageBox

from config import DEFAULT_DST


def save_images_to_pdf_for_dialog_users(config, users, log_callback, parent_widget):
    """Dialog 전용 PDF 생성"""
    source_dir = config.get("source_dir", "")
    template_path = config.get("template_dir", "")
    if not template_path or not os.path.isfile(template_path):
        log_callback("❌ 템플릿 경로가 없습니다.")
        QMessageBox.warning(parent_widget, "경고", "PDF 템플릿 파일이 설정되지 않았습니다.")
        return

    try:
        template_reader = PdfReader(template_path)
        template_page = template_reader.pages[0]
        page_w, page_h = A4
        cfg = config
        h_margin = cfg.get("h_margin", 20)
        v_margin = cfg.get("v_margin", 30)
        target_w = cfg.get("target_w", 300)
        target_h = cfg.get("target_h", 160)
        img_h = (page_h - (2 + 1) * v_margin) / 2

        for user in users:
            try:
                user_folder = os.path.join(cfg.get("target_dir", DEFAULT_DST), user["name"])
                os.makedirs(user_folder, exist_ok=True)

                base_pdf_name = f"{user['name']}_{user['note_title']}.pdf"
                pdf_path = os.path.join(user_folder, base_pdf_name)
                counter = 1
                while os.path.exists(pdf_path):
                    pdf_path = os.path.join(user_folder, f"{user['name']}_{user['note_title']}_{counter}.pdf")
                    counter += 1

                writer = PdfWriter()

                for i, note_number in enumerate(user["note_numbers"]):
                    note_number = note_number.strip()
                    if not note_number:
                        continue

                    img_file = os.path.join(source_dir, f"{note_number}.jpg")
                    if not os.path.isfile(img_file):
                        log_callback(f"⚠️ 이미지 파일 없음: {img_file}")
                        continue

                    idx_in_page = i % 2
                    if idx_in_page == 0:
                        packet = io.BytesIO()
                        c = canvas.Canvas(packet, pagesize=A4)

                    row = idx_in_page
                    x = h_margin
                    y = page_h - v_margin - (row + 1) * img_h - row * v_margin

                    x_offset = cfg.get("x_offset1", 0) if idx_in_page == 0 else cfg.get("x_offset2", 0)
                    y_offset = cfg.get("y_offset1", -50) if idx_in_page == 0 else cfg.get("y_offset2", 10)

                    try:
                        img = ImageReader(img_file)
                        iw, ih = img.getSize()
                        ratio = min(target_w / iw, target_h / ih)
                        draw_w = iw * ratio
                        draw_h = ih * ratio
                        draw_x = x + (target_w - draw_w) / 2 + x_offset
                        draw_y = y + (target_h - draw_h) / 2 + y_offset
                        c.drawImage(img, draw_x, draw_y, width=draw_w, height=draw_h)
                    except Exception as e:
                        log_callback(f"⚠️ 이미지 삽입 실패: {img_file} ({e})")
                        continue

                    if idx_in_page == 1 or i == len(user["note_numbers"]) - 1:
                        c.save()
                        packet.seek(0)
                        overlay_pdf = PdfReader(packet)
                        base_page_copy = deepcopy(template_page)
                        base_page_copy.merge_page(overlay_pdf.pages[0])
                        writer.add_page(base_page_copy)

                with open(pdf_path, "wb") as f:
                    writer.write(f)
                log_callback(f"✅ PDF 다중생성 완료: {pdf_path}")

            except Exception as e:
                log_callback(f"❌ 사용자 {user['name']} PDF 생성 실패: {e}")

        QMessageBox.information(parent_widget, "알림", "선택된 사용자의 PDF 생성이 완료되었습니다.")

        # 생성된 파일이 있는 폴더 열기
        target_dir = os.path.abspath(cfg.get("target_dir", DEFAULT_DST))
        try:
            if sys.platform == "win32":
                os.startfile(target_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", target_dir])
            else:
                subprocess.Popen(["xdg-open", target_dir])
            log_callback(f"📁 폴더 열기: {target_dir}")
        except Exception as e:
            log_callback(f"❌ 폴더를 여는 데 실패했습니다: {e}")

    except Exception as e:
        log_callback(f"❌ PDF 생성 중 오류 발생: {e}")
        QMessageBox.critical(parent_widget, "오류", f"PDF 생성 중 오류가 발생했습니다: {e}")
