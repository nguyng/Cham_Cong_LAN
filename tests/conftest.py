import os
import sys
from datetime import date, time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))
os.environ["DATABASE_URL"] = "sqlite:///./test_suite.db"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-secret-key-with-at-least-32-characters"
os.environ["BACKUP_DIRECTORY"] = "test_backups"

from app.core.security import hash_password  # noqa: E402
from app.database.session import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.entities import (  # noqa: E402
    Department,
    Employee,
    LeaveBalance,
    LeaveType,
    Role,
    RoleName,
    Shift,
    ShiftAssignment,
    User,
)


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal.begin() as db:
        roles = {}
        for role_name in RoleName:
            role = Role(name=role_name, description=role_name.value)
            db.add(role)
            roles[role_name] = role
        db.flush()
        department = Department(code="IT", name="Công nghệ")
        db.add(department)
        db.flush()
        admin_employee = Employee(
            employee_code="AD001",
            full_name="Quản trị",
            email="admin@example.local",
            department_id=department.id,
        )
        manager_employee = Employee(
            employee_code="MG001",
            full_name="Quản lý",
            email="manager@example.local",
            department_id=department.id,
        )
        employee = Employee(
            employee_code="NV001",
            full_name="Nhân viên",
            email="employee@example.local",
            department_id=department.id,
        )
        db.add_all([admin_employee, manager_employee, employee])
        db.flush()
        db.add_all(
            [
                User(
                    username="admin",
                    password_hash=hash_password("AdminPass123!"),
                    role_id=roles[RoleName.ADMIN].id,
                    employee_id=admin_employee.id,
                ),
                User(
                    username="manager",
                    password_hash=hash_password("ManagerPass123!"),
                    role_id=roles[RoleName.MANAGER].id,
                    employee_id=manager_employee.id,
                ),
                User(
                    username="employee",
                    password_hash=hash_password("EmployeePass123!"),
                    role_id=roles[RoleName.EMPLOYEE].id,
                    employee_id=employee.id,
                ),
            ]
        )
        shift = Shift(
            code="HC",
            name="Hành chính",
            start_time=time(0, 0),
            end_time=time(23, 59),
            break_minutes=0,
        )
        leave_type = LeaveType(code="AL", name="Phép năm", paid=True, deduct_balance=True)
        db.add_all([shift, leave_type])
        db.flush()
        db.add(ShiftAssignment(employee_id=employee.id, shift_id=shift.id, work_date=date.today()))
        db.add(
            LeaveBalance(
                employee_id=employee.id,
                leave_type_id=leave_type.id,
                year=date.today().year,
                allocated_days=12,
                used_days=0,
            )
        )
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username="employee", password="EmployeePass123!") -> dict:
    response = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def employee_headers(client):
    token = login(client)["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def manager_headers(client):
    token = login(client, "manager", "ManagerPass123!")["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client):
    token = login(client, "admin", "AdminPass123!")["access_token"]
    return {"Authorization": f"Bearer {token}"}
