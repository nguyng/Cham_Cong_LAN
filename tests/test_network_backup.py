import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.services.backup import backup_database, restore_database


def test_multiple_clients_health(client):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: client.get("/api/v1/health").status_code, range(20)))
    assert results == [200] * 20


def test_sqlite_backup_is_real_database_copy():
    path = backup_database()
    assert path.exists()
    assert path.stat().st_size > 0
    path.unlink()


def test_sqlite_restore_round_trip(monkeypatch):
    import app.services.backup as backup_module

    runtime_dir = Path(".test-runtime") / str(uuid4())
    database = runtime_dir / "source.sqlite3"
    backup_dir = runtime_dir / "backups"
    backup_dir.mkdir(parents=True)
    with sqlite3.connect(database) as connection:
        connection.execute("create table sample(value text)")
        connection.execute("insert into sample values ('before')")
    settings = SimpleNamespace(database_url=f"sqlite:///{database}", backup_directory=str(backup_dir))
    monkeypatch.setattr(backup_module, "get_settings", lambda: settings)
    saved = backup_module.backup_database()
    with sqlite3.connect(database) as connection:
        connection.execute("update sample set value='after'")
    restore_database(saved)
    with sqlite3.connect(database) as connection:
        assert connection.execute("select value from sample").fetchone()[0] == "before"
