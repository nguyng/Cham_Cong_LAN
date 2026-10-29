"""Nạp bộ dữ liệu DEMO có thể chạy lặp lại cho SQLite cục bộ."""

import argparse
import os
import sqlite3
import sys
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_ROOT = ROOT / "server"


def configure_console_encoding():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            continue


def arguments():
    parser = argparse.ArgumentParser(description="Nạp dữ liệu DEMO cho LAN Attendance")
    parser.add_argument(
        "--database",
        type=Path,
        default=ROOT / "dist_portable" / "AttendanceServer" / "data" / "attendance.db",
        help="Đường dẫn SQLite cần nạp dữ liệu",
    )
    parser.add_argument(
        "--skip-backups",
        action="store_true",
        help="Không tạo 5 bản sao lưu DEMO",
    )
    return parser.parse_args()


def prepare_runtime(database_path: Path):
    database_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite:///{database_path.resolve().as_posix()}"
    os.environ["DATABASE_URL"] = database_url
    os.environ["ENVIRONMENT"] = "development"
    os.environ.setdefault("JWT_SECRET", "demo-seed-local-secret-at-least-32-characters")
    sys.path.insert(0, str(SERVER_ROOT))

    from alembic import command
    from alembic.config import Config

    config = Config(str(SERVER_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(SERVER_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")


def seed(database_path: Path):
    from app.core.security import hash_password, hash_token
    from app.database.session import SessionLocal
    from app.models.entities import (
        AttendanceAdjustment,
        AttendanceRecord,
        AttendanceStatus,
        AuditLog,
        Department,
        Device,
        Employee,
        LeaveBalance,
        LeaveRequest,
        LeaveType,
        LoginSession,
        Notification,
        Permission,
        Position,
        RandomCheck,
        RequestStatus,
        Role,
        RoleName,
        RolePermission,
        SecurityAlert,
        Shift,
        ShiftAssignment,
        SystemSetting,
        User,
    )
    from sqlalchemy import select

    now = datetime.now(UTC)
    today = date.today()

    def upsert(db, model, filters, values):
        item = db.scalar(select(model).filter_by(**filters))
        if item is None:
            item = model(**filters, **values)
            db.add(item)
            db.flush()
        else:
            for key, value in values.items():
                setattr(item, key, value)
            db.flush()
        return item

    with SessionLocal.begin() as db:
        roles = {}
        for role_name in RoleName:
            roles[role_name] = upsert(
                db,
                Role,
                {"name": role_name},
                {"description": f"Vai trò {role_name.value} dùng cho hệ thống"},
            )

        department_data = [
            ("DEMO-HC", "Hành chính - Nhân sự"),
            ("DEMO-KT", "Kế toán"),
            ("DEMO-KD", "Kinh doanh"),
            ("DEMO-CN", "Công nghệ"),
            ("DEMO-VH", "Vận hành"),
        ]
        departments = [
            upsert(
                db,
                Department,
                {"code": code},
                {"name": name, "active": True},
            )
            for code, name in department_data
        ]

        position_data = [
            ("DEMO-NV", "Nhân viên"),
            ("DEMO-CV", "Chuyên viên"),
            ("DEMO-TP", "Trưởng phòng"),
            ("DEMO-GS", "Giám sát"),
            ("DEMO-KTV", "Kỹ thuật viên"),
        ]
        positions = [
            upsert(db, Position, {"code": code}, {"name": name, "active": True})
            for code, name in position_data
        ]

        shift_data = [
            ("DEMO-HC", "Hành chính", time(8), time(17), 60, 10, 10),
            ("DEMO-S1", "Ca sáng", time(7), time(15), 45, 5, 5),
            ("DEMO-S2", "Ca chiều", time(15), time(23), 45, 5, 5),
            ("DEMO-D1", "Ca đêm", time(22), time(6), 60, 10, 10),
            ("DEMO-LH", "Ca linh hoạt", time(9), time(18), 60, 15, 15),
        ]
        shifts = [
            upsert(
                db,
                Shift,
                {"code": code},
                {
                    "name": name,
                    "start_time": start,
                    "end_time": end,
                    "break_minutes": break_minutes,
                    "late_grace_minutes": late_grace,
                    "early_grace_minutes": early_grace,
                    "active": True,
                },
            )
            for code, name, start, end, break_minutes, late_grace, early_grace in shift_data
        ]

        employee_data = [
            (
                "DEMO001",
                "Quản trị Demo",
                "demo.admin@company.local",
                "demo_admin",
                "AdminDemo@123",
                RoleName.ADMIN,
                0,
                2,
            ),
            (
                "DEMO002",
                "Quản lý Demo",
                "demo.manager@company.local",
                "demo_manager",
                "ManagerDemo@123",
                RoleName.MANAGER,
                1,
                2,
            ),
            (
                "DEMO003",
                "Nguyễn An",
                "demo.nv01@company.local",
                "demo_nv01",
                "EmployeeDemo@123",
                RoleName.EMPLOYEE,
                1,
                0,
            ),
            (
                "DEMO004",
                "Trần Bình",
                "demo.nv02@company.local",
                "demo_nv02",
                "EmployeeDemo@123",
                RoleName.EMPLOYEE,
                3,
                4,
            ),
            (
                "DEMO005",
                "Lê Chi",
                "demo.nv03@company.local",
                "demo_nv03",
                "EmployeeDemo@123",
                RoleName.EMPLOYEE,
                4,
                3,
            ),
        ]
        employees = []
        users = []
        for index, (
            employee_code,
            full_name,
            email,
            username,
            password,
            role_name,
            department_index,
            position_index,
        ) in enumerate(employee_data):
            employee = upsert(
                db,
                Employee,
                {"employee_code": employee_code},
                {
                    "full_name": full_name,
                    "email": email,
                    "phone": f"09000000{index + 1:02d}",
                    "department_id": departments[department_index].id,
                    "position_id": positions[position_index].id,
                    "hire_date": today - timedelta(days=365 + index * 90),
                    "active": True,
                },
            )
            user = upsert(
                db,
                User,
                {"username": username},
                {
                    "password_hash": hash_password(password),
                    "role_id": roles[role_name].id,
                    "employee_id": employee.id,
                    "active": True,
                    "failed_login_count": 0,
                    "locked_until": None,
                },
            )
            employees.append(employee)
            users.append(user)

        departments[1].manager_employee_id = employees[1].id

        permission_data = [
            ("DEMO_ATTENDANCE_VIEW", "Xem dữ liệu chấm công"),
            ("DEMO_ATTENDANCE_REVIEW", "Duyệt điều chỉnh chấm công"),
            ("DEMO_LEAVE_REVIEW", "Duyệt nghỉ phép"),
            ("DEMO_REPORT_EXPORT", "Xuất báo cáo"),
            ("DEMO_SYSTEM_ADMIN", "Quản trị hệ thống"),
        ]
        permissions = [
            upsert(db, Permission, {"code": code}, {"description": description})
            for code, description in permission_data
        ]
        for permission in permissions:
            if db.get(RolePermission, (roles[RoleName.ADMIN].id, permission.id)) is None:
                db.add(
                    RolePermission(
                        role_id=roles[RoleName.ADMIN].id,
                        permission_id=permission.id,
                    )
                )

        devices = []
        for index, employee in enumerate(employees):
            fingerprint_hash = hash_token(f"DEMO-DEVICE-FINGERPRINT-{index + 1:02d}")
            devices.append(
                upsert(
                    db,
                    Device,
                    {"fingerprint_hash": fingerprint_hash},
                    {
                        "employee_id": employee.id,
                        "device_name": f"DEMO-PC-{index + 1:02d}",
                        "approved": index != 4,
                        "active": True,
                        "last_ip": f"127.0.0.{index + 1}",
                        "last_seen_at": now - timedelta(minutes=index * 15),
                    },
                )
            )

        attendance_statuses = [
            AttendanceStatus.ON_TIME,
            AttendanceStatus.LATE,
            AttendanceStatus.EARLY_LEAVE,
            AttendanceStatus.LATE_AND_EARLY,
            AttendanceStatus.OPEN,
        ]
        attendances = []
        assignments = []
        for index, (employee, shift, device) in enumerate(
            zip(employees, shifts, devices, strict=False)
        ):
            work_date = today - timedelta(days=4 - index)
            assignment = upsert(
                db,
                ShiftAssignment,
                {"employee_id": employee.id, "work_date": work_date},
                {"shift_id": shift.id},
            )
            check_in = datetime.combine(work_date, shift.start_time, tzinfo=UTC) + timedelta(
                minutes=(0, 22, 0, 18, 3)[index]
            )
            check_out = None
            if index < 4:
                end_date = work_date + timedelta(
                    days=1 if shift.end_time <= shift.start_time else 0
                )
                check_out = datetime.combine(end_date, shift.end_time, tzinfo=UTC) - timedelta(
                    minutes=(0, 0, 35, 25, 0)[index]
                )
            attendance = upsert(
                db,
                AttendanceRecord,
                {
                    "employee_id": employee.id,
                    "work_date": work_date,
                    "shift_id": shift.id,
                },
                {
                    "check_in_at": check_in,
                    "check_out_at": check_out,
                    "check_in_ip": f"127.0.0.{index + 1}",
                    "check_out_ip": f"127.0.0.{index + 1}" if check_out else None,
                    "device_id": device.id,
                    "status": attendance_statuses[index],
                    "late_minutes": (0, 22, 0, 18, 0)[index],
                    "early_leave_minutes": (0, 0, 35, 25, 0)[index],
                    "worked_minutes": (480, 458, 445, 437, 0)[index],
                    "break_minutes": shift.break_minutes,
                    "suspicious": index == 3,
                },
            )
            assignments.append(assignment)
            attendances.append(attendance)

        adjustment_statuses = [
            RequestStatus.PENDING,
            RequestStatus.APPROVED,
            RequestStatus.REJECTED,
            RequestStatus.PENDING,
            RequestStatus.PENDING,
        ]
        for index, (attendance, user) in enumerate(zip(attendances, users, strict=False)):
            status = adjustment_statuses[index]
            upsert(
                db,
                AttendanceAdjustment,
                {"attendance_id": attendance.id, "reason": f"DEMO-ADJUSTMENT-{index + 1:02d}"},
                {
                    "requested_by": user.id,
                    "proposed_check_in": attendance.check_in_at - timedelta(minutes=5),
                    "proposed_check_out": attendance.check_out_at,
                    "status": status,
                    "reviewed_by": users[0].id if status != RequestStatus.PENDING else None,
                    "review_note": "Dữ liệu mẫu đã xử lý"
                    if status != RequestStatus.PENDING
                    else None,
                    "reviewed_at": now if status != RequestStatus.PENDING else None,
                },
            )

        leave_type_data = [
            ("DEMO-AL", "Phép năm", True, True),
            ("DEMO-SL", "Nghỉ ốm", True, True),
            ("DEMO-UL", "Nghỉ không lương", False, False),
            ("DEMO-WL", "Nghỉ cưới", True, False),
            ("DEMO-ML", "Nghỉ thai sản", True, False),
        ]
        leave_types = [
            upsert(
                db,
                LeaveType,
                {"code": code},
                {
                    "name": name,
                    "paid": paid,
                    "deduct_balance": deduct_balance,
                    "active": True,
                },
            )
            for code, name, paid, deduct_balance in leave_type_data
        ]

        leave_statuses = [
            RequestStatus.PENDING,
            RequestStatus.APPROVED,
            RequestStatus.REJECTED,
            RequestStatus.PENDING,
            RequestStatus.APPROVED,
        ]
        for index, (employee, leave_type) in enumerate(zip(employees, leave_types, strict=False)):
            used_days = (
                Decimal("1") if leave_statuses[index] == RequestStatus.APPROVED else Decimal("0")
            )
            upsert(
                db,
                LeaveBalance,
                {
                    "employee_id": employee.id,
                    "leave_type_id": leave_type.id,
                    "year": today.year,
                },
                {
                    "allocated_days": Decimal(str((12, 10, 5, 3, 180)[index])),
                    "used_days": used_days,
                },
            )
            start_date = today + timedelta(days=7 + index * 3)
            status = leave_statuses[index]
            upsert(
                db,
                LeaveRequest,
                {"employee_id": employee.id, "reason": f"DEMO-LEAVE-{index + 1:02d}"},
                {
                    "leave_type_id": leave_type.id,
                    "start_date": start_date,
                    "end_date": start_date,
                    "days": Decimal("1"),
                    "status": status,
                    "reviewed_by": users[0].id if status != RequestStatus.PENDING else None,
                    "review_note": "Đơn mẫu đã xử lý" if status != RequestStatus.PENDING else None,
                    "reviewed_at": now if status != RequestStatus.PENDING else None,
                },
            )

        random_results = ["VERIFIED", "MISSED", "PENDING", "UNVERIFIED", "VERIFIED"]
        for index, employee in enumerate(employees):
            sent_at = now - timedelta(hours=index + 1)
            result = random_results[index]
            upsert(
                db,
                RandomCheck,
                {"challenge_token_hash": hash_token(f"DEMO-RANDOM-CHECK-{index + 1:02d}")},
                {
                    "employee_id": employee.id,
                    "attendance_id": attendances[index].id,
                    "sent_at": sent_at,
                    "expires_at": now + timedelta(minutes=3)
                    if result == "PENDING"
                    else sent_at + timedelta(minutes=3),
                    "responded_at": sent_at + timedelta(minutes=1)
                    if result == "VERIFIED"
                    else None,
                    "result": result,
                    "response_ip": f"127.0.0.{index + 1}" if result == "VERIFIED" else None,
                },
            )

        alert_data = [
            ("DEMO_CONCURRENT_LOGIN", "MEDIUM", "Phát hiện phiên đăng nhập đồng thời"),
            ("DEMO_RANDOM_CHECK_MISSED", "HIGH", "Không phản hồi Random Check đúng hạn"),
            ("DEMO_NEW_DEVICE", "LOW", "Đăng nhập từ thiết bị mới"),
            ("DEMO_UNUSUAL_IP", "MEDIUM", "Địa chỉ IP cần quản trị viên kiểm tra"),
            ("DEMO_ATTENDANCE", "HIGH", "Bản ghi chấm công có dấu hiệu bất thường"),
        ]
        alert_statuses = ["OPEN", "OPEN", "CONFIRMED", "DISMISSED", "OPEN"]
        for index, (alert_type, severity, description) in enumerate(alert_data):
            status = alert_statuses[index]
            upsert(
                db,
                SecurityAlert,
                {"alert_type": alert_type, "employee_id": employees[index].id},
                {
                    "severity": severity,
                    "description": f"DEMO-ALERT-{index + 1:02d}: {description}",
                    "evidence": {"source": "demo_seed", "sample": index + 1},
                    "status": status,
                    "resolved_by": users[0].id if status != "OPEN" else None,
                    "resolution_note": "Cảnh báo mẫu đã được xem xét" if status != "OPEN" else None,
                    "resolved_at": now if status != "OPEN" else None,
                },
            )

        notification_data = [
            ("Chào mừng", "Tài khoản DEMO đã sẵn sàng", "SYSTEM"),
            ("Phân ca mới", "Bạn đã được phân ca làm việc", "SHIFT"),
            ("Kết quả nghỉ phép", "Đơn nghỉ phép mẫu đã được duyệt", "LEAVE"),
            ("Nhắc chấm công", "Vui lòng kiểm tra trạng thái check-out", "ATTENDANCE"),
            ("Xác minh thiết bị", "Thiết bị DEMO đang chờ phê duyệt", "SECURITY"),
        ]
        for index, (title, message, category) in enumerate(notification_data):
            upsert(
                db,
                Notification,
                {"user_id": users[index].id, "title": f"DEMO-{index + 1:02d}: {title}"},
                {
                    "message": message,
                    "category": category,
                    "read_at": now if index in (0, 2) else None,
                },
            )

        setting_data = [
            ("demo.company_name", {"text": "Công ty DEMO"}, "Tên đơn vị thử nghiệm"),
            ("demo.work_timezone", {"value": "Asia/Ho_Chi_Minh"}, "Múi giờ làm việc"),
            ("demo.random_check", {"enabled": True, "minutes": 120}, "Cấu hình Random Check"),
            ("demo.attendance", {"allow_early_check_in": 30}, "Cấu hình chấm công"),
            ("demo.notification", {"desktop": True}, "Cấu hình thông báo"),
        ]
        for key, value, description in setting_data:
            upsert(
                db,
                SystemSetting,
                {"key": key},
                {"value": value, "description": description, "updated_by": users[0].id},
            )

        for index, user in enumerate(users):
            action = f"DEMO_SEED_ACTION_{index + 1:02d}"
            audit = db.scalar(select(AuditLog).where(AuditLog.action == action))
            if audit is None:
                db.add(
                    AuditLog(
                        user_id=user.id,
                        action=action,
                        entity_type="DEMO",
                        entity_id=str(employees[index].id),
                        client_ip=f"127.0.0.{index + 1}",
                        after_data={"seed": True, "sample": index + 1},
                    )
                )

            session_id = f"demo-session-{index + 1:02d}"
            upsert(
                db,
                LoginSession,
                {"id": session_id},
                {
                    "user_id": user.id,
                    "token_hash": hash_token(f"DEMO-SESSION-TOKEN-{index + 1:02d}"),
                    "client_ip": f"127.0.0.{index + 1}",
                    "device_fingerprint": f"DEMO-DEVICE-{index + 1:02d}",
                    "expires_at": now + timedelta(days=1),
                    "revoked_at": now,
                    "last_seen_at": now - timedelta(minutes=index),
                },
            )

        summary_models = {
            "Phòng ban": Department,
            "Chức vụ": Position,
            "Ca làm": Shift,
            "Nhân viên DEMO": Employee,
            "Tài khoản DEMO": User,
            "Phân ca": ShiftAssignment,
            "Chấm công": AttendanceRecord,
            "Điều chỉnh công": AttendanceAdjustment,
            "Loại nghỉ phép": LeaveType,
            "Quỹ phép": LeaveBalance,
            "Đơn nghỉ phép": LeaveRequest,
            "Thiết bị": Device,
            "Random Check": RandomCheck,
            "Cảnh báo": SecurityAlert,
            "Thông báo": Notification,
            "Cấu hình DEMO": SystemSetting,
            "Nhật ký DEMO": AuditLog,
        }
        db.flush()
        summary = {}
        for label, model in summary_models.items():
            if model is Employee:
                summary[label] = len(
                    db.scalars(select(Employee).where(Employee.employee_code.like("DEMO%"))).all()
                )
            elif model is User:
                summary[label] = len(
                    db.scalars(select(User).where(User.username.like("demo_%"))).all()
                )
            elif model is SystemSetting:
                summary[label] = len(
                    db.scalars(select(SystemSetting).where(SystemSetting.key.like("demo.%"))).all()
                )
            elif model is AuditLog:
                summary[label] = len(
                    db.scalars(select(AuditLog).where(AuditLog.action.like("DEMO_SEED%"))).all()
                )
            else:
                summary[label] = len(db.scalars(select(model)).all())

    return summary


def create_demo_backups(database_path: Path):
    backup_directory = database_path.parent.parent / "backups"
    backup_directory.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database_path) as source:
        for index in range(1, 6):
            target_path = backup_directory / f"attendance_demo_{index:02d}.sqlite3"
            if target_path.exists():
                target_path.unlink()
            with sqlite3.connect(target_path) as target:
                source.backup(target)
    return backup_directory


def main():
    configure_console_encoding()
    options = arguments()
    database_path = options.database.resolve()
    prepare_runtime(database_path)
    summary = seed(database_path)
    backup_directory = None
    if not options.skip_backups:
        backup_directory = create_demo_backups(database_path)

    print("\nĐÃ NẠP DỮ LIỆU DEMO THÀNH CÔNG")
    print(f"Database: {database_path}")
    for label, count in summary.items():
        print(f"- {label}: {count}")
    if backup_directory:
        print(f"- Bản sao lưu DEMO: 5 ({backup_directory})")
    print("\nTÀI KHOẢN KIỂM THỬ")
    print("- Admin:    demo_admin / AdminDemo@123")
    print("- Manager:  demo_manager / ManagerDemo@123")
    print("- Employee: demo_nv01 / EmployeeDemo@123")
    print("- Employee: demo_nv02 / EmployeeDemo@123")
    print("- Employee: demo_nv03 / EmployeeDemo@123")


if __name__ == "__main__":
    main()
