from datetime import UTC, date, datetime, time, timedelta

from app.api.common import business_days_by_year
from app.core.security import hash_token
from app.database.session import SessionLocal
from app.models.entities import (
    Device,
    Employee,
    LeaveBalance,
    RandomCheck,
    SecurityAlert,
    Shift,
)


def _future_workday() -> date:
    result = date.today() + timedelta(days=7)
    while result.weekday() >= 5:
        result += timedelta(days=1)
    return result


def test_reversed_date_ranges_are_rejected(
    client, employee_headers, manager_headers
):
    params = {"start": str(date.today()), "end": str(date.today() - timedelta(days=1))}
    assert client.get("/api/v1/attendance", params=params, headers=employee_headers).status_code == 400
    assert (
        client.get("/api/v1/shift-assignments", params=params, headers=employee_headers).status_code
        == 400
    )
    assert (
        client.get("/api/v1/reports/attendance", params=params, headers=manager_headers).status_code
        == 400
    )
    assert (
        client.get(
            "/api/v1/reports/attendance.xlsx", params=params, headers=manager_headers
        ).status_code
        == 400
    )


def test_only_leave_owner_can_cancel(client, employee_headers, manager_headers):
    with SessionLocal() as db:
        leave_type_id = db.query(LeaveBalance).one().leave_type_id
    created = client.post(
        "/api/v1/leaves",
        json={
            "leave_type_id": leave_type_id,
            "start_date": str(_future_workday()),
            "end_date": str(_future_workday()),
            "reason": "Kiểm tra quyền hủy đơn nghỉ phép",
        },
        headers=employee_headers,
    )
    assert created.status_code == 201
    denied = client.post(
        f"/api/v1/leaves/{created.json()['id']}/cancel", headers=manager_headers
    )
    assert denied.status_code == 403


def test_cross_year_leave_uses_each_year_balance(
    client, employee_headers, manager_headers
):
    first_year = date.today().year + 1
    start = date(first_year, 12, 29)
    end = date(first_year + 1, 1, 4)
    required = business_days_by_year(start, end)
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        leave_type_id = db.query(LeaveBalance).one().leave_type_id
        for year in required:
            db.add(
                LeaveBalance(
                    employee_id=employee.id,
                    leave_type_id=leave_type_id,
                    year=year,
                    allocated_days=12,
                    used_days=0,
                )
            )

    created = client.post(
        "/api/v1/leaves",
        json={
            "leave_type_id": leave_type_id,
            "start_date": str(start),
            "end_date": str(end),
            "reason": "Nghỉ phép giao giữa hai năm",
        },
        headers=employee_headers,
    )
    assert created.status_code == 201, created.text
    leave_id = created.json()["id"]
    approved = client.post(
        f"/api/v1/leaves/{leave_id}/review",
        json={"approve": True, "note": "Đủ quỹ phép từng năm"},
        headers=manager_headers,
    )
    assert approved.status_code == 200, approved.text
    with SessionLocal() as db:
        balances = {
            item.year: item.used_days
            for item in db.query(LeaveBalance).filter(LeaveBalance.year.in_(required)).all()
        }
        assert balances == required

    cancelled = client.post(f"/api/v1/leaves/{leave_id}/cancel", headers=employee_headers)
    assert cancelled.status_code == 200
    with SessionLocal() as db:
        assert all(
            item.used_days == 0
            for item in db.query(LeaveBalance).filter(LeaveBalance.year.in_(required)).all()
        )


def test_duplicate_pending_adjustment_is_rejected(
    client, employee_headers, approved_employee_device
):
    checked_in = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "logic-audit-adjustment-checkin",
        },
        headers=employee_headers,
    )
    assert checked_in.status_code == 201
    payload = {
        "attendance_id": checked_in.json()["id"],
        "proposed_check_in": datetime.now(UTC).isoformat(),
        "reason": "Điều chỉnh giờ vào để kiểm tra trùng yêu cầu",
    }
    assert client.post("/api/v1/attendance/adjustments", json=payload, headers=employee_headers).status_code == 201
    assert client.post("/api/v1/attendance/adjustments", json=payload, headers=employee_headers).status_code == 409


