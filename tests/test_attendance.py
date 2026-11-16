from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from app.api.common import attendance_dict
from app.core.config import get_settings
from app.database.session import SessionLocal
from app.models.entities import AttendanceStatus, Employee, Shift, ShiftAssignment
from app.services.attendance import check_in, check_out
from fastapi import HTTPException

LOCAL_TIMEZONE = ZoneInfo("Asia/Ho_Chi_Minh")


def assign_test_shift(
    *,
    work_date: date,
    code: str = "POLICY",
    start: time = time(8, 0),
    end: time = time(17, 0),
    break_minutes: int = 0,
    late_grace_minutes: int = 0,
) -> None:
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        shift = Shift(
            code=code,
            name="Ca kiểm thử chính sách",
            start_time=start,
            end_time=end,
            break_minutes=break_minutes,
            # Legacy shift values must not make the common 15-minute policy vary.
            late_grace_minutes=late_grace_minutes,
        )
        db.add(shift)
        db.flush()
        db.add(
            ShiftAssignment(
                employee_id=employee.id,
                shift_id=shift.id,
                work_date=work_date,
            )
        )


def test_check_in_out_and_idempotency(client, employee_headers, approved_employee_device):
    payload = {
        "device_fingerprint": approved_employee_device,
        "idempotency_key": "request-0001",
        "latitude": 10.776889,
        "longitude": 106.700806,
        "location_accuracy_meters": 8.5,
    }
    first = client.post("/api/v1/attendance/check-in", json=payload, headers=employee_headers)
    assert first.status_code == 201, first.text
    assert first.json()["check_in_latitude"] == 10.776889
    assert first.json()["check_in_longitude"] == 106.700806
    assert first.json()["check_in_accuracy_meters"] == 8.5
    assert first.json()["check_in_location_source"] == "GPS"
    replay = client.post("/api/v1/attendance/check-in", json=payload, headers=employee_headers)
    assert replay.status_code == 201
    assert replay.json()["id"] == first.json()["id"]
    duplicate = client.post(
        "/api/v1/attendance/check-in",
        json={**payload, "idempotency_key": "request-0002"},
        headers=employee_headers,
    )
    assert duplicate.status_code == 409
    checkout = client.post(
        "/api/v1/attendance/check-out",
        json={
            **payload,
            "idempotency_key": "request-0003",
            "latitude": 10.777,
            "longitude": 106.701,
            "location_accuracy_meters": 12,
        },
        headers=employee_headers,
    )
    assert checkout.status_code == 200
    assert checkout.json()["check_out_at"] is not None
    assert checkout.json()["check_out_latitude"] == 10.777
    assert checkout.json()["check_out_longitude"] == 106.701


def test_attendance_rejects_incomplete_or_invalid_gps(client, employee_headers):
    incomplete = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": "approved-employee-test-device",
            "idempotency_key": "incomplete-gps",
            "latitude": 10.7,
        },
        headers=employee_headers,
    )
    assert incomplete.status_code == 422

    invalid = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": "approved-employee-test-device",
            "idempotency_key": "invalid-gps",
            "latitude": 91,
            "longitude": 106.7,
        },
        headers=employee_headers,
    )
    assert invalid.status_code == 422


def test_attendance_rejects_missing_device_fingerprint(client, employee_headers):
    response = client.post(
        "/api/v1/attendance/check-in",
        json={"device_fingerprint": None, "idempotency_key": "missing-device"},
        headers=employee_headers,
    )
    assert response.status_code == 422


def test_attendance_allows_lan_ip_fallback(
    client, employee_headers, approved_employee_device
):
    response = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "lan-ip-fallback",
            "location_source": "LAN_IP_FALLBACK",
        },
        headers=employee_headers,
    )

    assert response.status_code == 201, response.text
    assert response.json()["location_source"] == "LAN_IP_FALLBACK"
    assert response.json()["location_fallback_ip"] == "127.0.0.1"
    assert response.json()["check_in_latitude"] is None
    assert response.json()["check_in_location_source"] == "LAN_IP_FALLBACK"


def test_attendance_can_disable_lan_ip_fallback(
    client, employee_headers, approved_employee_device, monkeypatch
):
    from app.api import application

    monkeypatch.setattr(application.settings, "allow_lan_ip_location_fallback", False)
    response = client.post(
        "/api/v1/attendance/check-in",
        json={
            "device_fingerprint": approved_employee_device,
            "idempotency_key": "lan-ip-disabled",
            "location_source": "LAN_IP_FALLBACK",
        },
        headers=employee_headers,
    )

    assert response.status_code == 422
    assert "IP nội bộ đang bị tắt" in response.json()["detail"]


def test_common_work_timezone_is_utc_plus_7():
    settings = get_settings()

    assert settings.work_timezone == "Asia/Ho_Chi_Minh"
    local_time = datetime(2026, 11, 13, 8, tzinfo=ZoneInfo(settings.work_timezone))
    assert local_time.utcoffset() == timedelta(hours=7)


