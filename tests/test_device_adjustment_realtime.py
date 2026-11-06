from datetime import UTC, date, datetime, time, timedelta

from app.database.session import SessionLocal
from app.models.entities import (
    AttendanceRecord,
    AttendanceStatus,
    Department,
    Device,
    Employee,
    Notification,
)


def test_device_must_be_approved_before_attendance(client, employee_headers, admin_headers):
    fingerprint = "workstation-nv001-stable-fingerprint"
    registered = client.post(
        "/api/v1/devices",
        json={"fingerprint": fingerprint, "device_name": "Máy NV001"},
        headers=employee_headers,
    )
    assert registered.status_code == 201
    denied = client.post(
        "/api/v1/attendance/check-in",
        json={"device_fingerprint": fingerprint, "idempotency_key": "device-check-001"},
        headers=employee_headers,
    )
    assert denied.status_code == 403
    device_id = registered.json()["id"]
    approved = client.patch(
        f"/api/v1/devices/{device_id}/approve", params={"approved": True}, headers=admin_headers
    )
    assert approved.status_code == 200
    accepted = client.post(
        "/api/v1/attendance/check-in",
        json={"device_fingerprint": fingerprint, "idempotency_key": "device-check-002"},
        headers=employee_headers,
    )
    assert accepted.status_code == 201
    own_devices = client.get("/api/v1/devices/me", headers=employee_headers)
    assert own_devices.status_code == 200
    assert own_devices.json()[0]["approved"] is True


def test_manager_can_approve_device_only_in_own_department(
    client, employee_headers, manager_headers
):
    registered = client.post(
        "/api/v1/devices",
        json={"fingerprint": "manager-approved-device", "device_name": "Máy cùng phòng"},
        headers=employee_headers,
    )
    assert registered.status_code == 201

    approved = client.patch(
        f"/api/v1/devices/{registered.json()['id']}/approve",
        params={"approved": True},
        headers=manager_headers,
    )
    assert approved.status_code == 200
    assert approved.json()["approved"] is True

    with SessionLocal.begin() as db:
        other_department = Department(code="OTHER", name="Phòng khác")
        db.add(other_department)
        db.flush()
        other_employee = Employee(
            employee_code="NV-OTHER",
            full_name="Nhân viên phòng khác",
            email="other@example.local",
            department_id=other_department.id,
        )
        db.add(other_employee)
        db.flush()
        other_device = Device(
            employee_id=other_employee.id,
            fingerprint_hash="outside-manager-scope",
            device_name="Máy khác phòng",
        )
        db.add(other_device)
        db.flush()
        other_device_id = other_device.id

    denied = client.patch(
        f"/api/v1/devices/{other_device_id}/approve",
        params={"approved": True},
        headers=manager_headers,
    )
    assert denied.status_code == 403


def test_manager_can_remove_old_device_in_own_department(
    client, employee_headers, manager_headers
):
    payload = {"fingerprint": "old-device-for-removal", "device_name": "Máy cũ"}
    registered = client.post("/api/v1/devices", json=payload, headers=employee_headers)
    device_id = registered.json()["id"]

    removed = client.delete(f"/api/v1/devices/{device_id}", headers=manager_headers)

    assert removed.status_code == 200
    assert removed.json() == {"id": device_id, "deleted": True, "archived": False}
    pending = client.get(
        "/api/v1/devices", params={"approved": False}, headers=manager_headers
    )
    assert pending.status_code == 200
    assert all(item["id"] != device_id for item in pending.json())


def test_removed_device_with_attendance_is_archived_and_can_register_again(
    client, employee_headers, manager_headers, approved_employee_device
):
    check_in = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "archive-old-device-check-in",
        },
        headers=employee_headers,
    )
    assert check_in.status_code == 201
    devices = client.get("/api/v1/devices", headers=manager_headers).json()
    device_id = next(item["id"] for item in devices if item["device_name"] == "Máy kiểm thử NV001")

    removed = client.delete(f"/api/v1/devices/{device_id}", headers=manager_headers)
    assert removed.status_code == 200
    assert removed.json()["archived"] is True

    registered_again = client.post(
        "/api/v1/devices",
        json={"fingerprint": approved_employee_device, "device_name": "Máy đăng ký lại"},
        headers=employee_headers,
    )
    assert registered_again.status_code == 201
    assert registered_again.json() == {"id": device_id, "approved": False}


