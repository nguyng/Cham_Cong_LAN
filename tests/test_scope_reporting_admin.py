from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from app.core.config import get_settings
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.main import manager as connection_manager
from app.models.entities import (
    AttendanceAdjustment,
    AttendanceRecord,
    Department,
    Employee,
    LeaveRequest,
    LeaveType,
    RequestStatus,
    Role,
    RoleName,
    SecurityAlert,
    Shift,
    ShiftAssignment,
    User,
)


def create_other_department_records() -> tuple[int, int, int]:
    with SessionLocal.begin() as db:
        department = Department(code="OPS", name="Vận hành")
        db.add(department)
        db.flush()
        employee = Employee(
            employee_code="NV999",
            full_name="Nhân viên ngoài phòng",
            email="outside@example.local",
            department_id=department.id,
        )
        db.add(employee)
        db.flush()
        role = db.query(Role).filter_by(name=RoleName.EMPLOYEE).one()
        user = User(
            username="outside",
            password_hash=hash_password("OutsidePass123!"),
            role_id=role.id,
            employee_id=employee.id,
        )
        db.add(user)
        db.flush()
        shift = db.query(Shift).filter_by(code="HC").one()
        db.add(
            ShiftAssignment(
                employee_id=employee.id,
                shift_id=shift.id,
                work_date=date.today(),
            )
        )
        attendance = AttendanceRecord(
            employee_id=employee.id,
            shift_id=shift.id,
            work_date=date.today(),
            check_in_at=datetime.now(UTC),
            check_in_ip="127.0.0.1",
        )
        db.add(attendance)
        db.flush()
        adjustment = AttendanceAdjustment(
            attendance_id=attendance.id,
            requested_by=user.id,
            reason="Cần kiểm tra phạm vi dữ liệu phòng ban",
        )
        alert = SecurityAlert(
            employee_id=employee.id,
            alert_type="SCOPE_TEST",
            description="Cảnh báo thuộc phòng ban khác",
        )
        db.add_all([adjustment, alert])
        db.flush()
        return employee.id, adjustment.id, alert.id


def test_admin_dashboard_and_connected_client_details(client, admin_headers, monkeypatch):
    dashboard = client.get("/api/v1/dashboard", headers=admin_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["total_employees"] == 3

    with SessionLocal() as db:
        admin = db.query(User).filter_by(username="admin").one()
        admin_id = admin.id
        employee_id = admin.employee_id

    monkeypatch.setattr(connection_manager, "connection_counts", lambda: {admin_id: 2})
    response = client.get("/api/v1/clients", headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == [
        {
            "user_id": admin_id,
            "username": "admin",
            "role": "ADMIN",
            "employee_id": employee_id,
            "connections": 2,
        }
    ]


def test_manager_cannot_access_another_department(client, manager_headers):
    employee_id, adjustment_id, alert_id = create_other_department_records()

    employees = client.get("/api/v1/employees", headers=manager_headers)
    assert employees.status_code == 200
    assert employee_id not in {item["id"] for item in employees.json()}

    assert (
        client.get(
            "/api/v1/attendance",
            params={"employee_id": employee_id},
            headers=manager_headers,
        ).status_code
        == 403
    )
    assert (
        client.get(
            "/api/v1/shift-assignments",
            params={"employee_id": employee_id},
            headers=manager_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(f"/api/v1/random-checks/{employee_id}", headers=manager_headers).status_code
        == 403
    )
    assert (
        client.get(
            "/api/v1/reports/attendance",
            params={
                "start": str(date.today()),
                "end": str(date.today()),
                "employee_id": employee_id,
            },
            headers=manager_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/attendance/adjustments/{adjustment_id}/review",
            json={"approve": False, "note": "Ngoài phạm vi"},
            headers=manager_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/v1/security-alerts/{alert_id}/resolve",
            json={"approve": False, "note": "Ngoài phạm vi"},
            headers=manager_headers,
        ).status_code
        == 403
    )
    alerts = client.get("/api/v1/security-alerts", headers=manager_headers)
    assert alert_id not in {item["id"] for item in alerts.json()}


def test_report_includes_approved_leave_days(client, manager_headers):
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        leave_type = db.query(LeaveType).filter_by(code="AL").one()
        db.add(
            LeaveRequest(
                employee_id=employee.id,
                leave_type_id=leave_type.id,
                start_date=date.today(),
                end_date=date.today(),
                days=Decimal(1),
                reason="Nghỉ phép đã duyệt để lập báo cáo",
                status=RequestStatus.APPROVED,
            )
        )
    response = client.get(
        "/api/v1/reports/attendance",
        params={"start": str(date.today()), "end": str(date.today())},
        headers=manager_headers,
    )
    assert response.status_code == 200
    employee_row = next(row for row in response.json() if row["employee_code"] == "NV001")
    assert employee_row["leave_days"] == 1.0


def test_admin_can_list_created_backups(client, admin_headers):
    created = client.post("/api/v1/admin/backup", headers=admin_headers)
    assert created.status_code == 200, created.text
    filename = created.json()["filename"]
    listed = client.get("/api/v1/admin/backups", headers=admin_headers)
    assert listed.status_code == 200
    assert filename in {item["filename"] for item in listed.json()}
    backup_path = Path(get_settings().backup_directory) / filename
    backup_path.unlink(missing_ok=True)
