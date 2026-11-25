from datetime import datetime, timedelta

from client.app.timezone import (
    APP_TIMEZONE,
    APP_TIMEZONE_NAME,
    assignment_checkin_window_open,
    to_local_datetime,
)


def test_server_utc_timestamp_is_always_displayed_in_utc_plus_seven():
    converted = to_local_datetime("2026-11-13T01:30:00+00:00")

    assert converted is not None
    assert converted.strftime("%Y-%m-%d %H:%M:%S") == "2026-11-13 08:30:00"
    assert converted.utcoffset() == timedelta(hours=7)
    assert APP_TIMEZONE_NAME == "Asia/Ho_Chi_Minh"


def test_legacy_naive_server_timestamp_is_treated_as_utc():
    converted = to_local_datetime("2026-11-13T01:30:00")

    assert converted is not None
    assert converted.strftime("%H:%M") == "08:30"


def test_invalid_timestamp_is_left_for_the_ui_to_display_safely():
    assert to_local_datetime("not-a-timestamp") is None


def test_checkin_button_is_enabled_only_during_the_assigned_shift():
    assignment = {
        "work_date": "2026-11-18",
        "shift_start_time": "08:00",
        "shift_end_time": "17:00",
    }

    assert not assignment_checkin_window_open(
        assignment, datetime(2026, 11, 18, 7, 59, tzinfo=APP_TIMEZONE)
    )
    assert assignment_checkin_window_open(
        assignment, datetime(2026, 11, 18, 8, 0, tzinfo=APP_TIMEZONE)
    )
    assert assignment_checkin_window_open(
        assignment, datetime(2026, 11, 18, 17, 0, tzinfo=APP_TIMEZONE)
    )
    assert not assignment_checkin_window_open(
        assignment, datetime(2026, 11, 18, 17, 1, tzinfo=APP_TIMEZONE)
    )


def test_checkin_window_supports_overnight_shift_from_previous_work_date():
    assignment = {
        "work_date": "2026-11-17",
        "shift_start_time": "22:00",
        "shift_end_time": "06:00",
    }

    assert assignment_checkin_window_open(
        assignment, datetime(2026, 11, 18, 0, 30, tzinfo=APP_TIMEZONE)
    )
    assert not assignment_checkin_window_open(
        assignment, datetime(2026, 11, 17, 21, 59, tzinfo=APP_TIMEZONE)
    )
    assert not assignment_checkin_window_open(
        assignment, datetime(2026, 11, 18, 6, 1, tzinfo=APP_TIMEZONE)
    )