def test_same_workstation_can_be_registered_for_multiple_accounts(
    client, employee_headers, manager_headers
):
    payload = {"fingerprint": "shared-workstation-fingerprint", "device_name": "Máy dùng chung"}
    employee_device = client.post("/api/v1/devices", json=payload, headers=employee_headers)
    manager_device = client.post("/api/v1/devices", json=payload, headers=manager_headers)
    repeated = client.post("/api/v1/devices", json=payload, headers=employee_headers)

    assert employee_device.status_code == 201
    assert manager_device.status_code == 201
    assert manager_device.json()["id"] != employee_device.json()["id"]
    assert repeated.status_code == 201
    assert repeated.json()["id"] == employee_device.json()["id"]


def test_adjustment_request_list_and_review(
    client, employee_headers, manager_headers, approved_employee_device
):
    check_in = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "adjustment-checkin",
        },
        headers=employee_headers,
    )
    assert check_in.status_code == 201
    attendance_id = check_in.json()["id"]
    proposed = datetime.combine(date.today(), time.min, tzinfo=UTC)
    requested = client.post(
        "/api/v1/attendance/adjustments",
        json={
            "attendance_id": attendance_id,
            "proposed_check_in": proposed.isoformat(),
            "proposed_check_out": None,
            "reason": "Máy trạm khởi động chậm nên cần điều chỉnh",
        },
        headers=employee_headers,
    )
    assert requested.status_code == 201
    adjustment_id = requested.json()["id"]
    listed = client.get("/api/v1/attendance/adjustments", headers=manager_headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == adjustment_id
    reviewed = client.post(
        f"/api/v1/attendance/adjustments/{adjustment_id}/review",
        json={"approve": True, "note": "Đã đối chiếu nhật ký máy trạm"},
        headers=manager_headers,
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "APPROVED"
    with SessionLocal() as db:
        attendance_record = db.get(AttendanceRecord, attendance_id)
        assert attendance_record.late_minutes == 0
        assert attendance_record.status == AttendanceStatus.OPEN


def test_adjustment_rejects_invalid_time_order(
    client, employee_headers, manager_headers, approved_employee_device
):
    check_in = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "invalid-adjustment-checkin",
        },
        headers=employee_headers,
    )
    assert check_in.status_code == 201
    check_in_at = datetime.fromisoformat(check_in.json()["check_in_at"])
    before_check_in = check_in_at - timedelta(hours=1)

    malformed = client.post(
        "/api/v1/attendance/adjustments",
        json={
            "attendance_id": check_in.json()["id"],
            "proposed_check_in": check_in_at.isoformat(),
            "proposed_check_out": before_check_in.isoformat(),
            "reason": "Kiểm tra thứ tự thời gian không hợp lệ",
        },
        headers=employee_headers,
    )
    assert malformed.status_code == 422

    requested = client.post(
        "/api/v1/attendance/adjustments",
        json={
            "attendance_id": check_in.json()["id"],
            "proposed_check_in": None,
            "proposed_check_out": before_check_in.isoformat(),
            "reason": "Kiểm tra lúc duyệt điều chỉnh",
        },
        headers=employee_headers,
    )
    assert requested.status_code == 201
    reviewed = client.post(
        f"/api/v1/attendance/adjustments/{requested.json()['id']}/review",
        json={"approve": True, "note": "Không chấp nhận giờ sai"},
        headers=manager_headers,
    )
    assert reviewed.status_code == 409


def test_websocket_receives_attendance_broadcast(client, approved_employee_device):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "employee", "password": "EmployeePass123!"},
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    with client.websocket_connect(f"/api/v1/ws?token={login['access_token']}") as socket:
        assert socket.receive_json()["type"] == "connected"
        response = client.post(
            "/api/v1/attendance/check-in",
            json={
                "device_fingerprint": approved_employee_device,
                "idempotency_key": "websocket-checkin",
            },
            headers=headers,
        )
        assert response.status_code == 201
        message = socket.receive_json()
        assert message["type"] == "attendance_changed"
        assert message["data"]["id"] == response.json()["id"]


def test_mark_own_notification_read(client, employee_headers):
    with SessionLocal.begin() as db:
        user_id = 3
        item = Notification(
            user_id=user_id, title="Kiểm thử", message="Nội dung", category="SYSTEM"
        )
        db.add(item)
        db.flush()
        notification_id = item.id
    response = client.post(
        f"/api/v1/notifications/{notification_id}/read", headers=employee_headers
    )
    assert response.status_code == 204
    with SessionLocal() as db:
        assert db.get(Notification, notification_id).read_at is not None
