import secrets
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import jwt
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import Admin, CurrentUser, Db, Manager, client_ip, require_lan
from app.api.pagination import Page, paginated, paginated_rows
from app.api.routers import (
    ALL_ROUTERS,
    admin_router,
    attendance_router,
    auth_router,
    leave_router,
    organization_router,
    security_router,
    system_router,
)
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    hash_token,
    new_session_id,
    verify_password,
)
from app.database.session import SessionLocal
from app.models.entities import (
    AttendanceAdjustment,
    AttendanceRecord,
    AuditLog,
    Department,
    Device,
    Employee,
    IdempotencyRecord,
    LeaveBalance,
    LeaveRequest,
    LeaveType,
    LoginSession,
    Notification,
    Position,
    RandomCheck,
    RequestStatus,
    Role,
    RoleName,
    SecurityAlert,
    Shift,
    ShiftAssignment,
    SystemSetting,
    User,
)
from app.schemas.api import (
    AdjustmentIn,
    AssignmentIn,
    AttendanceAction,
    DepartmentIn,
    DeviceIn,
    EmployeeIn,
    EmployeeUpdate,
    LeaveBalanceIn,
    LeaveRequestIn,
    LeaveTypeIn,
    LoginRequest,
    PasswordChange,
    PositionIn,
    RandomCheckResponse,
    ReviewIn,
    SettingIn,
    ShiftIn,
    TokenResponse,
)
from app.services import attendance
from app.services.backup import backup_database, restore_database
from app.services.discovery import discovery_server
from app.services.maintenance import cleanup_expired_records
from app.services.reporting import excel_report, pdf_report
from app.websocket.manager import manager

settings = get_settings()


def now_utc() -> datetime:
    return datetime.now(UTC)


