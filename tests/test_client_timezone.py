from datetime import timedelta

from client.app.timezone import APP_TIMEZONE_NAME, to_local_datetime


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
