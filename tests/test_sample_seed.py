import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from scripts import seed_sample_data

ROOT = Path(__file__).resolve().parents[1]


def test_seed_default_targets_source_server_database(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["seed_sample_data.py"])
    options = seed_sample_data.arguments()
    assert options.database == ROOT / "server" / "data" / "attendance.db"


def test_seed_data_is_repeatable_and_creates_five_samples():
    runtime_directory = ROOT / ".test-runtime"
    runtime_directory.mkdir(exist_ok=True)
    database = runtime_directory / f"attendance-sample-{uuid4().hex}.db"
    command = [
        sys.executable,
        str(ROOT / "scripts" / "seed_sample_data.py"),
        "--database",
        str(database),
        "--skip-backups",
    ]

    queries = {
        "departments": "SELECT COUNT(*) FROM departments WHERE code IN ('PB01','PB02','PB03','PB04','PB05')",
        "positions": "SELECT COUNT(*) FROM positions WHERE code IN ('CV01','CV02','CV03','CV04','CV05')",
        "shifts": "SELECT COUNT(*) FROM shifts WHERE code IN ('CA01','CA02','CA03','CA04','CA05')",
        "employees": "SELECT COUNT(*) FROM employees WHERE employee_code IN ('NV001','NV002','NV003','NV004','NV005')",
        "users": "SELECT COUNT(*) FROM users WHERE username IN ('admin','manage','user1','user2','user3')",
        "root_admin": "SELECT COUNT(*) FROM users WHERE username = 'admin' AND is_root_admin = 1",
        "permissions": "SELECT COUNT(*) FROM permissions WHERE code IN ('ATTENDANCE_VIEW','ATTENDANCE_REVIEW','LEAVE_REVIEW','REPORT_EXPORT','SYSTEM_ADMIN')",
        "assignments": (
            "SELECT COUNT(*) FROM shift_assignments sa "
            "JOIN employees e ON e.id = sa.employee_id WHERE e.employee_code LIKE 'NV00%'"
        ),
        "attendance": (
            "SELECT COUNT(*) FROM attendance_records ar "
            "JOIN employees e ON e.id = ar.employee_id WHERE e.employee_code LIKE 'NV00%'"
        ),
        "adjustments": "SELECT COUNT(*) FROM attendance_adjustments WHERE reason LIKE 'Điều chỉnh công #%'",
        "leave_types": "SELECT COUNT(*) FROM leave_types WHERE code IN ('PN','OM','KLUONG','CUOI','TS')",
        "leave_balances": (
            "SELECT COUNT(*) FROM leave_balances lb "
            "JOIN employees e ON e.id = lb.employee_id WHERE e.employee_code LIKE 'NV00%'"
        ),
        "leave_requests": "SELECT COUNT(*) FROM leave_requests WHERE reason LIKE 'Lý do nghỉ phép #%'",
        "devices": "SELECT COUNT(*) FROM devices WHERE device_name LIKE 'PC-%'",
        "random_checks": (
            "SELECT COUNT(*) FROM random_checks rc "
            "JOIN employees e ON e.id = rc.employee_id WHERE e.employee_code LIKE 'NV00%'"
        ),
        "alerts": "SELECT COUNT(*) FROM security_alerts WHERE employee_id IN (SELECT id FROM employees WHERE employee_code LIKE 'NV00%')",
        "notifications": "SELECT COUNT(*) FROM notifications WHERE user_id IN (SELECT id FROM users WHERE username IN ('admin','manage','user1','user2','user3'))",
        "settings": "SELECT COUNT(*) FROM system_settings WHERE key IN ('company.name','work.timezone','random_check.policy','attendance.policy','notification.policy')",
        "audit_logs": "SELECT COUNT(*) FROM audit_logs WHERE action LIKE 'SEED_DATA%'",
        "sessions": (
            "SELECT COUNT(*) FROM login_sessions ls "
            "JOIN users u ON u.id = ls.user_id "
            "WHERE u.username IN ('admin','manage','user1','user2','user3')"
        ),
    }
    try:
        first = subprocess.run(
            command, cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        second = subprocess.run(
            command, cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
        )

        assert "ĐÃ NẠP DỮ LIỆU KIỂM THỬ THÀNH CÔNG" in first.stdout
        assert "- Chấm công: 5" in second.stdout

        with closing(sqlite3.connect(database)) as connection:
            counts = {
                name: connection.execute(query).fetchone()[0] for name, query in queries.items()
            }
            first_attendance = connection.execute(
                "SELECT ar.check_in_at, ar.check_out_at, ar.worked_minutes, ar.break_minutes "
                "FROM attendance_records ar "
                "JOIN employees e ON e.id = ar.employee_id "
                "WHERE e.employee_code = 'NV001'"
            ).fetchone()

        assert counts == {**dict.fromkeys(queries, 5), "root_admin": 1}
        check_in = datetime.fromisoformat(first_attendance[0]).replace(tzinfo=UTC)
        check_out = datetime.fromisoformat(first_attendance[1]).replace(tzinfo=UTC)
        local_check_in = check_in.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
        assert local_check_in.hour == 8
        assert local_check_in.utcoffset() == timedelta(hours=7)
        assert first_attendance[2] == int((check_out - check_in).total_seconds() // 60) - first_attendance[3]

        with closing(sqlite3.connect(database)) as connection:
            connection.execute(
                "UPDATE employees SET full_name = ? WHERE employee_code = 'NV001'",
                ("Dữ liệu cần giữ nguyên",),
            )
            connection.commit()
        skipped = subprocess.run(
            [*command, "--if-empty"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        with closing(sqlite3.connect(database)) as connection:
            preserved_name = connection.execute(
                "SELECT full_name FROM employees WHERE employee_code = 'NV001'"
            ).fetchone()[0]
        assert "bỏ qua dữ liệu mẫu" in skipped.stdout
        assert preserved_name == "Dữ liệu cần giữ nguyên"
    finally:
        for suffix in ("", "-shm", "-wal"):
            database.with_name(database.name + suffix).unlink(missing_ok=True)
