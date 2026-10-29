from pathlib import Path


def sqlite_database_path(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Hệ thống được cấu hình chỉ sử dụng SQLite")
    raw_path = database_url.removeprefix("sqlite:///")
    if raw_path == ":memory:":
        return Path(":memory:")
    return Path(raw_path).expanduser().resolve()
