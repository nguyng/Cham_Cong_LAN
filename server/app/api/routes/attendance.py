from datetime import date

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.common import (
    attendance_dict,
    attendance_identity,
    audit,
    enforce_employee_scope,
    ensure_employee,
    now_utc,
    validate_date_range,
)
from app.api.deps import CurrentUser, Db, Manager, client_ip, require_lan
from app.api.pagination import Page, paginated
from app.api.routers import attendance_router
from app.core.config import get_settings
from app.core.security import hash_token
from app.models.entities import (
    AttendanceAdjustment,
    AttendanceRecord,
    Device,
    Employee,
    IdempotencyRecord,
    RequestStatus,
    RoleName,
    User,
)
from app.schemas.api import AdjustmentIn, AttendanceAction, ReviewIn
from app.services import attendance
from app.services.geofencing import validate_attendance_location
from app.websocket.manager import manager

settings = get_settings()


def approved_device(db: Session, employee_id: int, fingerprint: str, ip: str) -> Device:
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


def attendance_action(
    operation: str, payload: AttendanceAction, request: Request, db: Session, user: User
):
    ip = client_ip(request)
    require_lan(ip)
    has_gps = payload.latitude is not None and payload.longitude is not None
    if not has_gps and not settings.allow_lan_ip_location_fallback:
        raise HTTPException(
            422,
            "Server yêu cầu tọa độ GPS; chức năng dự phòng bằng IP nội bộ đang bị tắt",
        )
    geofence_distance = validate_attendance_location(
        settings,
        payload.latitude,
        payload.longitude,
        payload.location_accuracy_meters,
    )
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
        attendance.check_in(
            db,
            employee,
            ip,
            device.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_accuracy_meters=payload.location_accuracy_meters,
            geofence_distance_meters=geofence_distance,
        )
        if operation == "CHECK_IN"
        else attendance.check_out(
            db,
            employee,
            ip,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_accuracy_meters=payload.location_accuracy_meters,
            geofence_distance_meters=geofence_distance,
        )
    )
    result = jsonable_encoder(attendance_dict(record))
    result["location_source"] = "GPS" if has_gps else "LAN_IP_FALLBACK"
    result["geofence_enabled"] = settings.geofencing_enabled
    result["geofence_distance_meters"] = geofence_distance
    if not has_gps:
        result["location_fallback_ip"] = ip
    db.add(
        IdempotencyRecord(
            user_id=user.id,
            operation=operation,
            request_key=payload.idempotency_key,
            response_data=result,
        )
    )
    audit(db, operation, user, ip, record, after=result)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        replay = db.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.user_id == user.id,
                IdempotencyRecord.operation == operation,
                IdempotencyRecord.request_key == payload.idempotency_key,
            )
        )
        if replay:
            return replay.response_data
        raise HTTPException(409, "Yêu cầu chấm công bị trùng; vui lòng tải lại dữ liệu") from None
    return result


@attendance_router.post("/api/v1/attendance/check-in", status_code=201)
async def check_in(payload: AttendanceAction, request: Request, db: Db, user: CurrentUser):
    result = attendance_action("CHECK_IN", payload, request, db, user)
    await manager.broadcast({"type": "attendance_changed"})
    return result


@attendance_router.post("/api/v1/attendance/check-out")
async def check_out(payload: AttendanceAction, request: Request, db: Db, user: CurrentUser):
    result = attendance_action("CHECK_OUT", payload, request, db, user)
    await manager.broadcast({"type": "attendance_changed"})
    return result