def audit(
    db: Session,
    action: str,
    user: User | None,
    ip: str | None,
    entity=None,
    before=None,
    after=None,
):
    db.add(
        AuditLog(
            user_id=user.id if user else None,
            action=action,
            entity_type=entity.__class__.__name__ if entity else None,
            entity_id=str(getattr(entity, "id", "")) if entity else None,
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
        "check_out_at": item.check_out_at,
        "status": item.status.value,
        "late_minutes": item.late_minutes,
        "early_leave_minutes": item.early_leave_minutes,
        "worked_minutes": item.worked_minutes,
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


async def expire_random_checks():
    with SessionLocal() as db:
        checks = db.scalars(
            select(RandomCheck).where(
                RandomCheck.result == "PENDING", RandomCheck.expires_at < now_utc()
            )
        ).all()
        for check in checks:
            check.result = "UNVERIFIED"
            db.add(
                SecurityAlert(
                    employee_id=check.employee_id,
                    alert_type="RANDOM_CHECK_MISSED",
                    description="Nhân viên không phản hồi Random Check đúng hạn; cần Manager xem xét",
                    evidence={"random_check_id": check.id},
                )
            )
        db.commit()
        if checks:
            await manager.broadcast({"type": "security_alerts_updated", "count": len(checks)})


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler(timezone="UTC")
    if settings.environment != "test":
        discovery_server.start()
        scheduler.add_job(
            expire_random_checks,
            "interval",
            seconds=30,
            id="expire-random-checks",
            replace_existing=True,
        )
        scheduler.add_job(
            run_scheduled_random_check,
            "interval",
            minutes=settings.random_check_interval_minutes,
            jitter=max(1, settings.random_check_interval_minutes * 30),
            id="issue-random-check",
            replace_existing=True,
        )
        scheduler.add_job(
            cleanup_expired_records,
            "interval",
            hours=settings.cleanup_interval_hours,
            id="cleanup-expired-records",
            replace_existing=True,
        )
        cleanup_expired_records()
        scheduler.start()
    try:
        yield
    finally:
        if settings.environment != "test":
            scheduler.shutdown(wait=False)
            discovery_server.stop()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=bool(settings.cors_origins),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)


@system_router.get("/api/v1/health")
def health(db: Db):
    db.execute(select(1))
    return {"status": "ok", "server_time": now_utc(), "version": app.version}


@auth_router.post("/api/v1/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Db):
    ip = client_ip(request)
    user = db.scalar(select(User).where(User.username == payload.username))
    now = now_utc()
    locked = user and user.locked_until and user.locked_until.replace(tzinfo=UTC) > now
    if locked:
        audit(db, "LOGIN_LOCKED", user, ip)
        db.commit()
        raise HTTPException(423, "Tài khoản đang bị khóa tạm thời")
    if not user or not user.active or not verify_password(payload.password, user.password_hash):
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.locked_until = now + timedelta(minutes=15)
                user.failed_login_count = 0
        audit(db, "LOGIN_FAILED", user, ip, after={"username": payload.username})
        db.commit()
        raise HTTPException(401, "Tên đăng nhập hoặc mật khẩu không đúng")
    user.failed_login_count = 0
    user.locked_until = None
    session_id = new_session_id()
    token, expires_at = create_access_token(user.id, user.role.name.value, session_id)
    active_sessions = db.scalar(
        select(func.count(LoginSession.id)).where(
            LoginSession.user_id == user.id,
            LoginSession.revoked_at.is_(None),
            LoginSession.expires_at > now,
        )
    )
    if active_sessions:
        db.add(
            SecurityAlert(
                employee_id=user.employee_id,
                alert_type="CONCURRENT_LOGIN",
                description="Phát hiện nhiều phiên đăng nhập đồng thời; cần kiểm tra trước khi kết luận",
                evidence={"ip": ip, "active_sessions": active_sessions},
            )
        )
    db.add(
        LoginSession(
            id=session_id,
            user_id=user.id,
            token_hash=hash_token(token),
            client_ip=ip,
            device_fingerprint=payload.device_fingerprint,
            expires_at=expires_at,
            last_seen_at=now,
        )
    )
    audit(db, "LOGIN_SUCCESS", user, ip)
    db.commit()
    return TokenResponse(
        access_token=token,
        expires_at=expires_at,
        role=user.role.name.value,
        user_id=user.id,
        employee_id=user.employee_id,
    )


@auth_router.post("/api/v1/auth/logout", status_code=204)
def logout(request: Request, db: Db, user: CurrentUser):
    token = request.headers["authorization"][7:]
    session_id = decode_token(token)["sid"]
    session = db.get(LoginSession, session_id)
    session.revoked_at = now_utc()
    audit(db, "LOGOUT", user, client_ip(request))
    db.commit()
    return Response(status_code=204)


@auth_router.post("/api/v1/auth/change-password", status_code=204)
def change_password(payload: PasswordChange, request: Request, db: Db, user: CurrentUser):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(400, "Mật khẩu hiện tại không đúng")
    user.password_hash = hash_password(payload.new_password)
    user.password_changed_at = now_utc()
    db.query(LoginSession).filter(
        LoginSession.user_id == user.id, LoginSession.revoked_at.is_(None)
    ).update({LoginSession.revoked_at: now_utc()})
    audit(db, "PASSWORD_CHANGED", user, client_ip(request))
    db.commit()
    return Response(status_code=204)


@auth_router.get("/api/v1/me")
def me(user: CurrentUser):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role.name.value,
        "employee": employee_dict(user.employee) if user.employee else None,
    }


@auth_router.get("/api/v1/users")
def list_users(db: Db, admin: Admin, pagination: Page):
    return paginated(
        db,
        select(User).order_by(User.username),
        pagination,
        lambda x: {
            "id": x.id,
            "username": x.username,
            "role": x.role.name.value,
            "employee_id": x.employee_id,
            "active": x.active,
            "locked_until": x.locked_until,
        },
    )


@auth_router.patch("/api/v1/users/{user_id}/role")
def change_user_role(user_id: int, role: RoleName, request: Request, db: Db, admin: Admin):
    item = db.get(User, user_id)
    target_role = db.scalar(select(Role).where(Role.name == role))
    if not item or not target_role:
        raise HTTPException(404, "Không tìm thấy tài khoản hoặc vai trò")
    before = {"role": item.role.name.value}
    item.role_id = target_role.id
    audit(db, "USER_ROLE_CHANGED", admin, client_ip(request), item, before, {"role": role.value})
    db.commit()
    return {"id": item.id, "role": role.value}


@auth_router.post("/api/v1/users/{user_id}/unlock", status_code=204)
def unlock_user(user_id: int, db: Db, admin: Admin):
    item = db.get(User, user_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    item.failed_login_count = 0
    item.locked_until = None
    db.commit()
    return Response(status_code=204)


@organization_router.post("/api/v1/departments", status_code=201)
def create_department(payload: DepartmentIn, request: Request, db: Db, admin: Admin):
    item = Department(**payload.model_dump())
    db.add(item)
    audit(
        db,
        "DEPARTMENT_CREATED",
        admin,
        client_ip(request),
        item,
        after=payload.model_dump(mode="json"),
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã hoặc tên phòng ban đã tồn tại") from None
    db.refresh(item)
    return {"id": item.id, **payload.model_dump()}


@organization_router.get("/api/v1/departments")
def list_departments(db: Db, user: CurrentUser, pagination: Page):
    return paginated(
        db,
        select(Department).order_by(Department.name),
        pagination,
        lambda item: {
            "id": item.id,
            "code": item.code,
            "name": item.name,
            "manager_employee_id": item.manager_employee_id,
            "manager_name": employee_identity(db, item.manager_employee_id)["full_name"],
            "active": item.active,
        },
    )


@organization_router.put("/api/v1/departments/{department_id}")
def update_department(
    department_id: int, payload: DepartmentIn, request: Request, db: Db, admin: Admin
):
    item = db.get(Department, department_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy phòng ban")
    before = {"code": item.code, "name": item.name, "manager_employee_id": item.manager_employee_id}
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    audit(
        db,
        "DEPARTMENT_UPDATED",
        admin,
        client_ip(request),
        item,
        before,
        payload.model_dump(mode="json"),
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã hoặc tên phòng ban đã tồn tại") from None
    return {"id": item.id, **payload.model_dump(), "active": item.active}


@organization_router.delete("/api/v1/departments/{department_id}", status_code=204)
def deactivate_department(department_id: int, db: Db, admin: Admin):
    item = db.get(Department, department_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy phòng ban")
    item.active = False
    db.commit()
    return Response(status_code=204)


@organization_router.post("/api/v1/positions", status_code=201)
def create_position(payload: PositionIn, db: Db, admin: Admin):
    item = Position(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Chức vụ đã tồn tại") from None
    db.refresh(item)
    return {"id": item.id, **payload.model_dump()}


@organization_router.get("/api/v1/positions")
def list_positions(db: Db, user: CurrentUser, pagination: Page):
    return paginated(
        db,
        select(Position).order_by(Position.name),
        pagination,
        lambda x: {"id": x.id, "code": x.code, "name": x.name, "active": x.active},
    )


@organization_router.put("/api/v1/positions/{position_id}")
def update_position(position_id: int, payload: PositionIn, db: Db, admin: Admin):
    item = db.get(Position, position_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy chức vụ")
    item.code, item.name = payload.code, payload.name
    db.commit()
    return {"id": item.id, "code": item.code, "name": item.name, "active": item.active}


@organization_router.delete("/api/v1/positions/{position_id}", status_code=204)
def deactivate_position(position_id: int, db: Db, admin: Admin):
    item = db.get(Position, position_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy chức vụ")
    item.active = False
    db.commit()
    return Response(status_code=204)


@organization_router.post("/api/v1/employees", status_code=201)
def create_employee(payload: EmployeeIn, request: Request, db: Db, admin: Admin):
    role = db.scalar(select(Role).where(Role.name == RoleName(payload.role)))
    if not role:
        raise HTTPException(409, "Chưa khởi tạo vai trò hệ thống")
    employee_data = payload.model_dump(exclude={"username", "temporary_password", "role"})
    item = Employee(**employee_data)
    db.add(item)
    db.flush()
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.temporary_password),
        role_id=role.id,
        employee_id=item.id,
    )
    db.add(user)
    audit(db, "EMPLOYEE_CREATED", admin, client_ip(request), item, after=employee_data)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã nhân viên, email hoặc username đã tồn tại") from None
    db.refresh(item)
    return employee_dict(item)


@organization_router.get("/api/v1/employees")
def list_employees(
    db: Db,
    user: CurrentUser,
    pagination: Page,
    search: str | None = None,
    department_id: int | None = None,
    active: bool | None = None,
):
    query = select(Employee)
    if user.role.name == RoleName.EMPLOYEE:
        query = query.where(Employee.id == user.employee_id)
    elif user.role.name == RoleName.MANAGER:
        query = query.where(Employee.department_id == ensure_employee(user).department_id)
    if search:
        query = query.where(
            or_(
                Employee.full_name.contains(search),
                Employee.employee_code.contains(search),
                Employee.email.contains(search),
            )
        )
    if department_id:
        query = query.where(Employee.department_id == department_id)
    if active is not None:
        query = query.where(Employee.active == active)
    return paginated(db, query.order_by(Employee.full_name), pagination, employee_dict)


@organization_router.put("/api/v1/employees/{employee_id}")
def update_employee(
    employee_id: int, payload: EmployeeUpdate, request: Request, db: Db, admin: Admin
):
    item = db.get(Employee, employee_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    before = employee_dict(item)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    audit(
        db,
        "EMPLOYEE_UPDATED",
        admin,
        client_ip(request),
        item,
        before,
        payload.model_dump(mode="json"),
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email đã thuộc nhân viên khác") from None
    return employee_dict(item)


@organization_router.patch("/api/v1/employees/{employee_id}/active")
def set_employee_active(employee_id: int, active: bool, request: Request, db: Db, admin: Admin):
    item = db.get(Employee, employee_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy nhân viên")
    before = {"active": item.active}
    item.active = active
    if user := db.scalar(select(User).where(User.employee_id == item.id)):
        user.active = active
    audit(
        db, "EMPLOYEE_STATUS_CHANGED", admin, client_ip(request), item, before, {"active": active}
    )
    db.commit()
    return employee_dict(item)


@organization_router.post("/api/v1/shifts", status_code=201)
def create_shift(payload: ShiftIn, db: Db, admin: Admin):
    item = Shift(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã ca đã tồn tại") from None
    db.refresh(item)
    return {"id": item.id, **payload.model_dump()}


@organization_router.get("/api/v1/shifts")
def list_shifts(db: Db, user: CurrentUser, pagination: Page):
    return paginated(
        db,
        select(Shift).order_by(Shift.name),
        pagination,
        lambda x: {
            "id": x.id,
            "code": x.code,
            "name": x.name,
            "start_time": x.start_time,
            "end_time": x.end_time,
            "break_minutes": x.break_minutes,
            "late_grace_minutes": x.late_grace_minutes,
            "early_grace_minutes": x.early_grace_minutes,
            "active": x.active,
        },
    )


@organization_router.put("/api/v1/shifts/{shift_id}")
def update_shift(shift_id: int, payload: ShiftIn, db: Db, admin: Admin):
    item = db.get(Shift, shift_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy ca làm")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.commit()
    return {"id": item.id, **payload.model_dump(), "active": item.active}


@organization_router.delete("/api/v1/shifts/{shift_id}", status_code=204)
def deactivate_shift(shift_id: int, db: Db, admin: Admin):
    item = db.get(Shift, shift_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy ca làm")
    item.active = False
    db.commit()
    return Response(status_code=204)


@organization_router.post("/api/v1/shift-assignments", status_code=201)
def assign_shift(payload: AssignmentIn, db: Db, manager_user: Manager):
    if manager_user.role.name == RoleName.MANAGER:
        employee = db.get(Employee, payload.employee_id)
        if not employee or employee.department_id != ensure_employee(manager_user).department_id:
            raise HTTPException(403, "Ngoài phạm vi phòng ban")
    results = []
    for offset in range((payload.end_date - payload.start_date).days + 1):
        work_date = payload.start_date + timedelta(days=offset)
        if work_date.weekday() not in payload.weekdays:
            continue
        existing = db.scalar(
            select(ShiftAssignment).where(
                ShiftAssignment.employee_id == payload.employee_id,
                ShiftAssignment.work_date == work_date,
            )
        )
        if existing:
            existing.shift_id = payload.shift_id
            item = existing
        else:
            item = ShiftAssignment(
                employee_id=payload.employee_id, shift_id=payload.shift_id, work_date=work_date
            )
            db.add(item)
        results.append(work_date)
    db.commit()
    return {"assigned_dates": results, "count": len(results)}


@organization_router.get("/api/v1/shift-assignments")
def list_assignments(
    db: Db,
    user: CurrentUser,
    pagination: Page,
    employee_id: int | None = None,
    start: date | None = None,
    end: date | None = None,
):
    query = select(ShiftAssignment)
    if user.role.name == RoleName.EMPLOYEE:
        target = employee_id or ensure_employee(user).id
        enforce_employee_scope(db, user, target)
        query = query.where(ShiftAssignment.employee_id == target)
    elif user.role.name == RoleName.MANAGER:
        query = query.join(Employee).where(
            Employee.department_id == ensure_employee(user).department_id
        )
        if employee_id:
            enforce_employee_scope(db, user, employee_id)
            query = query.where(ShiftAssignment.employee_id == employee_id)
    elif employee_id:
        enforce_employee_scope(db, user, employee_id)
        query = query.where(ShiftAssignment.employee_id == employee_id)
    if start:
        query = query.where(ShiftAssignment.work_date >= start)
    if end:
        query = query.where(ShiftAssignment.work_date <= end)
    return paginated(
        db,
        query.order_by(ShiftAssignment.work_date.desc()),
        pagination,
        lambda x: {
            "id": x.id,
            "employee_id": x.employee_id,
            "employee_code": x.employee.employee_code,
            "full_name": x.employee.full_name,
            "shift_id": x.shift_id,
            "shift_name": x.shift.name,
            "work_date": x.work_date,
        },
    )


def approved_device(
    db: Session, employee_id: int, fingerprint: str | None, ip: str
) -> Device | None:
    if not fingerprint:
        return None
    digest = hash_token(fingerprint)
    device = db.scalar(
        select(Device).where(
            Device.employee_id == employee_id,
            Device.fingerprint_hash == digest,
            Device.active.is_(True),
        )
    )
    if not device or not device.approved:
        raise HTTPException(403, "Thiết bị chưa được quản trị viên phê duyệt")
    device.last_ip = ip
    device.last_seen_at = now_utc()
    return device


@organization_router.post("/api/v1/devices", status_code=201)
def register_device(payload: DeviceIn, request: Request, db: Db, user: CurrentUser):
    employee = ensure_employee(user)
    item = Device(
        employee_id=employee.id,
        fingerprint_hash=hash_token(payload.fingerprint),
        device_name=payload.device_name,
        last_ip=client_ip(request),
        last_seen_at=now_utc(),
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Thiết bị đã được đăng ký") from None
    db.refresh(item)
    return {"id": item.id, "approved": item.approved}


@organization_router.patch("/api/v1/devices/{device_id}/approve")
def approve_device(device_id: int, approved: bool, db: Db, admin: Admin):
    item = db.get(Device, device_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy thiết bị")
    item.approved = approved
    db.commit()
    return {"id": item.id, "approved": item.approved}


@organization_router.get("/api/v1/devices")
def list_devices(db: Db, reviewer: Manager, pagination: Page):
    query = select(Device)
    if reviewer.role.name == RoleName.MANAGER:
        query = query.join(Employee).where(
            Employee.department_id == ensure_employee(reviewer).department_id
        )
    return paginated(
        db,
        query.order_by(Device.created_at.desc()),
        pagination,
        lambda x: {
            "id": x.id,
            "employee_id": x.employee_id,
            **employee_identity(db, x.employee_id),
            "device_name": x.device_name,
            "approved": x.approved,
            "active": x.active,
            "last_ip": x.last_ip,
            "last_seen_at": x.last_seen_at,
        },
    )


@organization_router.get("/api/v1/devices/me")
def my_devices(db: Db, user: CurrentUser, pagination: Page):
    employee = ensure_employee(user)
    return paginated(
        db,
        select(Device).where(Device.employee_id == employee.id).order_by(Device.created_at.desc()),
        pagination,
        lambda x: {
            "id": x.id,
            "device_name": x.device_name,
            "approved": x.approved,
            "active": x.active,
            "last_ip": x.last_ip,
            "last_seen_at": x.last_seen_at,
        },
    )


def attendance_action(
    operation: str, payload: AttendanceAction, request: Request, db: Session, user: User
):
    ip = client_ip(request)
    require_lan(ip)
    prior = db.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.user_id == user.id,
            IdempotencyRecord.operation == operation,
            IdempotencyRecord.request_key == payload.idempotency_key,
        )
    )
    if prior:
        return prior.response_data
    employee = ensure_employee(user)
    device = approved_device(db, employee.id, payload.device_fingerprint, ip)
    record = (
        attendance.check_in(db, employee, ip, device.id if device else None)
        if operation == "CHECK_IN"
        else attendance.check_out(db, employee, ip)
    )
    result = jsonable_encoder(attendance_dict(record))
    db.add(
        IdempotencyRecord(
            user_id=user.id,
            operation=operation,
            request_key=payload.idempotency_key,
            response_data=result,
        )
    )
    audit(db, operation, user, ip, record, after=result)
    db.commit()
    return result


@attendance_router.post("/api/v1/attendance/check-in", status_code=201)
async def check_in(payload: AttendanceAction, request: Request, db: Db, user: CurrentUser):
    result = attendance_action("CHECK_IN", payload, request, db, user)
    await manager.broadcast({"type": "attendance_changed", "data": result})
    return result


@attendance_router.post("/api/v1/attendance/check-out")
async def check_out(payload: AttendanceAction, request: Request, db: Db, user: CurrentUser):
    result = attendance_action("CHECK_OUT", payload, request, db, user)
    await manager.broadcast({"type": "attendance_changed", "data": result})
    return result


@attendance_router.get("/api/v1/attendance")
def list_attendance(
    db: Db,
    user: CurrentUser,
    pagination: Page,
    employee_id: int | None = None,
    start: date | None = None,
    end: date | None = None,
):
    query = select(AttendanceRecord)
    if user.role.name == RoleName.EMPLOYEE:
        target = employee_id or ensure_employee(user).id
        enforce_employee_scope(db, user, target)
        query = query.where(AttendanceRecord.employee_id == target)
    elif user.role.name == RoleName.MANAGER:
        query = query.join(Employee).where(
            Employee.department_id == ensure_employee(user).department_id
        )
        if employee_id:
            enforce_employee_scope(db, user, employee_id)
            query = query.where(AttendanceRecord.employee_id == employee_id)
    elif employee_id:
        enforce_employee_scope(db, user, employee_id)
        query = query.where(AttendanceRecord.employee_id == employee_id)
    if start:
        query = query.where(AttendanceRecord.work_date >= start)
    if end:
        query = query.where(AttendanceRecord.work_date <= end)
    return paginated(
        db, query.order_by(AttendanceRecord.work_date.desc()), pagination, attendance_dict
    )


@attendance_router.get("/api/v1/attendance/adjustments")
def list_adjustments(
    db: Db, user: CurrentUser, pagination: Page, status: RequestStatus | None = None
):
    query = select(AttendanceAdjustment)
    if user.role.name == RoleName.EMPLOYEE:
        query = query.where(AttendanceAdjustment.requested_by == user.id)
    elif user.role.name == RoleName.MANAGER:
        query = (
            query.join(AttendanceRecord, AttendanceAdjustment.attendance_id == AttendanceRecord.id)
            .join(Employee, AttendanceRecord.employee_id == Employee.id)
            .where(Employee.department_id == ensure_employee(user).department_id)
        )
    if status:
        query = query.where(AttendanceAdjustment.status == status)
    return paginated(
        db,
        query.order_by(AttendanceAdjustment.created_at.desc()),
        pagination,
        lambda x: {
            "id": x.id,
            "attendance_id": x.attendance_id,
            **attendance_identity(db, x.attendance_id),
            "requested_by": x.requested_by,
            "proposed_check_in": x.proposed_check_in,
            "proposed_check_out": x.proposed_check_out,
            "reason": x.reason,
            "status": x.status.value,
            "reviewed_by": x.reviewed_by,
            "review_note": x.review_note,
            "reviewed_at": x.reviewed_at,
        },
    )


@attendance_router.post("/api/v1/attendance/adjustments", status_code=201)
def request_adjustment(payload: AdjustmentIn, db: Db, user: CurrentUser):
    record = db.get(AttendanceRecord, payload.attendance_id)
    if not record:
        raise HTTPException(404, "Không tìm thấy bản ghi chấm công")
    enforce_employee_scope(db, user, record.employee_id)
    item = AttendanceAdjustment(**payload.model_dump(), requested_by=user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": item.status.value}


@attendance_router.post("/api/v1/attendance/adjustments/{adjustment_id}/review")
def review_adjustment(adjustment_id: int, payload: ReviewIn, db: Db, reviewer: Manager):
    item = db.get(AttendanceAdjustment, adjustment_id)
    if not item or item.status != RequestStatus.PENDING:
        raise HTTPException(409, "Yêu cầu không tồn tại hoặc đã xử lý")
    record = db.get(AttendanceRecord, item.attendance_id)
    enforce_employee_scope(db, reviewer, record.employee_id)
    item.status = RequestStatus.APPROVED if payload.approve else RequestStatus.REJECTED
    item.reviewed_by = reviewer.id
    item.review_note = payload.note
    item.reviewed_at = now_utc()
    if payload.approve:
        if item.proposed_check_in:
            record.check_in_at = item.proposed_check_in
        if item.proposed_check_out:
            record.check_out_at = item.proposed_check_out
        attendance.recalculate(record)
    db.commit()
    return {"id": item.id, "status": item.status.value}


@leave_router.post("/api/v1/leave-types", status_code=201)
def create_leave_type(payload: LeaveTypeIn, db: Db, admin: Admin):
    item = LeaveType(**payload.model_dump())
    db.add(item)
    db.commit()
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
    item = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.employee_id == payload.employee_id,
            LeaveBalance.leave_type_id == payload.leave_type_id,
            LeaveBalance.year == payload.year,
        )
    )
    if item:
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
    await manager.broadcast({"type": "leave_requested", "leave_id": item.id})
    return {"id": item.id, "days": item.days, "status": item.status.value}


@leave_router.get("/api/v1/leaves")
def list_leaves(db: Db, user: CurrentUser, pagination: Page, status: RequestStatus | None = None):
    query = select(LeaveRequest)
    if user.role.name == RoleName.EMPLOYEE:
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
    enforce_employee_scope(db, user, item.employee_id)
    if item.status not in (RequestStatus.PENDING, RequestStatus.APPROVED):
        raise HTTPException(409, "Chỉ có thể hủy đơn đang chờ hoặc đã duyệt")
    if item.status == RequestStatus.APPROVED:
        if item.start_date <= now_utc().date():
            raise HTTPException(409, "Không thể hủy đơn đã bắt đầu")
        leave_type = db.get(LeaveType, item.leave_type_id)
        if leave_type and leave_type.deduct_balance:
            balance = db.scalar(
                select(LeaveBalance).where(
                    LeaveBalance.employee_id == item.employee_id,
                    LeaveBalance.leave_type_id == item.leave_type_id,
                    LeaveBalance.year == item.start_date.year,
                )
            )
            if balance:
                balance.used_days = max(Decimal(0), balance.used_days - item.days)
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
    await manager.broadcast(
        {"type": "leave_cancelled", "leave_id": item.id, "employee_id": item.employee_id}
    )
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
            balance = db.scalar(
                select(LeaveBalance)
                .where(
                    LeaveBalance.employee_id == item.employee_id,
                    LeaveBalance.leave_type_id == item.leave_type_id,
                    LeaveBalance.year == item.start_date.year,
                )
                .with_for_update()
            )
            if not balance or balance.allocated_days - balance.used_days < item.days:
                raise HTTPException(409, "Số ngày phép còn lại không đủ")
            balance.used_days += item.days
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


async def issue_random_check(db: Session, employee_id: int):
    user = db.scalar(select(User).where(User.employee_id == employee_id, User.active.is_(True)))
    if not user:
        raise HTTPException(404, "Không tìm thấy tài khoản nhân viên")
    raw = secrets.token_urlsafe(32)
    now = now_utc()
    item = RandomCheck(
        employee_id=employee_id,
        challenge_token_hash=hash_token(raw),
        sent_at=now,
        expires_at=now + timedelta(seconds=settings.random_check_response_seconds),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    await manager.send_user(
        user.id,
        {
            "type": "random_check",
            "id": item.id,
            "challenge_token": raw,
            "expires_at": item.expires_at.isoformat(),
        },
    )
    return item


async def run_scheduled_random_check():
    """Select one checked-in employee; missed checks only create reviewable alerts."""
    with SessionLocal() as db:
        cutoff = now_utc() - timedelta(minutes=settings.random_check_interval_minutes)
        recent_employee_ids = select(RandomCheck.employee_id).where(RandomCheck.sent_at >= cutoff)
        candidates = db.scalars(
            select(AttendanceRecord.employee_id).where(
                AttendanceRecord.check_out_at.is_(None),
                AttendanceRecord.employee_id.not_in(recent_employee_ids),
            )
        ).all()
        if not candidates:
            return
        await issue_random_check(db, secrets.choice(candidates))


@security_router.post("/api/v1/random-checks/{employee_id:int}", status_code=201)
async def trigger_random_check(employee_id: int, db: Db, reviewer: Manager):
    enforce_employee_scope(db, reviewer, employee_id)
    item = await issue_random_check(db, employee_id)
    return {"id": item.id, "expires_at": item.expires_at, "status": item.result}


@security_router.post("/api/v1/random-checks/respond")
def respond_random_check(payload: RandomCheckResponse, request: Request, db: Db, user: CurrentUser):
    item = db.scalar(
        select(RandomCheck).where(
            RandomCheck.employee_id == user.employee_id,
            RandomCheck.challenge_token_hash == hash_token(payload.challenge_token),
            RandomCheck.result == "PENDING",
        )
    )
    if not item:
        raise HTTPException(404, "Yêu cầu xác minh không hợp lệ")
    now = now_utc()
    if item.expires_at.replace(tzinfo=UTC) < now:
        item.result = "UNVERIFIED"
        db.commit()
        raise HTTPException(410, "Yêu cầu xác minh đã hết hạn")
    item.responded_at = now
    item.response_ip = client_ip(request)
    item.result = "VERIFIED"
    db.commit()
    return {"id": item.id, "result": item.result}


@security_router.get("/api/v1/random-checks")
def list_random_checks(db: Db, user: CurrentUser, pagination: Page, employee_id: int | None = None):
    query = select(RandomCheck)
    if user.role.name == RoleName.EMPLOYEE:
        query = query.where(RandomCheck.employee_id == user.employee_id)
    elif user.role.name == RoleName.MANAGER:
        query = query.join(Employee).where(
            Employee.department_id == ensure_employee(user).department_id
        )
    if employee_id:
        if user.role.name == RoleName.EMPLOYEE and employee_id != user.employee_id:
            raise HTTPException(403, "Không được xem xác minh của người khác")
        query = query.where(RandomCheck.employee_id == employee_id)
    return paginated(
        db,
        query.order_by(RandomCheck.sent_at.desc()),
        pagination,
        lambda x: {
            "id": x.id,
            "employee_id": x.employee_id,
            **employee_identity(db, x.employee_id),
            "sent_at": x.sent_at,
            "expires_at": x.expires_at,
            "responded_at": x.responded_at,
            "result": x.result,
            "response_ip": x.response_ip,
        },
    )


@security_router.get("/api/v1/security-alerts")
def list_alerts(db: Db, reviewer: Manager, pagination: Page, status: str | None = None):
    query = select(SecurityAlert)
    if reviewer.role.name == RoleName.MANAGER:
        query = query.join(Employee).where(
            Employee.department_id == ensure_employee(reviewer).department_id
        )
    if status:
        query = query.where(SecurityAlert.status == status)
    return paginated(
        db,
        query.order_by(SecurityAlert.created_at.desc()),
        pagination,
        lambda x: {
            "id": x.id,
            "employee_id": x.employee_id,
            **employee_identity(db, x.employee_id),
            "type": x.alert_type,
            "severity": x.severity,
            "description": x.description,
            "evidence": x.evidence,
            "status": x.status,
            "created_at": x.created_at,
        },
    )


@security_router.post("/api/v1/security-alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, payload: ReviewIn, db: Db, reviewer: Manager):
    item = db.get(SecurityAlert, alert_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy cảnh báo")
    if item.employee_id:
        enforce_employee_scope(db, reviewer, item.employee_id)
    elif reviewer.role.name == RoleName.MANAGER:
        raise HTTPException(403, "Cảnh báo hệ thống chỉ dành cho Admin")
    item.status = "CONFIRMED" if payload.approve else "DISMISSED"
    item.resolved_by = reviewer.id
    item.resolution_note = payload.note
    item.resolved_at = now_utc()
    db.commit()
    return {"id": item.id, "status": item.status}


@security_router.get("/api/v1/notifications")
def notifications(db: Db, user: CurrentUser, pagination: Page):
    return paginated(
        db,
        select(Notification)
        .where(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc()),
        pagination,
        lambda x: {
            "id": x.id,
            "title": x.title,
            "message": x.message,
            "category": x.category,
            "read_at": x.read_at,
            "created_at": x.created_at,
        },
    )


@security_router.post("/api/v1/notifications/{notification_id}/read", status_code=204)
def mark_notification_read(notification_id: int, db: Db, user: CurrentUser):
    item = db.get(Notification, notification_id)
    if not item or item.user_id != user.id:
        raise HTTPException(404, "Không tìm thấy thông báo")
    item.read_at = now_utc()
    db.commit()
    return Response(status_code=204)


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
    department_id, employee_id = scoped_report_filters(db, reviewer, department_id, employee_id)
    content = pdf_report(report_rows(db, start, end, department_id, employee_id))
    return Response(
        content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="attendance_{start}_{end}.pdf"'},
    )


@admin_router.get("/api/v1/dashboard")
def dashboard(db: Db, user: CurrentUser):
    today = now_utc().date()
    attendance_scope = select(AttendanceRecord.id).join(Employee)
    leave_scope = select(LeaveRequest.id).join(Employee)
    alert_scope = select(SecurityAlert.id).join(Employee)
    employee_scope = select(Employee.id).where(Employee.active.is_(True))
    if user.role.name == RoleName.EMPLOYEE:
        attendance_scope = attendance_scope.where(AttendanceRecord.employee_id == user.employee_id)
        leave_scope = leave_scope.where(LeaveRequest.employee_id == user.employee_id)
        alert_scope = alert_scope.where(SecurityAlert.employee_id == user.employee_id)
        employee_scope = employee_scope.where(Employee.id == user.employee_id)
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


@admin_router.get("/api/v1/settings")
def list_settings(db: Db, admin: Admin, pagination: Page):
    return paginated(
        db,
        select(SystemSetting).order_by(SystemSetting.key),
        pagination,
        lambda x: {"key": x.key, "value": x.value, "description": x.description},
    )


@admin_router.put("/api/v1/settings/{key}")
def update_setting(key: str, payload: SettingIn, request: Request, db: Db, admin: Admin):
    item = db.get(SystemSetting, key)
    if item:
        before = item.value
        item.value = payload.value
        item.description = payload.description
        item.updated_by = admin.id
    else:
        before = None
        item = SystemSetting(key=key, **payload.model_dump(), updated_by=admin.id)
        db.add(item)
    audit(
        db,
        "SETTING_UPDATED",
        admin,
        client_ip(request),
        item,
        before={"value": before},
        after={"value": payload.value},
    )
    db.commit()
    return {"key": key, **payload.model_dump()}


@admin_router.get("/api/v1/audit-logs")
def audit_logs(
    db: Db,
    admin: Admin,
    pagination: Page,
    limit: int | None = Query(default=None, ge=1, le=1000),
):
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    if limit is not None and pagination.page is None:
        query = query.limit(limit)
    return paginated(
        db,
        query,
        pagination,
        lambda x: {
            "id": x.id,
            "user_id": x.user_id,
            "action": x.action,
            "entity_type": x.entity_type,
            "entity_id": x.entity_id,
            "client_ip": x.client_ip,
            "created_at": x.created_at,
        },
    )


@admin_router.get("/api/v1/clients")
def connected_clients(db: Db, admin: Admin, pagination: Page):
    connection_counts = manager.connection_counts()
    if not connection_counts:
        return paginated_rows([], pagination)
    users = db.scalars(
        select(User).where(User.id.in_(connection_counts)).order_by(User.username)
    ).all()
    rows = [
        {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.name.value,
            "employee_id": user.employee_id,
            "connections": connection_counts[user.id],
        }
        for user in users
    ]
    return paginated_rows(rows, pagination)


@admin_router.post("/api/v1/admin/backup")
def create_backup(request: Request, db: Db, admin: Admin):
    try:
        path = backup_database()
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(500, f"Sao lưu thất bại: {exc}") from exc
    audit(db, "DATABASE_BACKUP", admin, client_ip(request), after={"filename": path.name})
    db.commit()
    return {"filename": path.name, "created_at": now_utc()}


@admin_router.get("/api/v1/admin/backups")
def list_backups(admin: Admin, pagination: Page):
    directory = Path(settings.backup_directory).resolve()
    if not directory.exists():
        return paginated_rows([], pagination)
    rows = [
        {
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "modified_at": datetime.fromtimestamp(path.stat().st_mtime, UTC),
        }
        for path in sorted(directory.glob("attendance_*.sqlite3"), reverse=True)
        if path.is_file()
    ]
    return paginated_rows(rows, pagination)


@admin_router.post("/api/v1/admin/restore/{filename}")
def restore_backup(filename: str, request: Request, db: Db, admin: Admin):
    if Path(filename).name != filename:
        raise HTTPException(400, "Tên tệp không hợp lệ")
    audit(db, "DATABASE_RESTORE_REQUESTED", admin, client_ip(request), after={"filename": filename})
    db.commit()
    try:
        restore_database(Path(settings.backup_directory) / filename)
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(500, f"Khôi phục thất bại: {exc}") from exc
    return {"status": "restored", "filename": filename}


@security_router.websocket("/api/v1/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query()):
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        session_id = payload["sid"]
    except (jwt.PyJWTError, KeyError, ValueError):
        await websocket.close(code=4401)
        return
    with SessionLocal() as db:
        session = db.scalar(
            select(LoginSession).where(
                LoginSession.id == session_id,
                LoginSession.user_id == user_id,
                LoginSession.token_hash == hash_token(token),
                LoginSession.revoked_at.is_(None),
            )
        )
        if not session:
            await websocket.close(code=4401)
            return
    await manager.connect(user_id, websocket)
    try:
        await websocket.send_json({"type": "connected", "server_time": now_utc().isoformat()})
        while True:
            message = await websocket.receive_text()
            if message == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await manager.disconnect(user_id, websocket)


for domain_router in ALL_ROUTERS:
    app.include_router(domain_router)
