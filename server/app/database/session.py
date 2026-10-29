from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings
from app.database.sqlite import sqlite_database_path


class Base(DeclarativeBase):
    """Shared SQLAlchemy declarative base."""


def make_engine(url: str | None = None):
    database_url = url or get_settings().database_url
    if not database_url.startswith("sqlite:///"):
        raise ValueError("DATABASE_URL phải sử dụng SQLite (sqlite:///...)")
    database_path = sqlite_database_path(database_url)
    if database_path != Path(":memory:"):
        database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def configure_sqlite(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    return engine


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