@attendance_router.get("/api/v1/attendance")
def list_attendance(
    db: Db,
    user: CurrentUser,
    pagination: Page,
    employee_id: int | None = None,
    start: date | None = None,
    end: date | None = None,
    mine: bool = False,
    overtime_status: str | None = None,
):
    validate_date_range(start, end)
    query = select(AttendanceRecord)
    if mine:
        query = query.where(AttendanceRecord.employee_id == ensure_employee(user).id)
    elif user.role.name == RoleName.EMPLOYEE:
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
    if overtime_status:
        normalized_status = overtime_status.strip().upper()
        if normalized_status not in {"NONE", "PENDING", "APPROVED", "REJECTED"}:
            raise HTTPException(422, "Trạng thái làm thêm giờ không hợp lệ")
        query = query.where(AttendanceRecord.overtime_status == normalized_status)
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
        lambda item: {
            "id": item.id,
            "attendance_id": item.attendance_id,
            **attendance_identity(db, item.attendance_id),
            "requested_by": item.requested_by,
            "proposed_check_in": item.proposed_check_in,
            "proposed_check_out": item.proposed_check_out,
            "reason": item.reason,
            "status": item.status.value,
            "reviewed_by": item.reviewed_by,
            "review_note": item.review_note,
            "reviewed_at": item.reviewed_at,
        },
    )


@attendance_router.post("/api/v1/attendance/adjustments", status_code=201)
def request_adjustment(payload: AdjustmentIn, db: Db, user: CurrentUser):
    record = db.get(AttendanceRecord, payload.attendance_id)
    if not record:
        raise HTTPException(404, "Không tìm thấy bản ghi chấm công")
    enforce_employee_scope(db, user, record.employee_id)
    pending = db.scalar(
        select(AttendanceAdjustment.id).where(
            AttendanceAdjustment.attendance_id == record.id,
            AttendanceAdjustment.status == RequestStatus.PENDING,
        )
    )
    if pending:
        raise HTTPException(409, "Bản chấm công này đã có yêu cầu điều chỉnh đang chờ duyệt")
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
    if not record:
        raise HTTPException(409, "Bản ghi chấm công của yêu cầu không còn tồn tại")
    enforce_employee_scope(db, reviewer, record.employee_id)
    item.status = RequestStatus.APPROVED if payload.approve else RequestStatus.REJECTED
    item.reviewed_by = reviewer.id
    item.review_note = payload.note
    item.reviewed_at = now_utc()
    if payload.approve:
        effective_check_in = item.proposed_check_in or record.check_in_at
        effective_check_out = item.proposed_check_out or record.check_out_at
        if effective_check_out and attendance.as_utc(effective_check_out) <= attendance.as_utc(
            effective_check_in
        ):
            raise HTTPException(409, "Giờ check-out phải sau giờ check-in")
        if item.proposed_check_in:
            record.check_in_at = item.proposed_check_in
        if item.proposed_check_out:
            record.check_out_at = item.proposed_check_out
        attendance.recalculate(record)
    db.commit()
    return {"id": item.id, "status": item.status.value}


@attendance_router.post("/api/v1/attendance/{attendance_id}/overtime/review")
async def review_overtime(
    attendance_id: int,
    payload: ReviewIn,
    request: Request,
    db: Db,
    reviewer: Manager,
):
    record = db.get(AttendanceRecord, attendance_id)
    if not record:
        raise HTTPException(404, "Không tìm thấy bản ghi chấm công")
    enforce_employee_scope(db, reviewer, record.employee_id)
    if record.overtime_status != "PENDING" or record.overtime_minutes <= 0:
        raise HTTPException(409, "Bản ghi không có làm thêm giờ đang chờ duyệt")
    before = {
        "overtime_status": record.overtime_status,
        "approved_overtime_minutes": record.approved_overtime_minutes,
    }
    record.overtime_status = "APPROVED" if payload.approve else "REJECTED"
    record.approved_overtime_minutes = record.overtime_minutes if payload.approve else 0
    record.overtime_reviewed_by = reviewer.id
    record.overtime_review_note = payload.note
    record.overtime_reviewed_at = now_utc()
    audit(
        db,
        "OVERTIME_REVIEWED",
        reviewer,
        client_ip(request),
        record,
        before,
        {
            "overtime_status": record.overtime_status,
            "approved_overtime_minutes": record.approved_overtime_minutes,
        },
    )
    db.commit()
    await manager.broadcast({"type": "attendance_changed"})
    return attendance_dict(record)
