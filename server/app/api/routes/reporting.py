from datetime import date
from decimal import Decimal

from fastapi import HTTPException, Query, Request
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.common import (
    audit,
    business_days,
    enforce_employee_scope,
    ensure_employee,
    now_utc,
    validate_date_range,
)
from app.api.deps import CurrentUser, Db, Manager, client_ip
from app.api.pagination import Page, paginated_rows
from app.api.routers import admin_router
from app.models.entities import (
    AttendanceRecord,
    Employee,
    LeaveRequest,
    RequestStatus,
    RoleName,
    SecurityAlert,
    User,
)
from app.schemas.api import PayrollProfileIn
from app.services import attendance
from app.services.payroll import payroll_report
from app.services.reporting import excel_report, pdf_report
from app.websocket.manager import manager


def report_rows(
    db: Session,
    start: date,
    end: date,
    department_id: int | None = None,
    employee_id: int | None = None,
) -> list[dict]:
    employee_query = select(Employee)
    if department_id:
        employee_query = employee_query.where(Employee.department_id == department_id)
    if employee_id:
        employee_query = employee_query.where(Employee.id == employee_id)
    grouped: dict[int, dict] = {}
    employees = db.scalars(employee_query.order_by(Employee.employee_code)).all()
    employee_ids = [employee.id for employee in employees]
    for employee in employees:
        grouped[employee.id] = {
            "employee_code": employee.employee_code,
            "full_name": employee.full_name,
            "work_days": 0,
            "minutes": 0,
            "late_count": 0,
            "early_count": 0,
            "leave_days": Decimal(0),
        }
    if not employee_ids:
        return []
    attendance_query = select(AttendanceRecord).where(
        AttendanceRecord.employee_id.in_(employee_ids),
        AttendanceRecord.work_date.between(start, end),
    )
    for record in db.scalars(attendance_query).all():
        row = grouped[record.employee_id]
        row["work_days"] += 1
        row["minutes"] += record.worked_minutes
        row["late_count"] += int(record.late_minutes > 0)
        row["early_count"] += int(record.early_leave_minutes > 0)
    leave_query = select(LeaveRequest).where(
        LeaveRequest.employee_id.in_(employee_ids),
        LeaveRequest.status == RequestStatus.APPROVED,
        LeaveRequest.start_date <= end,
        LeaveRequest.end_date >= start,
    )
    for leave in db.scalars(leave_query).all():
        overlap_start = max(start, leave.start_date)
        overlap_end = min(end, leave.end_date)
        grouped[leave.employee_id]["leave_days"] += business_days(overlap_start, overlap_end)
    return [
        {
            **row,
            "leave_days": float(row["leave_days"]),
            "hours": round(row.pop("minutes") / 60, 2),
        }
        for row in grouped.values()
        if row["work_days"] or row["leave_days"]
    ]


def scoped_report_filters(
    db: Session,
    reviewer: User,
    department_id: int | None,
    employee_id: int | None,
) -> tuple[int | None, int | None]:
    if reviewer.role.name == RoleName.MANAGER:
        department_id = ensure_employee(reviewer).department_id
    if employee_id:
        employee = enforce_employee_scope(db, reviewer, employee_id)
        if department_id and employee.department_id != department_id:
            raise HTTPException(403, "Nhân viên không thuộc phòng ban được chọn")
    return department_id, employee_id


