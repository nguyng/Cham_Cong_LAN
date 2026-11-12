import logging
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import jwt
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.common import (
    audit,
    employee_dict,
    employee_identity,
    enforce_employee_scope,
    ensure_employee,
    now_utc,
    protect_admin_continuity,
    validate_date_range,
)
from app.api.deps import Admin, CurrentUser, Db, Manager, client_ip
from app.api.pagination import Page, paginated, paginated_rows
from app.api.routers import (
    ALL_ROUTERS,
    admin_router,
    auth_router,
    organization_router,
    security_router,
    system_router,
)
from app.api.routes import attendance as _attendance_routes
from app.api.routes import leave as _leave_routes
from app.api.routes import reporting as _reporting_routes
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
    AssignmentIn,
    DepartmentIn,
    DeviceIn,
    EmployeeIn,
    EmployeeUpdate,
    LoginRequest,
    PasswordChange,
    PositionIn,
    RandomCheckResponse,
    ReviewIn,
    SettingIn,
    ShiftIn,
    TokenResponse,
)
from app.services.backup import backup_database, restore_database
from app.services.discovery import discovery_server
from app.services.maintenance import cleanup_expired_records
from app.websocket.manager import manager

settings = get_settings()
logger = logging.getLogger("attendance.server")
# Importing each domain module registers its endpoints on the shared APIRouter.
DOMAIN_ROUTE_MODULES = (_attendance_routes, _leave_routes, _reporting_routes)

ADMIN_REMOVABLE_MODELS = {
    "employees": Employee,
    "departments": Department,
    "positions": Position,
    "shifts": Shift,
    "shift-assignments": ShiftAssignment,
    "attendance": AttendanceRecord,
    "attendance-adjustments": AttendanceAdjustment,
    "leaves": LeaveRequest,
    "leave-types": LeaveType,
    "leave-balances": LeaveBalance,
    "security-alerts": SecurityAlert,
    "random-checks": RandomCheck,
    "devices": Device,
    "users": User,
    "settings": SystemSetting,
}

# Dữ liệu danh mục/tài khoản phải được giữ lại để báo cáo lịch sử không
# mất liên kết. Nút Xóa sẽ lưu trữ các bản ghi này thay vì xóa vật lý.
ADMIN_ARCHIVED_RESOURCES = {
    "employees",
    "departments",
    "positions",
    "shifts",
    "leave-types",
    "users",
}


def validate_employee_references(
    db: Session, department_id: int | None, position_id: int | None
):
    if department_id is not None:
        department = db.get(Department, department_id)
        if not department or not department.active:
            raise HTTPException(409, "Phòng ban không tồn tại hoặc đã ngừng hoạt động")
    if position_id is not None:
        position = db.get(Position, position_id)
        if not position or not position.active:
            raise HTTPException(409, "Chức vụ không tồn tại hoặc đã ngừng hoạt động")


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
            await manager.broadcast({"type": "security_alerts_updated"})


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


@app.exception_handler(RequestValidationError)
async def request_validation_error(_request: Request, exc: RequestValidationError):
    fields = []
    for error in exc.errors():
        location = ".".join(
            str(part) for part in error.get("loc", []) if part not in ("body", "query", "path")
        )
        message = error.get("msg", "không hợp lệ")
        fields.append(f"{location}: {message}" if location else str(message))
    detail = "Dữ liệu không hợp lệ: " + "; ".join(fields or ["vui lòng kiểm tra lại"])
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": detail, "errors": exc.errors()}),
    )


