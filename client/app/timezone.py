"""Timezone helpers shared by the desktop client.

The attendance system has one business timezone.  Keeping the conversion here
prevents the Windows timezone of an individual workstation from changing dates
or times shown by the application.
"""

from datetime import UTC, date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

APP_TIMEZONE_NAME = "Asia/Ho_Chi_Minh"

try:
    APP_TIMEZONE = ZoneInfo(APP_TIMEZONE_NAME)
except ZoneInfoNotFoundError:  # pragma: no cover - only for Windows without tzdata
    APP_TIMEZONE = timezone(timedelta(hours=7), name=APP_TIMEZONE_NAME)


def local_now() -> datetime:
    """Return the current application time in UTC+7."""

    return datetime.now(APP_TIMEZONE)


def local_today() -> date:
    """Return today's business date in UTC+7."""

    return local_now().date()


def assignment_checkin_window_open(
    assignment: dict, now: datetime | None = None
) -> bool:
    """Return whether the current time falls within the assigned shift."""

    try:
        work_date = date.fromisoformat(str(assignment["work_date"]))
        shift_start_time = time.fromisoformat(str(assignment["shift_start_time"]))
        shift_end_time = time.fromisoformat(str(assignment["shift_end_time"]))
    except (KeyError, TypeError, ValueError):
        return False

    shift_start = datetime.combine(work_date, shift_start_time).replace(tzinfo=APP_TIMEZONE)
    shift_end = datetime.combine(work_date, shift_end_time).replace(tzinfo=APP_TIMEZONE)
    if shift_end <= shift_start:
        shift_end += timedelta(days=1)
    current_time = (now or local_now()).astimezone(APP_TIMEZONE)
    return shift_start <= current_time <= shift_end


def to_local_datetime(value: datetime | str | None) -> datetime | None:
    """Parse a server timestamp and convert it to the application timezone.

    Legacy API values without an offset were historically UTC, so they remain
    interpreted as UTC instead of inheriting the workstation timezone.
    """

    if value is None or value == "":
        return None
    try:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(APP_TIMEZONE)

