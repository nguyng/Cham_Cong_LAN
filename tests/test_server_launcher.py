import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from app.core.security import verify_password
from app.database.session import SessionLocal
from app.models.entities import User
from app.services.bootstrap import create_initial_admin

from server_launcher import run_migrations


def test_launcher_migrates_a_new_sqlite_database():
    database = Path(".test-runtime") / f"migration-{uuid4()}" / "attendance.db"
    run_migrations(f"sqlite:///{database.as_posix()}")

    assert database.is_file()
    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "select name from sqlite_master where type = 'table'"
            ).fetchall()
        }
        revision = connection.execute("select version_num from alembic_version").fetchone()[0]
    assert "users" in tables
    assert "attendance_records" in tables
    assert revision == "20261030_0002"


def test_packaged_bootstrap_creates_admin_without_plaintext_password():
    with SessionLocal.begin() as db:
        user = create_initial_admin(
            db,
            username="packaged-admin",
            employee_code="AD999",
            full_name="Quản trị đóng gói",
            email="packaged-admin@example.local",
            password="PackagedAdmin123!",
        )
        user_id = user.id
    with SessionLocal() as db:
        stored = db.get(User, user_id)
        assert stored.password_hash != "PackagedAdmin123!"
        assert verify_password("PackagedAdmin123!", stored.password_hash)
        with pytest.raises(ValueError, match="Username đã tồn tại"):
            create_initial_admin(
                db,
                username="packaged-admin",
                employee_code="AD998",
                full_name="Trùng tài khoản",
                email="packaged-admin-2@example.local",
                password="PackagedAdmin123!",
            )
