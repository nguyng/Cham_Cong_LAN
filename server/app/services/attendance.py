from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

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


def shift_window(work_date: date, shift: Shift) -> tuple[datetime, datetime]:
    start = datetime.combine(work_date, shift.start_time, tzinfo=UTC)
    end = datetime.combine(work_date, shift.end_time, tzinfo=UTC)
    if end <= start:
        end += timedelta(days=1)
    return start, end


def assignment_for_now(db: Session, employee_id: int, now: datetime) -> ShiftAssignment:
    candidate_dates = [now.date(), (now - timedelta(days=1)).date()]
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
    db: Session, employee: Employee, ip: str, device_id: int | None, now: datetime | None = None
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
        device_id=device_id,
        status=AttendanceStatus.LATE if late else AttendanceStatus.OPEN,
        late_minutes=late,
        break_minutes=assignment.shift.break_minutes,
    )
    db.add(record)
    db.flush()
    return record


def check_out(db: Session, employee: Employee, ip: str, now: datetime | None = None):
    now = now or utc_now()
    record = db.scalar(
        select(AttendanceRecord)
        .where(AttendanceRecord.employee_id == employee.id, AttendanceRecord.check_out_at.is_(None))
        .order_by(AttendanceRecord.check_in_at.desc())
        .with_for_update()
    )
    if not record:
        raise HTTPException(409, "Không có ca đang mở để check-out")
    _, shift_end = shift_window(record.work_date, record.shift)
    early = max(0, int((shift_end - now).total_seconds() // 60) - record.shift.early_grace_minutes)
    elapsed = max(0, int((now - as_utc(record.check_in_at)).total_seconds() // 60))
    record.check_out_at = now
    record.check_out_ip = ip
    record.early_leave_minutes = early
    record.worked_minutes = max(0, elapsed - record.break_minutes)
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
    if not record.check_out_at:
        return
    start, end = shift_window(record.work_date, record.shift)
    record.late_minutes = max(
        0,
        int((as_utc(record.check_in_at) - start).total_seconds() // 60)
        - record.shift.late_grace_minutes,
    )
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
