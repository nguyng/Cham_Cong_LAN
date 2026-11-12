from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.entities import (
    AttendanceRecord,
    AttendanceStatus,
    Employee,
    SecurityAlert,
    Shift,
    ShiftAssignment,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """Normalize database timestamps; SQLite drops timezone metadata in tests."""
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def local_date(value: datetime) -> date:
    return as_utc(value).astimezone(ZoneInfo(get_settings().work_timezone)).date()


def shift_window(work_date: date, shift: Shift) -> tuple[datetime, datetime]:
    timezone = ZoneInfo(get_settings().work_timezone)
    start = datetime.combine(work_date, shift.start_time, tzinfo=timezone)
    end = datetime.combine(work_date, shift.end_time, tzinfo=timezone)
    if end <= start:
        end += timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def assignment_for_now(db: Session, employee_id: int, now: datetime) -> ShiftAssignment:
    current_work_date = local_date(now)
    candidate_dates = [current_work_date, current_work_date - timedelta(days=1)]
    rows = db.scalars(
        select(ShiftAssignment)
        .where(
            ShiftAssignment.employee_id == employee_id,
            ShiftAssignment.work_date.in_(candidate_dates),
        )
        .order_by(ShiftAssignment.work_date.desc())
    ).all()
    for assignment in rows:
        start, end = shift_window(assignment.work_date, assignment.shift)
        if start - timedelta(hours=4) <= now <= end + timedelta(hours=8):
            return assignment
    raise HTTPException(409, "Không có ca làm phù hợp tại thời điểm hiện tại")


def check_in(
    db: Session,
    employee: Employee,
    ip: str,
    device_id: int | None,
    now: datetime | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    location_accuracy_meters: float | None = None,
    geofence_distance_meters: float | None = None,
):
    now = now or utc_now()
    assignment = assignment_for_now(db, employee.id, now)
    existing = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.work_date == assignment.work_date,
            AttendanceRecord.shift_id == assignment.shift_id,
        )
    )
    if existing:
        raise HTTPException(409, "Ca này đã được check-in")
    shift_start, _ = shift_window(assignment.work_date, assignment.shift)
    late = max(
        0, int((now - shift_start).total_seconds() // 60) - assignment.shift.late_grace_minutes
    )
    record = AttendanceRecord(
        employee_id=employee.id,
        shift_id=assignment.shift_id,
        work_date=assignment.work_date,
        check_in_at=now,
        check_in_ip=ip,
        check_in_latitude=latitude,
        check_in_longitude=longitude,
        check_in_accuracy_meters=location_accuracy_meters,
        check_in_geofence_distance_meters=geofence_distance_meters,
        device_id=device_id,
        status=AttendanceStatus.LATE if late else AttendanceStatus.OPEN,
        late_minutes=late,
        break_minutes=assignment.shift.break_minutes,
    )
    db.add(record)
    db.flush()
    return record


def check_out(
    db: Session,
    employee: Employee,
    ip: str,
    now: datetime | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    location_accuracy_meters: float | None = None,
    geofence_distance_meters: float | None = None,
):
    now = now or utc_now()
    record = db.scalar(
        select(AttendanceRecord)
        .where(AttendanceRecord.employee_id == employee.id, AttendanceRecord.check_out_at.is_(None))
        .order_by(AttendanceRecord.check_in_at.desc())
        .with_for_update()
    )
    if not record:
        raise HTTPException(409, "Không có ca đang mở để check-out")
    if as_utc(now) <= as_utc(record.check_in_at):
        raise HTTPException(409, "Giờ check-out phải sau giờ check-in")
    _, shift_end = shift_window(record.work_date, record.shift)
    early = max(0, int((shift_end - now).total_seconds() // 60) - record.shift.early_grace_minutes)
    elapsed = max(0, int((now - as_utc(record.check_in_at)).total_seconds() // 60))
    record.check_out_at = now
    record.check_out_ip = ip
    record.check_out_latitude = latitude
    record.check_out_longitude = longitude
    record.check_out_accuracy_meters = location_accuracy_meters
    record.check_out_geofence_distance_meters = geofence_distance_meters
    record.early_leave_minutes = early
    record.worked_minutes = max(0, elapsed - record.break_minutes)
    update_overtime(record, now, shift_end)
    if record.late_minutes and early:
        record.status = AttendanceStatus.LATE_AND_EARLY
    elif record.late_minutes:
        record.status = AttendanceStatus.LATE
    elif early:
        record.status = AttendanceStatus.EARLY_LEAVE
    else:
        record.status = AttendanceStatus.ON_TIME
    if elapsed < 10 or now > shift_end + timedelta(hours=4):
        record.suspicious = True
        db.add(
            SecurityAlert(
                employee_id=employee.id,
                alert_type="SUSPICIOUS_ATTENDANCE",
                description="Ca làm dưới 10 phút hoặc check-out ngoài khung giờ",
                evidence={"attendance_id": record.id, "elapsed_minutes": elapsed},
            )
        )
    db.flush()
    return record


def recalculate(record: AttendanceRecord):
    start, end = shift_window(record.work_date, record.shift)
    record.late_minutes = max(
        0,
        int((as_utc(record.check_in_at) - start).total_seconds() // 60)
        - record.shift.late_grace_minutes,
    )
    if not record.check_out_at:
        record.early_leave_minutes = 0
        record.status = AttendanceStatus.LATE if record.late_minutes else AttendanceStatus.OPEN
        return
    record.early_leave_minutes = max(
        0,
        int((end - as_utc(record.check_out_at)).total_seconds() // 60)
        - record.shift.early_grace_minutes,
    )
    record.worked_minutes = max(
        0,
        int((as_utc(record.check_out_at) - as_utc(record.check_in_at)).total_seconds() // 60)
        - record.break_minutes,
    )
    update_overtime(record, as_utc(record.check_out_at), end)
    if record.late_minutes and record.early_leave_minutes:
        record.status = AttendanceStatus.LATE_AND_EARLY
    elif record.late_minutes:
        record.status = AttendanceStatus.LATE
    elif record.early_leave_minutes:
        record.status = AttendanceStatus.EARLY_LEAVE
    else:
        record.status = AttendanceStatus.ON_TIME


def update_overtime(
    record: AttendanceRecord, check_out_at: datetime, shift_end: datetime
) -> None:
    """Detect time worked after the scheduled shift and invalidate stale approval."""

    overtime_minutes = max(
        0, int((as_utc(check_out_at) - as_utc(shift_end)).total_seconds() // 60)
    )
    if overtime_minutes == record.overtime_minutes:
        return
    record.overtime_minutes = overtime_minutes
    record.approved_overtime_minutes = 0
    record.overtime_status = "PENDING" if overtime_minutes else "NONE"
    record.overtime_reviewed_by = None
    record.overtime_review_note = None
    record.overtime_reviewed_at = None
