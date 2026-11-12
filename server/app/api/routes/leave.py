from decimal import Decimal

from fastapi import HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.api.common import (
    audit,
    business_days,
    business_days_by_year,
    employee_identity,
    enforce_employee_scope,
    ensure_employee,
    now_utc,
)
from app.api.deps import Admin, CurrentUser, Db, Manager, client_ip
from app.api.pagination import Page, paginated
from app.api.routers import leave_router
from app.models.entities import (
    Employee,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    Notification,
    RequestStatus,
    RoleName,
    User,
)
from app.schemas.api import LeaveBalanceIn, LeaveRequestIn, LeaveTypeIn, ReviewIn
from app.services import attendance
from app.websocket.manager import manager


@leave_router.post("/api/v1/leave-types", status_code=201)
def create_leave_type(payload: LeaveTypeIn, db: Db, admin: Admin):
    item = LeaveType(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã loại nghỉ phép đã tồn tại") from None
    db.refresh(item)
    return {"id": item.id, **payload.model_dump()}


@leave_router.get("/api/v1/leave-types")
def list_leave_types(db: Db, user: CurrentUser, pagination: Page):
    return paginated(
        db,
        select(LeaveType).where(LeaveType.active.is_(True)).order_by(LeaveType.name),
        pagination,
        lambda x: {
            "id": x.id,
            "code": x.code,
            "name": x.name,
            "paid": x.paid,
            "deduct_balance": x.deduct_balance,
            "active": x.active,
        },
    )


@leave_router.put("/api/v1/leave-types/{leave_type_id}")
def update_leave_type(leave_type_id: int, payload: LeaveTypeIn, db: Db, admin: Admin):
    item = db.get(LeaveType, leave_type_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy loại nghỉ phép")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã loại nghỉ phép đã tồn tại") from None
    return {"id": item.id, **payload.model_dump(), "active": item.active}


@leave_router.delete("/api/v1/leave-types/{leave_type_id}", status_code=204)
def deactivate_leave_type(leave_type_id: int, db: Db, admin: Admin):
    item = db.get(LeaveType, leave_type_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy loại nghỉ phép")
    item.active = False
    db.commit()
    return Response(status_code=204)


@leave_router.put("/api/v1/leave-balances")
def set_leave_balance(payload: LeaveBalanceIn, db: Db, admin: Admin):
    employee = db.get(Employee, payload.employee_id)
    if not employee or not employee.active:
        raise HTTPException(409, "Nhân viên không tồn tại hoặc đã ngừng hoạt động")
    leave_type = db.get(LeaveType, payload.leave_type_id)
    if not leave_type or not leave_type.active:
        raise HTTPException(409, "Loại nghỉ phép không tồn tại hoặc đã ngừng hoạt động")
    item = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == payload.employee_id,
            LeaveBalance.leave_type_id == payload.leave_type_id,
            LeaveBalance.year == payload.year,
        )
    )
    if item:
        if payload.allocated_days < item.used_days:
            raise HTTPException(409, "Số ngày cấp không thể nhỏ hơn số ngày đã sử dụng")
        item.allocated_days = payload.allocated_days
    else:
        item = LeaveBalance(**payload.model_dump())
        db.add(item)
    db.commit()
    return {
        "employee_id": item.employee_id,
        "allocated_days": item.allocated_days,
        "used_days": item.used_days,
    }


@leave_router.get("/api/v1/leave-balances")
def list_leave_balances(
    db: Db,
    reviewer: Manager,
    pagination: Page,
    employee_id: int | None = None,
    year: int | None = None,
):
    query = select(LeaveBalance).join(Employee)
    if reviewer.role.name == RoleName.MANAGER:
        query = query.where(Employee.department_id == ensure_employee(reviewer).department_id)
    if employee_id:
        enforce_employee_scope(db, reviewer, employee_id)
        query = query.where(LeaveBalance.employee_id == employee_id)
    if year:
        query = query.where(LeaveBalance.year == year)
    return paginated(
        db,
        query.order_by(Employee.employee_code, LeaveBalance.year.desc()),
        pagination,
        lambda item: {
            "id": item.id,
            "employee_id": item.employee_id,
            **employee_identity(db, item.employee_id),
            "leave_type_id": item.leave_type_id,
            "leave_type_name": db.get(LeaveType, item.leave_type_id).name,
            "year": item.year,
            "allocated_days": float(item.allocated_days),
            "used_days": float(item.used_days),
            "remaining_days": float(item.allocated_days - item.used_days),
        },
    )


@leave_router.post("/api/v1/leaves", status_code=201)
async def create_leave(payload: LeaveRequestIn, db: Db, user: CurrentUser):
    employee = ensure_employee(user)
    leave_type = db.get(LeaveType, payload.leave_type_id)
    if not leave_type or not leave_type.active:
        raise HTTPException(409, "Loại nghỉ phép không tồn tại hoặc đã ngừng hoạt động")
    days = business_days(payload.start_date, payload.end_date)
    if days <= 0:
        raise HTTPException(400, "Khoảng nghỉ không có ngày làm việc")
    overlapping = db.scalar(
        select(func.count(LeaveRequest.id)).where(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_([RequestStatus.PENDING, RequestStatus.APPROVED]),
            LeaveRequest.start_date <= payload.end_date,
            LeaveRequest.end_date >= payload.start_date,
        )
    )
    if overlapping:
        raise HTTPException(409, "Đã có đơn nghỉ trùng thời gian")
    item = LeaveRequest(**payload.model_dump(), employee_id=employee.id, days=days)
    db.add(item)
    db.commit()
    db.refresh(item)
    await manager.broadcast({"type": "leave_requested"})
    return {"id": item.id, "days": item.days, "status": item.status.value}