@pytest.mark.parametrize(
    (
        "delay_minutes",
        "legacy_grace_minutes",
        "expected_late_minutes",
        "expected_status",
    ),
    [
        (14, 5, 0, AttendanceStatus.OPEN),
        (15, 10, 15, AttendanceStatus.LATE),
        (16, 15, 16, AttendanceStatus.LATE),
    ],
)
def test_common_late_threshold_boundary(
    delay_minutes: int,
    legacy_grace_minutes: int,
    expected_late_minutes: int,
    expected_status: AttendanceStatus,
):
    work_date = date(2029, 1, 8)
    assign_test_shift(
        work_date=work_date,
        late_grace_minutes=legacy_grace_minutes,
    )
    local_check_in = datetime.combine(
        work_date,
        time(8, delay_minutes),
        tzinfo=LOCAL_TIMEZONE,
    )

    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        record = check_in(
            db,
            employee,
            "192.168.1.20",
            None,
            local_check_in.astimezone(UTC),
        )

        assert record.check_in_at == local_check_in.astimezone(UTC)
        assert record.late_minutes == expected_late_minutes
        assert record.status == expected_status


def test_early_check_in_keeps_actual_time_and_is_not_late():
    work_date = date(2029, 1, 9)
    assign_test_shift(work_date=work_date)
    local_check_in = datetime(2029, 1, 9, 7, 45, tzinfo=LOCAL_TIMEZONE)

    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        record = check_in(
            db,
            employee,
            "192.168.1.20",
            None,
            local_check_in.astimezone(UTC),
        )

        assert record.check_in_at == local_check_in.astimezone(UTC)
        assert record.late_minutes == 0
        assert record.status == AttendanceStatus.OPEN


def test_checkout_calculates_worked_minutes_and_admin_api_has_shift_details(
    client, admin_headers
):
    work_date = date(2029, 1, 10)
    assign_test_shift(work_date=work_date, break_minutes=60)
    check_in_at = datetime(2029, 1, 10, 8, 15, tzinfo=LOCAL_TIMEZONE).astimezone(UTC)
    check_out_at = datetime(2029, 1, 10, 17, 0, tzinfo=LOCAL_TIMEZONE).astimezone(UTC)

    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        record = check_in(db, employee, "192.168.1.20", None, check_in_at)
        record = check_out(db, employee, "192.168.1.20", check_out_at)
        attendance_id = record.id

        assert record.worked_minutes == 465
        assert record.late_minutes == 15
        assert record.status == AttendanceStatus.LATE
        serialized = attendance_dict(record)
        assert serialized["shift_start_time"] == "08:00"
        assert serialized["shift_end_time"] == "17:00"
        assert serialized["shift_start_at"] == datetime(
            2029, 1, 10, 1, 0, tzinfo=UTC
        )
        assert serialized["is_late"] is True
        assert serialized["work_timezone"] == "Asia/Ho_Chi_Minh"

    response = client.get("/api/v1/attendance", headers=admin_headers)
    assert response.status_code == 200, response.text
    row = next(item for item in response.json() if item["id"] == attendance_id)
    assert row["check_in_at"] is not None
    assert row["check_out_at"] is not None
    assert row["shift_start_time"] == "08:00"
    assert row["worked_minutes"] == 465
    assert row["late_minutes"] == 15
    assert row["is_late"] is True


def test_overnight_shift_late_early_calculation():
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        old = db.query(ShiftAssignment).filter_by(employee_id=employee.id).one()
        db.delete(old)
        shift = Shift(
            code="NIGHT",
            name="Ca đêm",
            start_time=time(22, 0),
            end_time=time(6, 0),
            break_minutes=30,
        )
        db.add(shift)
        db.flush()
        work_date = date(2026, 10, 28)
        db.add(ShiftAssignment(employee_id=employee.id, shift_id=shift.id, work_date=work_date))
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        check_in_at = datetime(2026, 10, 28, 22, 15, tzinfo=LOCAL_TIMEZONE).astimezone(UTC)
        record = check_in(db, employee, "192.168.1.20", None, check_in_at)
        assert record.late_minutes == 15
        check_out_at = datetime(2026, 10, 29, 5, 50, tzinfo=LOCAL_TIMEZONE).astimezone(UTC)
        record = check_out(db, employee, "192.168.1.20", check_out_at)
        assert record.early_leave_minutes == 10
        assert record.worked_minutes == 425
        assert record.status == AttendanceStatus.LATE_AND_EARLY


def test_no_assignment_rejected():
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        with pytest.raises(HTTPException) as exc:
            check_in(db, employee, "192.168.1.20", None, datetime(2030, 1, 1, 8, tzinfo=UTC))
        assert exc.value.status_code == 409


def test_checkout_cannot_be_before_checkin():
    work_date = date(2028, 1, 3)
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        shift = db.query(Shift).filter_by(code="HC").one()
        db.add(ShiftAssignment(employee_id=employee.id, shift_id=shift.id, work_date=work_date))
    with SessionLocal.begin() as db:
        employee = db.query(Employee).filter_by(employee_code="NV001").one()
        checked_in_at = datetime(2028, 1, 3, 9, tzinfo=UTC)
        check_in(db, employee, "192.168.1.20", None, checked_in_at)
        with pytest.raises(HTTPException) as exc:
            check_out(
                db,
                employee,
                "192.168.1.20",
                checked_in_at - timedelta(minutes=1),
            )
        assert exc.value.status_code == 409
