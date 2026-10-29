from datetime import UTC, date, datetime, time

import pytest
from app.database.session import SessionLocal
from app.models.entities import AttendanceStatus, Employee, Shift, ShiftAssignment
from app.services.attendance import check_in, check_out
from fastapi import HTTPException


def test_check_in_out_and_idempotency(client, employee_headers):
    payload = {"device_fingerprint": None, "idempotency_key": "request-0001"}
    first = client.post("/api/v1/attendance/check-in", json=payload, headers=employee_headers)
    assert first.status_code == 201, first.text
    replay = client.post("/api/v1/attendance/check-in", json=payload, headers=employee_headers)
    assert replay.status_code == 201
    assert replay.json()["id"] == first.json()["id"]
    duplicate = client.post("/api/v1/attendance/check-in", json={**payload, "idempotency_key": "request-0002"}, headers=employee_headers)
    assert duplicate.status_code == 409
    checkout = client.post("/api/v1/attendance/check-out", json={**payload, "idempotency_key": "request-0003"}, headers=employee_headers)
    assert checkout.status_code == 200
    assert checkout.json()["check_out_at"] is not None


def test_overnight_shift_late_early_calculation():
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        old = db.query(ShiftAssignment).filter_by(employee_id=employee.id).one()
        db.delete(old)
        shift = Shift(code="NIGHT", name="Ca đêm", start_time=time(22, 0), end_time=time(6, 0), break_minutes=30)
        db.add(shift)
        db.flush()
        work_date = date(2026, 10, 28)
        db.add(ShiftAssignment(employee_id=employee.id, shift_id=shift.id, work_date=work_date))
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        record = check_in(db, employee, "192.168.1.20", None, datetime(2026, 10, 28, 22, 10, tzinfo=UTC))
        assert record.late_minutes == 10
        record = check_out(db, employee, "192.168.1.20", datetime(2026, 10, 29, 5, 50, tzinfo=UTC))
        assert record.early_leave_minutes == 10
        assert record.status == AttendanceStatus.LATE_AND_EARLY


def test_no_assignment_rejected():
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        with pytest.raises(HTTPException) as exc:
            check_in(db, employee, "192.168.1.20", None, datetime(2030, 1, 1, 8, tzinfo=UTC))
        assert exc.value.status_code == 409
