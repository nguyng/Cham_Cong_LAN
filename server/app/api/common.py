from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import (
    AttendanceRecord,
    AuditLog,
    Employee,
    Role,
    RoleName,
    User,
)


def now_utc() -> datetime:
    return datetime.now(UTC)


def audit(db: Session, action: str, user: User | None, ip: str | None, entity=None, before=None, after=None):
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            action=action,
            entity_type=entity.__class__.__name__ if entity else None,
            entity_id=str(getattr(entity, "id", getattr(entity, "key", ""))) if entity else None,
            client_ip=ip,
            before_data=before,
            after_data=after,
        )
    )


def employee_dict(item: Employee) -> dict:
    return {
        "id": item.id,
        "employee_code": item.employee_code,
        "full_name": item.full_name,
        "email": item.email,
        "phone": item.phone,
        "department_id": item.department_id,
        "department_name": item.department.name if item.department else None,
        "position_id": item.position_id,
        "position_name": item.position.name if item.position else None,
        "hire_date": item.hire_date,
        "active": item.active,
    }


def attendance_dict(item: AttendanceRecord) -> dict:
    return {
        "id": item.id,
        "employee_id": item.employee_id,
        "employee_code": item.employee.employee_code if item.employee else None,
        "full_name": item.employee.full_name if item.employee else None,
        "shift_id": item.shift_id,
        "work_date": item.work_date,
        "check_in_at": item.check_in_at,
        "check_in_ip": item.check_in_ip,
        "check_in_location_source": (
            "GPS" if item.check_in_latitude is not None else "LAN_IP_FALLBACK"
        ),
        "check_out_at": item.check_out_at,
        "check_out_ip": item.check_out_ip,
        "check_out_location_source": (
            None
            if item.check_out_at is None
            else "GPS"
            if item.check_out_latitude is not None
            else "LAN_IP_FALLBACK"
        ),
        "check_in_latitude": item.check_in_latitude,
        "check_in_longitude": item.check_in_longitude,
        "check_in_accuracy_meters": item.check_in_accuracy_meters,
        "check_in_geofence_distance_meters": item.check_in_geofence_distance_meters,
        "check_out_latitude": item.check_out_latitude,
        "check_out_longitude": item.check_out_longitude,
        "check_out_accuracy_meters": item.check_out_accuracy_meters,
        "check_out_geofence_distance_meters": item.check_out_geofence_distance_meters,
        "status": item.status.value,
        "late_minutes": item.late_minutes,
        "early_leave_minutes": item.early_leave_minutes,
        "worked_minutes": item.worked_minutes,
        "overtime_minutes": item.overtime_minutes,
        "approved_overtime_minutes": item.approved_overtime_minutes,
        "overtime_status": item.overtime_status,
        "overtime_review_note": item.overtime_review_note,
        "overtime_reviewed_at": item.overtime_reviewed_at,
        "suspicious": item.suspicious,
    }


def employee_identity(db: Session, employee_id: int | None) -> dict:
    employee = db.get(Employee, employee_id) if employee_id else None
    return {
        "employee_code": employee.employee_code if employee else None,
        "full_name": employee.full_name if employee else None,
    }


def attendance_identity(db: Session, attendance_id: int) -> dict:
    record = db.get(AttendanceRecord, attendance_id)
    return {
        **employee_identity(db, record.employee_id if record else None),
        "work_date": record.work_date if record else None,
    }


def ensure_employee(user: User) -> Employee:
    if not user.employee:
        raise HTTPException(409, "Tài khoản chưa liên kết hồ sơ nhân viên")
    return user.employee


def protect_admin_continuity(db: Session, target: User, actor: User):
    """Prevent account changes that could remove the last usable Admin."""
    if not target.active or target.role.name != RoleName.ADMIN:
        return
    if target.id == actor.id:
        raise HTTPException(409, "Không thể vô hiệu hóa Admin đang đăng nhập")
    active_admins = db.scalar(
        select(func.count(User.id))
        .join(Role)
        .where(User.active.is_(True), Role.name == RoleName.ADMIN)
    )
    if active_admins <= 1:
        raise HTTPException(409, "Hệ thống phải còn ít nhất một Admin hoạt động")


def enforce_employee_scope(db: Session, user: User, employee_id: int) -> Employee:
    """Enforce the row-level scope used by every Manager-facing endpoint."""
    employee = db.get(Employee, employee_id)
    if not employee:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    if (
        user.role.name == RoleName.MANAGER
        and employee.department_id != ensure_employee(user).department_id
    ):
        raise HTTPException(403, "Ngoài phạm vi phòng ban")
    if user.role.name == RoleName.EMPLOYEE and employee.id != user.employee_id:
        raise HTTPException(403, "Không được truy cập dữ liệu của nhân viên khác")
    return employee


def business_days(start: date, end: date) -> Decimal:
    days = sum(
        1
        for offset in range((end - start).days + 1)
        if (start + timedelta(days=offset)).weekday() < 5
    )
    return Decimal(days)


def business_days_by_year(start: date, end: date) -> dict[int, Decimal]:
    """Split working days by calendar year for yearly leave balances."""
    result: dict[int, Decimal] = {}
    for offset in range((end - start).days + 1):
        current = start + timedelta(days=offset)
        if current.weekday() < 5:
            result[current.year] = result.get(current.year, Decimal(0)) + Decimal(1)
    return result


def validate_date_range(
    start: date | None, end: date | None, *, max_days: int | None = None
):
    if start is not None and end is not None and end < start:
        raise HTTPException(400, "Ngày kết thúc phải từ ngày bắt đầu trở đi")
    if (
        max_days is not None
        and start is not None
        and end is not None
        and (end - start).days > max_days
    ):
        raise HTTPException(400, f"Khoảng thời gian chỉ được tối đa {max_days + 1} ngày")
