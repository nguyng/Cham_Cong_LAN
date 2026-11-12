from io import BytesIO
from re import sub

from openpyxl import Workbook
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.table import Table, TableStyleInfo

TITLE_FILL = PatternFill("solid", fgColor="1E3A8A")
HEADER_FILL = PatternFill("solid", fgColor="2563EB")
SUBTITLE_FILL = PatternFill("solid", fgColor="DBEAFE")
THIN_BORDER = Border(
    left=Side(style="thin", color="CBD5E1"),
    right=Side(style="thin", color="CBD5E1"),
    top=Side(style="thin", color="CBD5E1"),
    bottom=Side(style="thin", color="CBD5E1"),
)


def _cell_value(text: str) -> tuple[object, str | None]:
    cleaned = text.strip()
    if cleaned.endswith("₫"):
        digits = sub(r"[^0-9-]", "", cleaned)
        if digits not in ("", "-"):
            return int(digits), '#,##0 "₫"'
    if cleaned.endswith("%"):
        try:
            return float(cleaned[:-1].replace(",", ".")) / 100, "0.0%"
        except ValueError:
            pass
    if cleaned.startswith(("=", "+", "-", "@")):
        return f"'{cleaned}", None
    return cleaned, None


def styled_workbook_bytes(title: str, headers: list[str], rows: list[list[str]]) -> bytes:
    """Create a polished, printable Excel workbook from the currently displayed table."""
    book = Workbook()
    sheet = book.active
    sheet.title = "Dữ liệu"
    sheet.sheet_view.showGridLines = False
    sheet.freeze_panes = "A5"
    sheet.auto_filter.ref = f"A4:{sheet.cell(4, len(headers)).coordinate}"
    sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    title_cell = sheet.cell(1, 1, title.upper())
    title_cell.fill = TITLE_FILL
    title_cell.font = Font(name="Aptos Display", size=18, bold=True, color="FFFFFF")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    sheet.row_dimensions[1].height = 34

    sheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
    subtitle = sheet.cell(2, 1, f"Tổng số bản ghi trong bảng: {len(rows)}")
    subtitle.fill = SUBTITLE_FILL
    subtitle.font = Font(name="Aptos", size=10, italic=True, color="1E3A8A")
    subtitle.alignment = Alignment(horizontal="left", vertical="center")
    sheet.row_dimensions[2].height = 22

    for column, header in enumerate(headers, start=1):
        cell = sheet.cell(4, column, header)
        cell.fill = HEADER_FILL
        cell.font = Font(name="Aptos", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = THIN_BORDER
    sheet.row_dimensions[4].height = 31

    for row_number, values in enumerate(rows, start=5):
        for column, text in enumerate(values, start=1):
            value, number_format = _cell_value(text)
            cell = sheet.cell(row_number, column, value)
            cell.font = Font(name="Aptos", size=10, color="0F172A")
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            cell.border = THIN_BORDER
            if number_format:
                cell.number_format = number_format
                cell.alignment = Alignment(horizontal="right", vertical="center")
        sheet.row_dimensions[row_number].height = 24

    table_ref = f"A4:{sheet.cell(max(4, len(rows) + 4), len(headers)).coordinate}"
    table = Table(displayName="BangDuLieu", ref=table_ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    sheet.add_table(table)

    status_columns = [index + 1 for index, header in enumerate(headers) if "trạng thái" in header.lower()]
    for column in status_columns:
        letter = sheet.cell(4, column).column_letter
        target = f"{letter}5:{letter}{max(5, len(rows) + 4)}"
        for word, background, foreground in (
            ("Đã duyệt", "DCFCE7", "166534"),
            ("Đúng giờ", "DCFCE7", "166534"),
            ("Chờ duyệt", "FEF3C7", "92400E"),
            ("Từ chối", "FEE2E2", "991B1B"),
            ("Đã hủy", "E2E8F0", "334155"),
        ):
            sheet.conditional_formatting.add(
                target,
                FormulaRule(
                    formula=[f'ISNUMBER(SEARCH("{word}",{letter}5))'],
                    fill=PatternFill("solid", fgColor=background),
                    font=Font(color=foreground, bold=True),
                ),
            )

    for column, header in enumerate(headers, start=1):
        values = [str(header), *(str(row[column - 1]) for row in rows if column <= len(row))]
        width = min(42, max(11, max((len(value) for value in values), default=10) + 3))
        if any(keyword in header.lower() for keyword in ("họ tên", "nội dung", "mô tả", "lý do")):
            width = max(width, 22)
        sheet.column_dimensions[sheet.cell(4, column).column_letter].width = width

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
