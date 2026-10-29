from copy import copy
from io import BytesIO

from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

HEADERS = ["Mã NV", "Họ tên", "Ngày công", "Tổng giờ", "Đi muộn", "Về sớm", "Ngày nghỉ"]


def excel_report(rows: list[dict]) -> bytes:
    book = Workbook()
    sheet = book.active
    sheet.title = "Bao cao cham cong"
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(
            [
                row["employee_code"],
                row["full_name"],
                row["work_days"],
                row["hours"],
                row["late_count"],
                row["early_count"],
                row["leave_days"],
            ]
        )
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for cell in sheet[1]:
        font = copy(cell.font)
        font.bold = True
        cell.font = font
    stream = BytesIO()
    book.save(stream)
    return stream.getvalue()


def pdf_report(rows: list[dict]) -> bytes:
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=landscape(A4), title="Bao cao cham cong")
    styles = getSampleStyleSheet()
    data = [HEADERS] + [
        [
            r["employee_code"],
            r["full_name"],
            r["work_days"],
            r["hours"],
            r["late_count"],
            r["early_count"],
            r["leave_days"],
        ]
        for r in rows
    ]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    doc.build([Paragraph("LAN Attendance - Attendance Report", styles["Title"]), table])
    return stream.getvalue()
