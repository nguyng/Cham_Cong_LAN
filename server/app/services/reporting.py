from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table as ExcelTable
from openpyxl.worksheet.table import TableStyleInfo
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

from app.core.config import get_settings

HEADERS = ["Mã NV", "Họ tên", "Ngày công", "Tổng giờ", "Đi muộn", "Về sớm", "Ngày nghỉ"]
PDF_FONT = "AttendanceUnicode"
PDF_FONT_BOLD = "AttendanceUnicodeBold"


def _safe_excel_text(value: object) -> str:
    text = str(value)
    return f"'{text}" if text.startswith(("=", "+", "-", "@")) else text


def _font_candidates() -> list[tuple[Path, Path]]:
    settings = get_settings()
    configured_regular = settings.report_pdf_font
    configured_bold = settings.report_pdf_font_bold
    candidates: list[tuple[Path, Path]] = []
    if configured_regular:
        regular = Path(configured_regular)
        candidates.append((regular, Path(configured_bold) if configured_bold else regular))
    assets = Path(__file__).resolve().parents[1] / "assets" / "fonts"
    candidates.extend(
        [
            (assets / "DejaVuSans.ttf", assets / "DejaVuSans-Bold.ttf"),
            (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
            (Path("C:/Windows/Fonts/segoeui.ttf"), Path("C:/Windows/Fonts/segoeuib.ttf")),
            (
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ),
        ]
    )
    return candidates


def register_pdf_fonts() -> tuple[str, str]:
    """Register a TrueType font that contains the complete Vietnamese alphabet."""
    if PDF_FONT in pdfmetrics.getRegisteredFontNames():
        return PDF_FONT, PDF_FONT_BOLD
    for regular, bold in _font_candidates():
        if regular.is_file():
            bold = bold if bold.is_file() else regular
            pdfmetrics.registerFont(TTFont(PDF_FONT, str(regular)))
            pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, str(bold)))
            return PDF_FONT, PDF_FONT_BOLD
    raise RuntimeError(
        "Không tìm thấy font Unicode để xuất PDF. "
        "Hãy cấu hình REPORT_PDF_FONT và REPORT_PDF_FONT_BOLD."
    )


def excel_report(rows: list[dict]) -> bytes:
    book = Workbook()
    sheet = book.active
    sheet.title = "Báo cáo chấm công"
    sheet.sheet_view.showGridLines = False
    sheet.merge_cells("A1:G1")
    title = sheet["A1"]
    title.value = "HỆ THỐNG CHẤM CÔNG LAN — BÁO CÁO CHẤM CÔNG"
    title.fill = PatternFill("solid", fgColor="1E3A8A")
    title.font = Font(name="Aptos Display", size=18, bold=True, color="FFFFFF")
    title.alignment = Alignment(horizontal="center", vertical="center")
    sheet.row_dimensions[1].height = 34
    sheet.merge_cells("A2:G2")
    summary = sheet["A2"]
    summary.value = f"Tổng số nhân viên có dữ liệu trong kỳ: {len(rows)}"
    summary.fill = PatternFill("solid", fgColor="DBEAFE")
    summary.font = Font(name="Aptos", size=10, italic=True, color="1E3A8A")
    summary.alignment = Alignment(vertical="center")
    sheet.append([])
    sheet.append(HEADERS)
    for row in rows:
        sheet.append(
            [
                _safe_excel_text(row["employee_code"]),
                _safe_excel_text(row["full_name"]),
                row["work_days"],
                row["hours"],
                row["late_count"],
                row["early_count"],
                row["leave_days"],
            ]
        )
    thin = Side(style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for cell in sheet[4]:
        cell.fill = PatternFill("solid", fgColor="2563EB")
        cell.font = Font(name="Aptos", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    sheet.row_dimensions[4].height = 31
    for row in sheet.iter_rows(min_row=5, max_row=sheet.max_row):
        for cell in row:
            cell.font = Font(name="Aptos", size=10, color="0F172A")
            cell.alignment = Alignment(vertical="center")
            cell.border = border
        row[2].number_format = "0.0"
        row[3].number_format = "0.00"
        row[4].number_format = "0"
        row[5].number_format = "0"
        row[6].number_format = "0.0"
        sheet.row_dimensions[row[0].row].height = 24
    table_ref = f"A4:G{max(4, sheet.max_row)}"
    table = ExcelTable(displayName="BaoCaoChamCong", ref=table_ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    sheet.add_table(table)
    widths = (15, 28, 14, 14, 14, 14, 14)
    for column, width in enumerate(widths, start=1):
        sheet.column_dimensions[sheet.cell(4, column).column_letter].width = width
    sheet.freeze_panes = "A5"
    sheet.auto_filter.ref = table_ref
    sheet.print_title_rows = "1:4"
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.oddFooter.center.text = "Trang &P / &N"
    sheet.oddFooter.right.text = "Hệ thống chấm công LAN"
    stream = BytesIO()
    book.save(stream)
    return stream.getvalue()


def pdf_report(rows: list[dict]) -> bytes:
    regular_font, bold_font = register_pdf_fonts()
    stream = BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=landscape(A4), title="Báo cáo chấm công")
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "VietnameseTitle",
        parent=styles["Title"],
        fontName=bold_font,
    )
    cell_style = ParagraphStyle(
        "VietnameseCell",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=8,
        leading=10,
    )
    header_style = ParagraphStyle(
        "VietnameseHeader",
        parent=cell_style,
        fontName=bold_font,
        textColor=colors.white,
        alignment=1,
    )
    raw_data = [HEADERS] + [
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
    data = [
        [
            Paragraph(escape(str(value)), header_style if row_index == 0 else cell_style)
            for value in row
        ]
        for row_index, row in enumerate(raw_data)
    ]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), bold_font),
                ("FONTNAME", (0, 1), (-1, -1), regular_font),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    doc.build([Paragraph("HỆ THỐNG CHẤM CÔNG LAN — BÁO CÁO CHẤM CÔNG", title_style), table])
    return stream.getvalue()
