from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, or_

from app.core.config import get_settings
from app.database.session import SessionLocal
from app.models.entities import IdempotencyRecord, LoginSession


def cleanup_expired_records(now: datetime | None = None) -> dict[str, int]:
    """Bound growth of short-lived request and authentication records."""
    settings = get_settings()
    current = now or datetime.now(UTC)
    idempotency_cutoff = current - timedelta(hours=settings.idempotency_retention_hours)
    session_cutoff = current - timedelta(days=settings.login_session_retention_days)

    with SessionLocal.begin() as db:
        idempotency_result = db.execute(
            delete(IdempotencyRecord).where(IdempotencyRecord.created_at < idempotency_cutoff)
        )
        session_result = db.execute(
            delete(LoginSession).where(
                or_(
                    LoginSession.expires_at < session_cutoff,
                    LoginSession.revoked_at < session_cutoff,
                )
            )
        )
    return {
        "idempotency_records": idempotency_result.rowcount,
        "login_sessions": session_result.rowcount,
    }
