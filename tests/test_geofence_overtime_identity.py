from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path

import pytest
from app.api.routes import attendance as attendance_routes
from app.database.session import SessionLocal
from app.models.entities import (
    AttendanceRecord,
    AttendanceStatus,
    Employee,
    Shift,
    ShiftAssignment,
)
from starlette.websockets import WebSocketDisconnect

from client.app import device_identity


def test_geofence_accepts_inside_and_rejects_outside(
    client, employee_headers, approved_employee_device, monkeypatch
):
    monkeypatch.setattr(attendance_routes.settings, "geofencing_enabled", True)
    monkeypatch.setattr(attendance_routes.settings, "company_latitude", 10.776889)
    monkeypatch.setattr(attendance_routes.settings, "company_longitude", 106.700806)
    monkeypatch.setattr(attendance_routes.settings, "geofence_radius_meters", 150.0)
    monkeypatch.setattr(attendance_routes.settings, "geofence_max_accuracy_meters", 50.0)

    outside = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "outside-geofence-001",
            "latitude": 10.790000,
            "longitude": 106.700806,
            "location_accuracy_meters": 10,
        },
        headers=employee_headers,
    )
    assert outside.status_code == 403
    assert "ngoài khu vực" in outside.json()["detail"]

    inside = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "inside-geofence-001",
            "latitude": 10.776900,
            "longitude": 106.700810,
            "location_accuracy_meters": 8,
        },
        headers=employee_headers,
    )
    assert inside.status_code == 201, inside.text
    assert inside.json()["geofence_enabled"] is True
    assert inside.json()["check_in_geofence_distance_meters"] < 5


def test_geofence_rejects_imprecise_gps(
    client, employee_headers, approved_employee_device, monkeypatch
):
    monkeypatch.setattr(attendance_routes.settings, "geofencing_enabled", True)
    monkeypatch.setattr(attendance_routes.settings, "company_latitude", 10.776889)
    monkeypatch.setattr(attendance_routes.settings, "company_longitude", 106.700806)
    monkeypatch.setattr(attendance_routes.settings, "geofence_radius_meters", 150.0)
    monkeypatch.setattr(attendance_routes.settings, "geofence_max_accuracy_meters", 25.0)
    response = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "imprecise-geofence-001",
            "latitude": 10.776889,
            "longitude": 106.700806,
            "location_accuracy_meters": 100,
        },
        headers=employee_headers,
    )
    assert response.status_code == 422
    assert "chưa đủ chính xác" in response.json()["detail"]


def test_manager_reviews_overtime_and_payroll_includes_it(client, manager_headers):
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        employee.base_salary = Decimal("20000000")
        employee.attendance_bonus = Decimal("0")
        employee.overtime_multiplier = Decimal("1.50")
        shift = db.query(Shift).filter_by(code="HC").one()
        shift.start_time = time(8)
        shift.end_time = time(17)
        shift.break_minutes = 60
        db.add(
            ShiftAssignment(
                employee_id=employee.id,
                shift_id=shift.id,
                work_date=date(2024, 1, 2),
            )
        )
        record = AttendanceRecord(
            employee_id=employee.id,
            shift_id=shift.id,
            work_date=date(2024, 1, 2),
            check_in_at=datetime(2024, 1, 2, 8, tzinfo=UTC),
            check_out_at=datetime(2024, 1, 2, 18, tzinfo=UTC),
            check_in_ip="127.0.0.1",
            check_out_ip="127.0.0.1",
            status=AttendanceStatus.ON_TIME,
            worked_minutes=540,
            overtime_minutes=60,
            overtime_status="PENDING",
        )
        db.add(record)
        db.flush()
        record_id = record.id
        employee_id = employee.id

    reviewed = client.post(
        f"/api/v1/attendance/{record_id}/overtime/review",
        json={"approve": True, "note": "Đồng ý làm thêm theo phân công"},
        headers=manager_headers,
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["approved_overtime_minutes"] == 60
    assert reviewed.json()["overtime_status"] == "APPROVED"

    payroll = client.get(
        "/api/v1/payroll",
        params={"year": 2024, "month": 1},
        headers=manager_headers,
    )
    assert payroll.status_code == 200, payroll.text
    row = next(
        item for item in payroll.json()["items"] if item["employee_id"] == employee_id
    )
    assert row["approved_overtime_hours"] == 1
    assert row["overtime_earned"] == 3_750_000
    assert row["total_salary"] == row["base_earned"] + row["overtime_earned"]
    assert payroll.json()["summary"]["total_overtime"] == 3_750_000


def test_device_identity_does_not_depend_on_mac_address(monkeypatch):
    monkeypatch.setattr(device_identity, "_system_machine_id", lambda: "machine-guid")
    monkeypatch.setattr(device_identity, "_windows_volume_serial", lambda: "A1B2C3D4")
    monkeypatch.setattr(device_identity, "_installation_id", lambda _path: "installation-id")
    monkeypatch.setattr(device_identity.uuid, "getnode", lambda: 111)
    config_path = Path(".test-runtime/device-identity/config.json")
    first = device_identity.machine_fingerprint(config_path)
    monkeypatch.setattr(device_identity.uuid, "getnode", lambda: 999)
    second = device_identity.machine_fingerprint(config_path)
    assert first == second
    assert len(first) == 64


def test_websocket_query_token_is_rejected(client):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "employee", "password": "EmployeePass123!"},
    ).json()
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect(
            f"/api/v1/ws?token={login['access_token']}"
        ) as socket:
            socket.receive_json()
    assert exc.value.code == 4401
