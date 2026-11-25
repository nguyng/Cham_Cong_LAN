from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from app.api.deps import client_ip, require_lan
from app.core.config import Settings
from app.database.session import SessionLocal
from app.models.entities import (
    AttendanceRecord,
    AttendanceStatus,
    Employee,
    SecurityAlert,
    Shift,
    ShiftAssignment,
)
from fastapi import HTTPException


def test_duplicate_employee_creation_returns_conflict(client, admin_headers):
    with SessionLocal() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        department_id = employee.department_id

    response = client.post(
        "/api/v1/employees",
        json={
            "employee_code": "NV001",
            "full_name": "Nhân viên bị trùng",
            "email": "duplicate@example.com",
            "department_id": department_id,
            "username": "duplicate-user",
            "temporary_password": "DuplicatePass123!",
            "role": "EMPLOYEE",
        },
        headers=admin_headers,
    )

    assert response.status_code == 409, response.text
    assert "đã tồn tại" in response.json()["detail"]


def test_invalid_client_ip_is_rejected_as_forbidden():
    with pytest.raises(HTTPException) as raised:
        require_lan("not-an-ip-address")

    assert raised.value.status_code == 403


def test_ipv4_mapped_internal_address_is_allowed(monkeypatch):
    settings = Settings(allowed_networks=["192.168.0.0/16"])
    monkeypatch.setattr("app.api.deps.get_settings", lambda: settings)

    require_lan("::ffff:192.168.1.25")


def test_radmin_network_is_only_allowed_when_configured(monkeypatch):
    settings = Settings(allowed_networks=["26.0.0.0/8"])
    monkeypatch.setattr("app.api.deps.get_settings", lambda: settings)

    require_lan("26.167.29.64")
    with pytest.raises(HTTPException) as raised:
        require_lan("8.8.8.8")
    assert raised.value.status_code == 403


def test_ipv4_mapped_client_address_is_displayed_as_ipv4():
    from starlette.requests import Request

    request = Request(
        {
            "type": "http",
            "method": "POST",
            "headers": [],
            "client": ("::ffff:192.168.1.25", 8000),
        }
    )

    assert client_ip(request) == "192.168.1.25"


def test_admin_dashboard_counts_system_security_alerts(client, admin_headers):
    with SessionLocal.begin() as db:
        db.add(
            SecurityAlert(
                employee_id=None,
                alert_type="SYSTEM_TEST",
                description="Cảnh báo hệ thống không gắn với nhân viên",
            )
        )

    response = client.get("/api/v1/dashboard", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["open_alerts"] == 1


def test_payroll_does_not_pay_an_unfinished_attendance(client, manager_headers):
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        employee.base_salary = Decimal("12000000")
        employee.attendance_bonus = Decimal("1000000")
        shift = db.query(Shift).filter_by(code="HC").one()
        work_date = date(2024, 1, 2)
        db.add(
            ShiftAssignment(
                employee_id=employee.id,
                shift_id=shift.id,
                work_date=work_date,
            )
        )
        db.add(
            AttendanceRecord(
                employee_id=employee.id,
                shift_id=shift.id,
                work_date=work_date,
                check_in_at=datetime(2024, 1, 2, 8, tzinfo=UTC),
                check_out_at=None,
                check_in_ip="127.0.0.1",
                status=AttendanceStatus.OPEN,
            )
        )
        employee_id = employee.id

    response = client.get(
        "/api/v1/payroll",
        params={"year": 2024, "month": 1},
        headers=manager_headers,
    )

    assert response.status_code == 200
    row = next(item for item in response.json()["items"] if item["employee_id"] == employee_id)
    assert row["work_days"] == 0
    assert row["absence_days"] == 1
    assert row["base_earned"] == 0
    assert row["bonus_earned"] == 0


def test_relative_backup_directory_is_resolved_from_server_config():
    settings = Settings(backup_directory="relative-backups")
    backup_path = Path(settings.backup_directory)

    assert backup_path.is_absolute()
    assert backup_path.name == "relative-backups"
    assert backup_path.parent.name == "server"
