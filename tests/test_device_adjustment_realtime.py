from datetime import UTC, datetime, timedelta

from app.database.session import SessionLocal
from app.models.entities import Notification


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


def test_adjustment_request_list_and_review(client, employee_headers, manager_headers):
    check_in = client.post(
        "/api/v1/attendance/check-in",
        json={"device_fingerprint": None, "idempotency_key": "adjustment-checkin"},
        headers=employee_headers,
    )
    assert check_in.status_code == 201
    attendance_id = check_in.json()["id"]
    proposed = datetime.now(UTC) - timedelta(minutes=10)
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


def test_websocket_receives_attendance_broadcast(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "employee", "password": "EmployeePass123!"},
    ).json()
    headers = {"Authorization": f"Bearer {login['access_token']}"}
    with client.websocket_connect(f"/api/v1/ws?token={login['access_token']}") as socket:
        assert socket.receive_json()["type"] == "connected"
        response = client.post(
            "/api/v1/attendance/check-in",
            json={"device_fingerprint": None, "idempotency_key": "websocket-checkin"},
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
