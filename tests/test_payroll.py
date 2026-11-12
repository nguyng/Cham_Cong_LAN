from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from app.database.session import SessionLocal
from app.models.entities import (
    AttendanceRecord,
    AttendanceStatus,
    Department,
    Employee,
    LeaveRequest,
    LeaveType,
    RequestStatus,
    Shift,
    ShiftAssignment,
)


def seed_payroll_period():
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        employee.base_salary = Decimal("20000000")
        employee.attendance_bonus = Decimal("1000000")
        shift = db.query(Shift).filter_by(code="HC").one()
        db.add(
            ShiftAssignment(
                employee_id=employee.id,
                shift_id=shift.id,
                work_date=date(2024, 1, 2),
            )
        )
        db.add(
            ShiftAssignment(
                employee_id=employee.id,
                shift_id=shift.id,
                work_date=date(2024, 1, 3),
            )
        )
        db.add(
            AttendanceRecord(
                employee_id=employee.id,
                shift_id=shift.id,
                work_date=date(2024, 1, 2),
                check_in_at=datetime(2024, 1, 2, 8, tzinfo=UTC),
                check_out_at=datetime(2024, 1, 2, 17, tzinfo=UTC),
                check_in_ip="127.0.0.1",
                check_out_ip="127.0.0.1",
                status=AttendanceStatus.ON_TIME,
                worked_minutes=480,
            )
        )
        leave_type = db.query(LeaveType).filter_by(code="AL").one()
        db.add(
            LeaveRequest(
                employee_id=employee.id,
                leave_type_id=leave_type.id,
                start_date=date(2024, 1, 3),
                end_date=date(2024, 1, 3),
                days=1,
                reason="Nghỉ phép hưởng lương",
                status=RequestStatus.APPROVED,
            )
        )
        return employee.id


def test_monthly_payroll_and_attendance_bonus(client, manager_headers):
    employee_id = seed_payroll_period()

    response = client.get(
        "/api/v1/payroll",
        params={"year": 2024, "month": 1, "page": 1},
        headers=manager_headers,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    row = next(item for item in data["items"] if item["employee_id"] == employee_id)
    assert row["scheduled_days"] == 2
    assert row["work_days"] == 1
    assert row["paid_leave_days"] == 1
    assert row["absence_days"] == 0
    assert row["base_earned"] == 20_000_000
    assert row["bonus_earned"] == 1_000_000
    assert row["total_salary"] == 21_000_000
    assert row["bonus_status"] == "Đạt thưởng"
    assert data["monthly_chart"][0]["total"] == 21_000_000
    assert data["summary"]["bonus_recipients"] == 1


def test_manager_can_update_salary_only_in_department(client, manager_headers):
    employee_id = seed_payroll_period()
    updated = client.put(
        f"/api/v1/payroll/profiles/{employee_id}",
        json={"base_salary": 22_000_000, "attendance_bonus": 1_500_000},
        headers=manager_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["base_salary"] == 22_000_000

    with SessionLocal.begin() as db:
        other_department = Department(code="OPS", name="Vận hành")
        db.add(other_department)
        db.flush()
        outsider = Employee(
            employee_code="OUT001",
            full_name="Ngoài phòng ban",
            email="outside@example.local",
            department_id=other_department.id,
            base_salary=Decimal("18000000"),
        )
        db.add(outsider)
        db.flush()
        outsider_id = outsider.id

    denied = client.put(
        f"/api/v1/payroll/profiles/{outsider_id}",
        json={"base_salary": 25_000_000, "attendance_bonus": 2_000_000},
        headers=manager_headers,
    )
    assert denied.status_code == 403


def test_payroll_rejects_future_year(client, admin_headers):
    response = client.get(
        "/api/v1/payroll",
        params={"year": date.today().year + 1},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "tương lai" in response.json()["detail"]


def test_payroll_rejects_future_month_in_current_year(client, admin_headers):
    if date.today().month == 12:
        pytest.skip("Không còn tháng tương lai trong năm hiện tại")
    response = client.get(
        "/api/v1/payroll",
        params={"year": date.today().year, "month": date.today().month + 1},
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "tương lai" in response.json()["detail"]
