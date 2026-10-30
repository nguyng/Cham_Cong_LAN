from datetime import date, timedelta

from app.database.session import SessionLocal
from app.models.entities import Employee, LeaveBalance, RandomCheck


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


def test_excel_pdf_exports(client, employee_headers, manager_headers):
    client.post(
        "/api/v1/attendance/check-in",
        json={"device_fingerprint": None, "idempotency_key": "report-checkin"},
        headers=employee_headers,
    )
    client.post(
        "/api/v1/attendance/check-out",
        json={"device_fingerprint": None, "idempotency_key": "report-checkout"},
        headers=employee_headers,
    )
    params = {"start": str(date.today()), "end": str(date.today())}
    report = client.get("/api/v1/reports/attendance", params=params, headers=manager_headers)
    assert report.status_code == 200 and len(report.json()) == 1
    excel = client.get("/api/v1/reports/attendance.xlsx", params=params, headers=manager_headers)
    assert excel.status_code == 200 and excel.content.startswith(b"PK")
    pdf = client.get("/api/v1/reports/attendance.pdf", params=params, headers=manager_headers)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
