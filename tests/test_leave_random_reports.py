from datetime import date, timedelta
from io import BytesIO

from app.database.session import SessionLocal
from app.models.entities import Employee, LeaveBalance, RandomCheck
from app.services.reporting import excel_report, pdf_report, register_pdf_fonts
from openpyxl import load_workbook
from reportlab.pdfbase import pdfmetrics


def test_leave_request_and_approval(client, employee_headers, manager_headers):
    with SessionLocal() as db:
        leave_type_id = db.query(LeaveBalance).one().leave_type_id
    start = date.today() + timedelta(days=(7 - date.today().weekday()) % 7 + 1)
    end = start + timedelta(days=1)
    response = client.post(
        "/api/v1/leaves",
        json={
            "leave_type_id": leave_type_id,
            "start_date": str(start),
            "end_date": str(end),
            "reason": "Việc gia đình cần giải quyết",
        },
        headers=employee_headers,
    )
    assert response.status_code == 201, response.text
    leave_id = response.json()["id"]
    review = client.post(
        f"/api/v1/leaves/{leave_id}/review",
        json={"approve": True, "note": "Đồng ý nghỉ phép"},
        headers=manager_headers,
    )
    assert review.status_code == 200
    with SessionLocal() as db:
        assert float(db.query(LeaveBalance).one().used_days) > 0


def test_leave_references_and_used_balance_are_validated(
    client, employee_headers, admin_headers
):
    invalid_type = client.post(
        "/api/v1/leaves",
        json={
            "leave_type_id": 999999,
            "start_date": str(date.today() + timedelta(days=7)),
            "end_date": str(date.today() + timedelta(days=8)),
            "reason": "Kiểm tra loại nghỉ không tồn tại",
        },
        headers=employee_headers,
    )
    assert invalid_type.status_code == 409

    with SessionLocal.begin() as db:
        balance = db.query(LeaveBalance).one()
        balance.used_days = 2
        payload = {
            "employee_id": balance.employee_id,
            "leave_type_id": balance.leave_type_id,
            "year": balance.year,
            "allocated_days": 1,
        }
    reduced = client.put("/api/v1/leave-balances", json=payload, headers=admin_headers)
    assert reduced.status_code == 409


def test_shift_assignment_rejects_invalid_or_empty_schedule(client, manager_headers):
    with SessionLocal() as db:
        employee_id = db.query(Employee).filter_by(employee_code="NV001").one().id
    payload = {
        "employee_id": employee_id,
        "shift_id": 999999,
        "start_date": str(date.today()),
        "end_date": str(date.today()),
        "weekdays": [date.today().weekday()],
    }
    assert (
        client.post("/api/v1/shift-assignments", json=payload, headers=manager_headers).status_code
        == 409
    )
    payload["weekdays"] = []
    assert (
        client.post("/api/v1/shift-assignments", json=payload, headers=manager_headers).status_code
        == 422
    )


def test_random_check_response_and_alert_review(client, employee_headers, manager_headers):
    with SessionLocal() as db:
        employee_id = db.query(Employee).filter_by(employee_code="NV001").one().id
    # WebSocket không kết nối nên token thách thức không bị lộ qua HTTP; tạo challenge kiểm thử riêng.
    from datetime import UTC, datetime, timedelta

    from app.core.security import hash_token

    raw = "test-random-challenge-token-123456"
    with SessionLocal.begin() as db:
        db.add(
            RandomCheck(
                employee_id=employee_id,
                challenge_token_hash=hash_token(raw),
                sent_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(minutes=3),
            )
        )
    response = client.post(
        "/api/v1/random-checks/respond", json={"challenge_token": raw}, headers=employee_headers
    )
    assert response.status_code == 200
    assert response.json()["result"] == "VERIFIED"


def test_excel_pdf_exports(
    client, employee_headers, manager_headers, approved_employee_device
):
    client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "report-checkin",
        },
        headers=employee_headers,
    )
    client.post(
        "/api/v1/attendance/check-out",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "report-checkout",
        },
        headers=employee_headers,
    )
    params = {"start": str(date.today()), "end": str(date.today())}
    report = client.get("/api/v1/reports/attendance", params=params, headers=manager_headers)
    assert report.status_code == 200 and len(report.json()) == 1
    excel = client.get("/api/v1/reports/attendance.xlsx", params=params, headers=manager_headers)
    assert excel.status_code == 200 and excel.content.startswith(b"PK")
    workbook = load_workbook(BytesIO(excel.content))
    sheet = workbook["Báo cáo chấm công"]
    assert sheet["A1"].value == "HỆ THỐNG CHẤM CÔNG LAN — BÁO CÁO CHẤM CÔNG"
    assert sheet["A4"].font.bold is True
    assert sheet.freeze_panes == "A5"
    assert "BaoCaoChamCong" in sheet.tables
    pdf = client.get("/api/v1/reports/attendance.pdf", params=params, headers=manager_headers)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_pdf_font_contains_vietnamese_glyphs():
    regular, bold = register_pdf_fonts()

    for font_name in (regular, bold):
        font = pdfmetrics.getFont(font_name)
        assert all(ord(char) in font.face.charToGlyph for char in "Đặng Nguyễn Trường")


def test_server_reports_escape_formula_and_markup_text():
    rows = [
        {
            "employee_code": "=1+1",
            "full_name": "A & B <không phải markup>",
            "work_days": 1,
            "hours": 8,
            "late_count": 0,
            "early_count": 0,
            "leave_days": 0,
        }
    ]

    sheet = load_workbook(BytesIO(excel_report(rows))).active
    assert sheet["A5"].value == "'=1+1"
    assert sheet["B5"].value == "A & B <không phải markup>"
    assert pdf_report(rows).startswith(b"%PDF")