@app.exception_handler(Exception)
async def unexpected_server_error(request: Request, exc: Exception):
    error_id = secrets.token_hex(4).upper()
    logger.error(
        "Unhandled request error id=%s method=%s path=%s",
        error_id,
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Server gặp lỗi nội bộ. Mã lỗi: {error_id}. Hãy kiểm tra cửa sổ Server."
        },
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
    if item.role.name != role and item.role.name == RoleName.ADMIN:
        protect_admin_continuity(db, item, admin)
    before = {"role": item.role.name.value}
    item.role_id = target_role.id
    if before["role"] != role.value:
        db.query(LoginSession).filter(
            LoginSession.user_id == item.id,
            LoginSession.revoked_at.is_(None),
        ).update({LoginSession.revoked_at: now_utc()})
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
    try:
        db.flush()
        audit(
            db,
            "DEPARTMENT_CREATED",
            admin,
            client_ip(request),
            item,
            after=payload.model_dump(mode="json"),
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã hoặc tên phòng ban đã tồn tại") from None
    db.refresh(item)
    return {"id": item.id, **payload.model_dump()}


@organization_router.get("/api/v1/departments")
def list_departments(
    db: Db, user: CurrentUser, pagination: Page, active: bool | None = None
):
    query = select(Department)
    if active is not None:
        query = query.where(Department.active.is_(active))
    return paginated(
        db,
        query.order_by(Department.name),
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
def list_positions(db: Db, user: CurrentUser, pagination: Page, active: bool | None = None):
    query = select(Position)
    if active is not None:
        query = query.where(Position.active.is_(active))
    return paginated(
        db,
        query.order_by(Position.name),
        pagination,
        lambda x: {"id": x.id, "code": x.code, "name": x.name, "active": x.active},
    )


@organization_router.put("/api/v1/positions/{position_id}")
def update_position(position_id: int, payload: PositionIn, db: Db, admin: Admin):
    item = db.get(Position, position_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy chức vụ")
    item.code, item.name = payload.code, payload.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã hoặc tên chức vụ đã tồn tại") from None
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
    validate_employee_references(db, payload.department_id, payload.position_id)
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
    validate_employee_references(db, payload.department_id, payload.position_id)
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
    user = db.scalar(select(User).where(User.employee_id == item.id))
    if not active:
        open_attendance = db.scalar(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.employee_id == item.id,
                AttendanceRecord.check_out_at.is_(None),
            )
        )
        if open_attendance:
            raise HTTPException(409, "Nhân viên đang có ca mở; hãy check-out trước khi vô hiệu hóa")
    if user and item.active and not active:
        protect_admin_continuity(db, user, admin)
    item.active = active
    if user:
        user.active = active
        if not active:
            db.query(LoginSession).filter(
                LoginSession.user_id == user.id,
                LoginSession.revoked_at.is_(None),
            ).update({LoginSession.revoked_at: now_utc()})
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
def list_shifts(db: Db, user: CurrentUser, pagination: Page, active: bool | None = None):
    query = select(Shift)
    if active is not None:
        query = query.where(Shift.active.is_(active))
    return paginated(
        db,
        query.order_by(Shift.name),
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
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Mã ca đã tồn tại") from None
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
    employee = enforce_employee_scope(db, manager_user, payload.employee_id)
    if not employee.active:
        raise HTTPException(409, "Nhân viên đã ngừng hoạt động")
    shift = db.get(Shift, payload.shift_id)
    if not shift or not shift.active:
        raise HTTPException(409, "Ca làm không tồn tại hoặc đã ngừng hoạt động")
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
    if not results:
        raise HTTPException(400, "Khoảng ngày không chứa thứ làm việc đã chọn")
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
    mine: bool = False,
):
    validate_date_range(start, end)
    query = select(ShiftAssignment)
    if mine:
        query = query.where(ShiftAssignment.employee_id == ensure_employee(user).id)
    elif user.role.name == RoleName.EMPLOYEE:
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


@organization_router.post("/api/v1/devices", status_code=201)
def register_device(payload: DeviceIn, request: Request, db: Db, user: CurrentUser):
    employee = ensure_employee(user)
    fingerprint_hash = hash_token(payload.fingerprint)
    existing = db.scalar(
        select(Device).where(
            Device.employee_id == employee.id,
            Device.fingerprint_hash == fingerprint_hash,
        )
    )
    if existing:
        existing.device_name = payload.device_name
        if not existing.active:
            existing.active = True
            existing.approved = False
        existing.last_ip = client_ip(request)
        existing.last_seen_at = now_utc()
        db.commit()
        return {"id": existing.id, "approved": existing.approved}
    item = Device(
        employee_id=employee.id,
        fingerprint_hash=fingerprint_hash,
        device_name=payload.device_name,
        last_ip=client_ip(request),
        last_seen_at=now_utc(),
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Device).where(
                Device.employee_id == employee.id,
                Device.fingerprint_hash == fingerprint_hash,
            )
        )
        if existing:
            return {"id": existing.id, "approved": existing.approved}
        raise HTTPException(409, "Không thể đăng ký thiết bị") from None
    db.refresh(item)
    return {"id": item.id, "approved": item.approved}


@organization_router.patch("/api/v1/devices/{device_id}/approve")
def approve_device(
    device_id: int,
    approved: bool,
    request: Request,
    db: Db,
    reviewer: Manager,
):
    item = db.get(Device, device_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy thiết bị")
    enforce_employee_scope(db, reviewer, item.employee_id)
    if approved and not item.active:
        raise HTTPException(409, "Thiết bị đã bị xóa; nhân viên phải đăng ký lại trước khi duyệt")
    if not approved:
        open_attendance = db.scalar(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.device_id == item.id,
                AttendanceRecord.check_out_at.is_(None),
            )
        )
        if open_attendance:
            raise HTTPException(409, "Thiết bị đang được dùng cho ca mở; hãy check-out trước khi thu hồi")
    before = {"approved": item.approved}
    item.approved = approved
    audit(
        db,
        "DEVICE_APPROVAL_CHANGED",
        reviewer,
        client_ip(request),
        item,
        before=before,
        after={"approved": approved},
    )
    db.commit()
    return {"id": item.id, "approved": item.approved}


@organization_router.get("/api/v1/devices")
def list_devices(
    db: Db,
    reviewer: Manager,
    pagination: Page,
    approved: bool | None = None,
    active: bool | None = None,
):
    query = select(Device)
    if reviewer.role.name == RoleName.MANAGER:
        query = query.join(Employee).where(
            Employee.department_id == ensure_employee(reviewer).department_id
        )
    if approved is not None:
        query = query.where(Device.approved.is_(approved))
    if active is not None:
        query = query.where(Device.active.is_(active))
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


@organization_router.delete("/api/v1/devices/{device_id}")
def remove_old_device(device_id: int, request: Request, db: Db, reviewer: Manager):
    item = db.get(Device, device_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy thiết bị")
    enforce_employee_scope(db, reviewer, item.employee_id)
    open_attendance = db.scalar(
        select(func.count(AttendanceRecord.id)).where(
            AttendanceRecord.device_id == item.id,
            AttendanceRecord.check_out_at.is_(None),
        )
    )
    if open_attendance:
        raise HTTPException(409, "Thiết bị đang được dùng cho ca mở; hãy check-out trước khi xóa")
    before = {
        "employee_id": item.employee_id,
        "device_name": item.device_name,
        "approved": item.approved,
        "active": item.active,
    }
    linked_attendance = db.scalar(
        select(func.count()).select_from(AttendanceRecord).where(AttendanceRecord.device_id == item.id)
    )
    archived = bool(linked_attendance)
    audit(
        db,
        "DEVICE_REMOVED",
        reviewer,
        client_ip(request),
        item,
        before=before,
        after={"approved": False, "active": False, "archived": archived},
    )
    if archived:
        item.approved = False
        item.active = False
    else:
        db.delete(item)
    db.commit()
    return {"id": device_id, "deleted": not archived, "archived": archived}


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




async def issue_random_check(db: Session, employee_id: int):
    user = db.scalar(select(User).where(User.employee_id == employee_id, User.active.is_(True)))
    if not user:
        raise HTTPException(404, "Không tìm thấy tài khoản nhân viên")
    open_attendance = db.scalar(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.employee_id == employee_id,
            AttendanceRecord.check_out_at.is_(None),
        )
        .order_by(AttendanceRecord.check_in_at.desc())
    )
    if not open_attendance:
        raise HTTPException(409, "Nhân viên chưa check-in hoặc đã check-out")
    raw = secrets.token_urlsafe(32)
    now = now_utc()
    item = RandomCheck(
        employee_id=employee_id,
        attendance_id=open_attendance.id,
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
        db.add(
            SecurityAlert(
                employee_id=item.employee_id,
                alert_type="RANDOM_CHECK_MISSED",
                description="Nhân viên phản hồi Random Check sau thời hạn; cần Manager xem xét",
                evidence={"random_check_id": item.id},
            )
        )
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




@admin_router.get("/api/v1/settings")
def list_settings(db: Db, admin: Admin, pagination: Page):
    return paginated(
        db,
        select(SystemSetting).order_by(SystemSetting.key),
        pagination,
        lambda x: {"key": x.key, "value": x.value, "description": x.description},
    )


@admin_router.delete("/api/v1/admin/records/{resource}", status_code=204)
def remove_admin_record(
    resource: str,
    identifier: str,
    request: Request,
    db: Db,
    admin: Admin,
):
    """Remove an Admin-selected record while preserving required business history."""
    model = ADMIN_REMOVABLE_MODELS.get(resource)
    if model is None:
        raise HTTPException(404, "Chức năng này không hỗ trợ xóa")

    if model is SystemSetting:
        item = db.get(model, identifier)
    else:
        try:
            record_id = int(identifier)
        except ValueError:
            raise HTTPException(400, "Mã bản ghi không hợp lệ") from None
        item = db.get(model, record_id)
    if not item:
        raise HTTPException(404, "Không tìm thấy dữ liệu cần xóa")

    if isinstance(item, User):
        if item.id == admin.id:
            raise HTTPException(409, "Không thể xóa tài khoản Admin đang đăng nhập")
        if item.active and item.role.name == RoleName.ADMIN:
            active_admins = db.scalar(
                select(func.count(User.id))
                .join(Role)
                .where(User.active.is_(True), Role.name == RoleName.ADMIN)
            )
            if active_admins <= 1:
                raise HTTPException(409, "Hệ thống phải còn ít nhất một Admin hoạt động")
    if isinstance(item, Employee) and item.id == admin.employee_id:
        raise HTTPException(409, "Không thể xóa hồ sơ của Admin đang đăng nhập")
    if isinstance(item, Employee):
        open_attendance = db.scalar(
            select(func.count(AttendanceRecord.id)).where(
                AttendanceRecord.employee_id == item.id,
                AttendanceRecord.check_out_at.is_(None),
            )
        )
        if open_attendance:
            raise HTTPException(409, "Nhân viên đang có ca mở; hãy check-out trước khi xóa")
    if isinstance(item, LeaveRequest) and item.status == RequestStatus.APPROVED:
        raise HTTPException(409, "Hãy hủy đơn nghỉ đã duyệt trước khi xóa")
    if isinstance(item, LeaveBalance) and item.used_days:
        raise HTTPException(409, "Quỹ phép đã phát sinh ngày nghỉ nên không thể xóa")

    archived = resource in ADMIN_ARCHIVED_RESOURCES
    before = {"identifier": identifier}
    if archived:
        before["active"] = item.active
        item.active = False
        if isinstance(item, Employee):
            linked_user = db.scalar(select(User).where(User.employee_id == item.id))
            if linked_user:
                linked_user.active = False
                db.query(LoginSession).filter(
                    LoginSession.user_id == linked_user.id,
                    LoginSession.revoked_at.is_(None),
                ).update({LoginSession.revoked_at: now_utc()})
        elif isinstance(item, User):
            db.query(LoginSession).filter(
                LoginSession.user_id == item.id,
                LoginSession.revoked_at.is_(None),
            ).update({LoginSession.revoked_at: now_utc()})
    else:
        db.delete(item)

    audit(
        db,
        "ADMIN_RECORD_ARCHIVED" if archived else "ADMIN_RECORD_DELETED",
        admin,
        client_ip(request),
        item,
        before=before,
        after={"active": False} if archived else None,
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            "Dữ liệu đang được bản ghi khác sử dụng. Hãy xóa dữ liệu liên quan trước.",
        ) from None
    return Response(status_code=204)


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
async def websocket_endpoint(websocket: WebSocket):
    authorization = websocket.headers.get("authorization", "")
    scheme, _, credentials = authorization.partition(" ")
    token = credentials if scheme.lower() == "bearer" and credentials else None
    if not token:
        await websocket.close(code=4401)
        return
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
        user = db.get(User, user_id)
        if (
            not user
            or not user.active
            or session.expires_at.replace(tzinfo=UTC) <= now_utc()
        ):
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
        pass
    finally:
        await manager.disconnect(user_id, websocket)


for domain_router in ALL_ROUTERS:
    app.include_router(domain_router)