def test_random_check_requires_open_attendance_and_links_record(
    client, employee_headers, manager_headers, approved_employee_device
):
    with SessionLocal() as db:
        employee_id = db.query(Employee).filter_by(employee_code="NV001").one().id
    assert (
        client.post(f"/api/v1/random-checks/{employee_id}", headers=manager_headers).status_code
        == 409
    )
    checked_in = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "logic-audit-random-checkin",
        },
        headers=employee_headers,
    )
    assert checked_in.status_code == 201
    triggered = client.post(f"/api/v1/random-checks/{employee_id}", headers=manager_headers)
    assert triggered.status_code == 201
    with SessionLocal() as db:
        item = db.get(RandomCheck, triggered.json()["id"])
        assert item.attendance_id == checked_in.json()["id"]


def test_late_random_check_response_creates_alert(client, employee_headers):
    raw_token = "expired-random-check-token-123456"
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        item = RandomCheck(
            employee_id=employee.id,
            challenge_token_hash=hash_token(raw_token),
            sent_at=datetime.now(UTC) - timedelta(minutes=5),
            expires_at=datetime.now(UTC) - timedelta(minutes=2),
        )
        db.add(item)
        db.flush()
        check_id = item.id
    response = client.post(
        "/api/v1/random-checks/respond",
        json={"challenge_token": raw_token},
        headers=employee_headers,
    )
    assert response.status_code == 410
    with SessionLocal() as db:
        alert = db.query(SecurityAlert).filter_by(alert_type="RANDOM_CHECK_MISSED").one()
        assert alert.evidence["random_check_id"] == check_id


def test_duplicate_catalog_updates_return_conflict(client, admin_headers):
    first = client.post(
        "/api/v1/positions", json={"code": "P1", "name": "Vị trí 1"}, headers=admin_headers
    )
    second = client.post(
        "/api/v1/positions", json={"code": "P2", "name": "Vị trí 2"}, headers=admin_headers
    )
    assert first.status_code == second.status_code == 201
    duplicate_position = client.put(
        f"/api/v1/positions/{second.json()['id']}",
        json={"code": "P1", "name": "Vị trí khác"},
        headers=admin_headers,
    )
    assert duplicate_position.status_code == 409

    created_shift = client.post(
        "/api/v1/shifts",
        json={
            "code": "CA2",
            "name": "Ca phụ",
            "start_time": str(time(8, 0)),
            "end_time": str(time(17, 0)),
            "break_minutes": 60,
            "late_grace_minutes": 5,
            "early_grace_minutes": 5,
        },
        headers=admin_headers,
    )
    assert created_shift.status_code == 201
    duplicate_shift = client.put(
        f"/api/v1/shifts/{created_shift.json()['id']}",
        json={
            "code": "HC",
            "name": "Ca trùng mã",
            "start_time": str(time(8, 0)),
            "end_time": str(time(17, 0)),
            "break_minutes": 60,
            "late_grace_minutes": 5,
            "early_grace_minutes": 5,
        },
        headers=admin_headers,
    )
    assert duplicate_shift.status_code == 409


def test_inactive_device_must_be_registered_again_before_approval(
    client, manager_headers
):
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        device = Device(
            employee_id=employee.id,
            fingerprint_hash="inactive-device-fingerprint-hash",
            device_name="Thiết bị đã xóa",
            active=False,
            approved=False,
        )
        db.add(device)
        db.flush()
        device_id = device.id
    response = client.patch(
        f"/api/v1/devices/{device_id}/approve",
        params={"approved": True},
        headers=manager_headers,
    )
    assert response.status_code == 409


def test_employee_rejects_missing_or_inactive_catalog_references(client, admin_headers):
    payload = {
        "employee_code": "BADREF",
        "full_name": "Nhân viên tham chiếu lỗi",
        "email": "badref@example.com",
        "department_id": 999_999,
        "position_id": None,
        "hire_date": str(date.today()),
        "username": "badref",
        "temporary_password": "Temporary123!",
        "role": "EMPLOYEE",
    }
    missing = client.post("/api/v1/employees", json=payload, headers=admin_headers)
    assert missing.status_code == 409
    assert "Phòng ban" in missing.json()["detail"]

    position = client.post(
        "/api/v1/positions",
        json={"code": "INACTIVE", "name": "Chức vụ ngừng dùng"},
        headers=admin_headers,
    )
    assert position.status_code == 201
    assert (
        client.delete(
            f"/api/v1/positions/{position.json()['id']}", headers=admin_headers
        ).status_code
        == 204
    )
    payload["department_id"] = None
    payload["position_id"] = position.json()["id"]
    inactive = client.post("/api/v1/employees", json=payload, headers=admin_headers)
    assert inactive.status_code == 409
    assert "Chức vụ" in inactive.json()["detail"]


