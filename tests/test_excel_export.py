from io import BytesIO

from openpyxl import load_workbook

from client.app.ui.excel_export import styled_workbook_bytes


def test_styled_table_workbook_has_title_table_formats_and_print_layout():
    content = styled_workbook_bytes(
        "Lương & chuyên cần",
        ["Mã NV", "Họ tên", "Tổng thực nhận", "Tỷ lệ công", "Trạng thái"],
        [
            ["NV001", "Nguyễn Văn An", "12.500.000 ₫", "100.0%", "Đã duyệt"],
            ["NV002", "Trần Thị Bình", "9.750.000 ₫", "92.5%", "Chờ duyệt"],
        ],
    )

    book = load_workbook(BytesIO(content))
    sheet = book["Dữ liệu"]
    assert sheet["A1"].value == "LƯƠNG & CHUYÊN CẦN"
    assert sheet["A1"].fill.fgColor.rgb.endswith("1E3A8A")
    assert sheet["A4"].font.bold is True
    assert sheet["C5"].value == 12500000
    assert sheet["C5"].number_format == '#,##0 "₫"'
    assert sheet["D5"].value == 1
    assert sheet.freeze_panes == "A5"
    assert sheet.page_setup.orientation == "landscape"
    assert "BangDuLieu" in sheet.tables
    assert sheet.column_dimensions["B"].width >= 18


def test_excel_export_neutralizes_formula_like_user_text():
    content = styled_workbook_bytes(
        "Danh sách",
        ["Mã NV", "Họ tên"],
        [["=1+1", "+SUM(A1:A2)"], ["@command", "-danger"]],
    )

    sheet = load_workbook(BytesIO(content)).active
    assert sheet["A5"].value == "'=1+1"
    assert sheet["B5"].value == "'+SUM(A1:A2)"
    assert sheet["A6"].value == "'@command"
    assert sheet["B6"].value == "'-danger"
