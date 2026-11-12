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
        attendance_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(attendance_records)")
        }
        employee_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(employees)")
        }
        revision = connection.execute("select version_num from alembic_version").fetchone()[0]
    assert "users" in tables
    assert "attendance_records" in tables
    assert "check_in_geofence_distance_meters" in attendance_columns
    assert "overtime_status" in attendance_columns
    assert "overtime_multiplier" in employee_columns
    assert revision == "20261113_0006"


def test_launcher_migrates_legacy_device_uniqueness_without_data_loss():
    database = Path(".test-runtime") / f"legacy-device-{uuid4()}" / "attendance.db"
    database.parent.mkdir(parents=True)
    with sqlite3.connect(database) as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE employees (id INTEGER PRIMARY KEY);
            CREATE TABLE devices (
                id INTEGER PRIMARY KEY,
                employee_id INTEGER NOT NULL REFERENCES employees(id),
                fingerprint_hash VARCHAR(128) NOT NULL UNIQUE,
                device_name VARCHAR(160) NOT NULL,
                approved BOOLEAN NOT NULL DEFAULT 0,
                active BOOLEAN NOT NULL DEFAULT 1,
                last_ip VARCHAR(64),
                last_seen_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
            );
            CREATE INDEX ix_devices_employee_id ON devices(employee_id);
            CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY);
            INSERT INTO alembic_version VALUES ('20261030_0002');
            INSERT INTO employees(id) VALUES (1), (2);
            INSERT INTO devices(id, employee_id, fingerprint_hash, device_name)
            VALUES (1, 1, 'shared-fingerprint', 'Máy cũ');
            """
        )

    run_migrations(f"sqlite:///{database.as_posix()}")

    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO devices(employee_id, fingerprint_hash, device_name) VALUES (?, ?, ?)",
            (2, "shared-fingerprint", "Máy dùng chung"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO devices(employee_id, fingerprint_hash, device_name) VALUES (?, ?, ?)",
                (1, "shared-fingerprint", "Bản ghi trùng"),
            )
        count = connection.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert count == 2
    assert revision == "20261113_0006"


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
