import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.database.sqlite import sqlite_database_path


def _backup_path() -> Path:
    directory = Path(get_settings().backup_directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S_%fZ")
    return directory / f"attendance_{stamp}.sqlite3"


def backup_database() -> Path:
    database_path = sqlite_database_path(get_settings().database_url)
    if database_path == Path(":memory:"):
        raise ValueError("Không thể sao lưu database SQLite in-memory")
    target = _backup_path()
    source = sqlite3.connect(database_path, timeout=30)
    destination = sqlite3.connect(target, timeout=30)
    try:
        source.backup(destination)
        result = destination.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"Bản sao lưu SQLite không toàn vẹn: {result}")
    finally:
        destination.close()
        source.close()
    return target


def restore_database(backup_file: Path):
    settings = get_settings()
    allowed_dir = Path(settings.backup_directory).resolve()
    source = backup_file.resolve()
    if allowed_dir not in source.parents or not source.is_file():
        raise ValueError("Tệp khôi phục phải nằm trong thư mục backup đã cấu hình")
    destination_path = sqlite_database_path(settings.database_url)
    if destination_path == Path(":memory:"):
        raise ValueError("Không thể khôi phục database SQLite in-memory")
    source_connection = sqlite3.connect(f"file:{source}?mode=ro", uri=True, timeout=30)
    destination_connection = sqlite3.connect(destination_path, timeout=30)
    try:
        integrity = source_connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"Tệp backup SQLite không toàn vẹn: {integrity}")
        source_connection.backup(destination_connection)
        destination_connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        destination_connection.close()
        source_connection.close()