@admin_router.get("/api/v1/payroll")
def payroll_summary(
    year: int,
    db: Db,
    reviewer: Manager,
    pagination: Page,
    month: int | None = Query(default=None, ge=1, le=12),
    department_id: int | None = None,
    employee_id: int | None = None,
):
    department_id, employee_id = scoped_report_filters(
        db, reviewer, department_id, employee_id
    )
    try:
        report = payroll_report(
            db,
            year=year,
            month=month,
            department_id=department_id,
            employee_id=employee_id,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if pagination.page is not None:
        items = report["items"]
        total = len(items)
        pages = max(1, (total + pagination.page_size - 1) // pagination.page_size)
        page = min(pagination.page, pages)
        start = (page - 1) * pagination.page_size
        report["items"] = items[start : start + pagination.page_size]
        report["pagination"] = {
            "page": page,
            "page_size": pagination.page_size,
            "total": total,
            "pages": pages,
        }
    return report


@admin_router.put("/api/v1/payroll/profiles/{employee_id}")
def update_payroll_profile(
    employee_id: int,
    payload: PayrollProfileIn,
    request: Request,
    db: Db,
    reviewer: Manager,
):
    employee = enforce_employee_scope(db, reviewer, employee_id)
    before = {
        "base_salary": float(employee.base_salary or 0),
        "attendance_bonus": float(employee.attendance_bonus or 0),
        "overtime_multiplier": float(employee.overtime_multiplier or Decimal("1.50")),
    }
    employee.base_salary = payload.base_salary
    employee.attendance_bonus = payload.attendance_bonus
    employee.overtime_multiplier = payload.overtime_multiplier
    after = {
        "base_salary": float(payload.base_salary),
        "attendance_bonus": float(payload.attendance_bonus),
        "overtime_multiplier": float(payload.overtime_multiplier),
    }
    audit(
        db,
        "PAYROLL_PROFILE_UPDATED",
        reviewer,
        client_ip(request),
        employee,
        before,
        after,
    )
    db.commit()
    return {"employee_id": employee.id, **after}


@admin_router.get("/api/v1/reports/attendance")
def attendance_report(
    start: date,
    end: date,
    db: Db,
    reviewer: Manager,
    pagination: Page,
    department_id: int | None = None,
    employee_id: int | None = None,
):
    validate_date_range(start, end, max_days=3_650)
    department_id, employee_id = scoped_report_filters(db, reviewer, department_id, employee_id)
    return paginated_rows(report_rows(db, start, end, department_id, employee_id), pagination)


@admin_router.get("/api/v1/reports/attendance.xlsx")
def export_excel(
    start: date,
    end: date,
    db: Db,
    reviewer: Manager,
    department_id: int | None = None,
    employee_id: int | None = None,
):
    validate_date_range(start, end, max_days=3_650)
    department_id, employee_id = scoped_report_filters(db, reviewer, department_id, employee_id)
    content = excel_report(report_rows(db, start, end, department_id, employee_id))
    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="attendance_{start}_{end}.xlsx"'},
    )


@admin_router.get("/api/v1/reports/attendance.pdf")
def export_pdf(
    start: date,
    end: date,
    db: Db,
    reviewer: Manager,
    department_id: int | None = None,
    employee_id: int | None = None,
):
    validate_date_range(start, end, max_days=3_650)
    department_id, employee_id = scoped_report_filters(db, reviewer, department_id, employee_id)
    content = pdf_report(report_rows(db, start, end, department_id, employee_id))
    return Response(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="attendance_{start}_{end}.pdf"'},
    )


@admin_router.get("/api/v1/dashboard")
def dashboard(db: Db, user: CurrentUser, mine: bool = False):
    today = attendance.local_date(now_utc())
    attendance_scope = select(AttendanceRecord.id).join(Employee)
    leave_scope = select(LeaveRequest.id).join(Employee)
    alert_scope = select(SecurityAlert.id).join(Employee)
    employee_scope = select(Employee.id).where(Employee.active.is_(True))
    if mine or user.role.name == RoleName.EMPLOYEE:
        employee_id = ensure_employee(user).id
        attendance_scope = attendance_scope.where(AttendanceRecord.employee_id == employee_id)
        leave_scope = leave_scope.where(LeaveRequest.employee_id == employee_id)
        alert_scope = alert_scope.where(SecurityAlert.employee_id == employee_id)
        employee_scope = employee_scope.where(Employee.id == employee_id)
    elif user.role.name == RoleName.MANAGER:
        department_id = ensure_employee(user).department_id
        attendance_scope = attendance_scope.where(Employee.department_id == department_id)
        leave_scope = leave_scope.where(Employee.department_id == department_id)
        alert_scope = alert_scope.where(Employee.department_id == department_id)
        employee_scope = employee_scope.where(Employee.department_id == department_id)
    present = db.scalar(
        select(func.count()).select_from(
            attendance_scope.where(
                AttendanceRecord.work_date == today,
                AttendanceRecord.check_out_at.is_(None),
            ).subquery()
        )
    )
    late = db.scalar(
        select(func.count()).select_from(
            attendance_scope.where(
                AttendanceRecord.work_date == today,
                AttendanceRecord.late_minutes > 0,
            ).subquery()
        )
    )
    pending_leave = db.scalar(
        select(func.count()).select_from(
            leave_scope.where(LeaveRequest.status == RequestStatus.PENDING).subquery()
        )
    )
    open_alerts = db.scalar(
        select(func.count()).select_from(
            alert_scope.where(SecurityAlert.status == "OPEN").subquery()
        )
    )
    return {
        "present": present,
        "late": late,
        "pending_leave": pending_leave,
        "open_alerts": open_alerts,
        "connected_clients": len(manager.connected_user_ids()),
        "total_employees": db.scalar(select(func.count()).select_from(employee_scope.subquery())),
    }