@leave_router.get("/api/v1/leaves")
def list_leaves(
    db: Db,
    user: CurrentUser,
    pagination: Page,
    status: RequestStatus | None = None,
    mine: bool = False,
):
    query = select(LeaveRequest)
    if mine:
        query = query.where(LeaveRequest.employee_id == ensure_employee(user).id)
    elif user.role.name == RoleName.EMPLOYEE:
        query = query.where(LeaveRequest.employee_id == user.employee_id)
    elif user.role.name == RoleName.MANAGER:
        query = query.join(Employee).where(
            Employee.department_id == ensure_employee(user).department_id
        )
    if status:
        query = query.where(LeaveRequest.status == status)
    return paginated(
        db,
        query.order_by(LeaveRequest.created_at.desc()),
        pagination,
        lambda x: {
            "id": x.id,
            "employee_id": x.employee_id,
            **employee_identity(db, x.employee_id),
            "leave_type_id": x.leave_type_id,
            "leave_type_name": db.get(LeaveType, x.leave_type_id).name,
            "start_date": x.start_date,
            "end_date": x.end_date,
            "days": x.days,
            "reason": x.reason,
            "status": x.status.value,
            "review_note": x.review_note,
        },
    )


@leave_router.post("/api/v1/leaves/{leave_id}/cancel")
async def cancel_leave(
    leave_id: int,
    request: Request,
    db: Db,
    user: CurrentUser,
):
    item = db.get(LeaveRequest, leave_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy đơn nghỉ phép")
    employee = ensure_employee(user)
    if item.employee_id != employee.id:
        raise HTTPException(403, "Chỉ nhân viên tạo đơn mới được hủy đơn nghỉ phép")
    if item.status not in (RequestStatus.PENDING, RequestStatus.APPROVED):
        raise HTTPException(409, "Chỉ có thể hủy đơn đang chờ hoặc đã duyệt")
    if item.status == RequestStatus.APPROVED:
        if item.start_date <= attendance.local_date(now_utc()):
            raise HTTPException(409, "Không thể hủy đơn đã bắt đầu")
        leave_type = db.get(LeaveType, item.leave_type_id)
        if leave_type and leave_type.deduct_balance:
            for year, used_days in business_days_by_year(
                item.start_date, item.end_date
            ).items():
                balance = db.scalar(
                    select(LeaveBalance).where(
                        LeaveBalance.employee_id == item.employee_id,
                        LeaveBalance.leave_type_id == item.leave_type_id,
                        LeaveBalance.year == year,
                    )
                )
                if balance:
                    balance.used_days = max(Decimal(0), balance.used_days - used_days)
    previous_status = item.status.value
    item.status = RequestStatus.CANCELLED
    item.reviewed_by = user.id
    item.review_note = "Đơn nghỉ phép đã được hủy"
    item.reviewed_at = now_utc()
    audit(
        db,
        "LEAVE_CANCELLED",
        user,
        client_ip(request),
        item,
        before={"status": previous_status},
        after={"status": RequestStatus.CANCELLED.value},
    )
    db.commit()
    await manager.broadcast({"type": "leave_cancelled"})
    return {"id": item.id, "status": item.status.value}


@leave_router.post("/api/v1/leaves/{leave_id}/review")
async def review_leave(leave_id: int, payload: ReviewIn, db: Db, reviewer: Manager):
    item = db.get(LeaveRequest, leave_id)
    if not item or item.status != RequestStatus.PENDING:
        raise HTTPException(409, "Đơn không tồn tại hoặc đã xử lý")
    if reviewer.role.name == RoleName.MANAGER:
        employee = db.get(Employee, item.employee_id)
        if employee.department_id != ensure_employee(reviewer).department_id:
            raise HTTPException(403, "Ngoài phạm vi phòng ban")
    if payload.approve:
        leave_type = db.get(LeaveType, item.leave_type_id)
        if leave_type.deduct_balance:
            balances: list[tuple[LeaveBalance, Decimal]] = []
            for year, required_days in business_days_by_year(
                item.start_date, item.end_date
            ).items():
                balance = db.scalar(
                    select(LeaveBalance)
                    .where(
                        LeaveBalance.employee_id == item.employee_id,
                        LeaveBalance.leave_type_id == item.leave_type_id,
                        LeaveBalance.year == year,
                    )
                    .with_for_update()
                )
                if not balance or balance.allocated_days - balance.used_days < required_days:
                    raise HTTPException(409, f"Số ngày phép còn lại của năm {year} không đủ")
                balances.append((balance, required_days))
            for balance, required_days in balances:
                balance.used_days += required_days
        item.status = RequestStatus.APPROVED
    else:
        item.status = RequestStatus.REJECTED
    item.reviewed_by = reviewer.id
    item.review_note = payload.note
    item.reviewed_at = now_utc()
    employee_user = db.scalar(select(User).where(User.employee_id == item.employee_id))
    if employee_user:
        db.add(
            Notification(
                user_id=employee_user.id,
                title="Kết quả đơn nghỉ phép",
                message=f"Đơn #{item.id}: {item.status.value}. {payload.note}",
                category="LEAVE",
            )
        )
    db.commit()
    if employee_user:
        await manager.send_user(
            employee_user.id,
            {"type": "leave_reviewed", "leave_id": item.id, "status": item.status.value},
        )
    return {"id": item.id, "status": item.status.value}
