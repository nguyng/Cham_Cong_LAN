from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.entities import Employee, Role, RoleName, User


def create_initial_admin(
    db: Session,
    *,
    username: str,
    employee_code: str,
    full_name: str,
    email: str,
    password: str,
) -> User:
    if len(password) < 10:
        raise ValueError("Mật khẩu Admin phải có tối thiểu 10 ký tự")
    if db.scalar(select(User).where(User.username == username)):
        raise ValueError("Username đã tồn tại")
    if db.scalar(
        select(Employee).where(
            (Employee.employee_code == employee_code) | (Employee.email == email)
        )
    ):
        raise ValueError("Mã nhân viên hoặc email đã tồn tại")
    for role_name in RoleName:
        if not db.scalar(select(Role).where(Role.name == role_name)):
            db.add(Role(name=role_name, description=role_name.value.title()))
    db.flush()
    employee = Employee(
        employee_code=employee_code,
        full_name=full_name,
        email=email,
        active=True,
    )
    db.add(employee)
    db.flush()
    role = db.scalar(select(Role).where(Role.name == RoleName.ADMIN))
    user = User(
        username=username,
        password_hash=hash_password(password),
        role_id=role.id,
        employee_id=employee.id,
    )
    db.add(user)
    db.flush()
    return user