def test_employee_with_open_attendance_cannot_be_deactivated(
    client, employee_headers, admin_headers, approved_employee_device
):
    checked_in = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "deactivate-open-attendance",
        },
        headers=employee_headers,
    )
    assert checked_in.status_code == 201
    employee_id = checked_in.json()["employee_id"]
    response = client.patch(
        f"/api/v1/employees/{employee_id}/active",
        params={"active": False},
        headers=admin_headers,
    )
    assert response.status_code == 409
    assert client.get("/api/v1/me", headers=employee_headers).status_code == 200


def test_shift_assignment_requires_at_least_one_matching_date(client, manager_headers):
    with SessionLocal() as db:
        employee_id = db.query(Employee).filter_by(employee_code="NV001").one().id
        shift_id = db.query(Shift).filter_by(code="HC").one().id
    target = _future_workday()
    non_matching_weekday = (target.weekday() + 1) % 7
    response = client.post(
        "/api/v1/shift-assignments",
        json={
            "employee_id": employee_id,
            "shift_id": shift_id,
            "start_date": str(target),
            "end_date": str(target),
            "weekdays": [non_matching_weekday],
        },
        headers=manager_headers,
    )
    assert response.status_code == 400


def test_active_catalog_filters_hide_archived_rows(client, admin_headers):
    created = client.post(
        "/api/v1/positions",
        json={"code": "ARCHIVED", "name": "Chức vụ lưu trữ"},
        headers=admin_headers,
    )
    assert created.status_code == 201
    assert (
        client.delete(
            f"/api/v1/positions/{created.json()['id']}", headers=admin_headers
        ).status_code
        == 204
    )
    active = client.get(
        "/api/v1/positions", params={"active": True}, headers=admin_headers
    )
    archived = client.get(
        "/api/v1/positions", params={"active": False}, headers=admin_headers
    )
    assert created.json()["id"] not in {item["id"] for item in active.json()}
    assert created.json()["id"] in {item["id"] for item in archived.json()}


def test_large_iterative_date_ranges_are_rejected(
    client, employee_headers, manager_headers
):
    start = date.today()
    end = start + timedelta(days=367)
    with SessionLocal() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        leave_type_id = db.query(LeaveBalance).one().leave_type_id
        shift_id = db.query(Shift).filter_by(code="HC").one().id

    leave = client.post(
        "/api/v1/leaves",
        json={
            "leave_type_id": leave_type_id,
            "start_date": str(start),
            "end_date": str(end),
            "reason": "Khoảng nghỉ quá dài cần bị từ chối",
        },
        headers=employee_headers,
    )
    assert leave.status_code == 422

    assignment = client.post(
        "/api/v1/shift-assignments",
        json={
            "employee_id": employee.id,
            "shift_id": shift_id,
            "start_date": str(start),
            "end_date": str(end),
            "weekdays": [0, 1, 2, 3, 4],
        },
        headers=manager_headers,
    )
    assert assignment.status_code == 422

    report = client.get(
        "/api/v1/reports/attendance",
        params={"start": str(start), "end": str(start + timedelta(days=3_651))},
        headers=manager_headers,
    )
    assert report.status_code == 400


def test_identifiers_are_trimmed_and_whitespace_only_names_are_rejected(
    client, admin_headers
):
    blank = client.post(
        "/api/v1/positions",
        json={"code": "   ", "name": "   "},
        headers=admin_headers,
    )
    assert blank.status_code == 422

    with SessionLocal() as db:
        department_id = db.query(Employee).filter_by(employee_code="NV001").one().department_id
    created = client.post(
        "/api/v1/employees",
        json={
            "employee_code": " TRIM01 ",
            "full_name": " Nhân viên chuẩn hóa ",
            "email": "trim01@example.com",
            "department_id": department_id,
            "username": " trimuser ",
            "temporary_password": "Temporary123!",
            "role": "EMPLOYEE",
        },
        headers=admin_headers,
    )
    assert created.status_code == 201, created.text
    assert created.json()["employee_code"] == "TRIM01"
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "trimuser", "password": "Temporary123!"},
    )
    assert login.status_code == 200
