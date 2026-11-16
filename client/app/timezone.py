"""Timezone helpers shared by the desktop client.

The attendance system has one business timezone.  Keeping the conversion here
prevents the Windows timezone of an individual workstation from changing dates
or times shown by the application.
"""

from datetime import UTC, date, datetime, timedelta, timezone
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

