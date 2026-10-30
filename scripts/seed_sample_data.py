"""Nạp bộ dữ liệu kiểm thử trung tính có thể chạy lặp lại cho SQLite cục bộ."""

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
    parser = argparse.ArgumentParser(description="Nạp dữ liệu kiểm thử cho LAN Attendance")
    parser.add_argument(
        "--database",
        type=Path,
        default=ROOT / "dist_portable" / "AttendanceServer" / "data" / "attendance.db",
        help="Đường dẫn SQLite cần nạp dữ liệu",
    )
    parser.add_argument(
        "--skip-backups",
        action="store_true",
        help="Không tạo 5 bản sao lưu kiểm thử",
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
    from sqlalchemy import delete, select, update

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

    def rename_legacy(db, model, field_name, old_value, new_value):
        field = getattr(model, field_name)
        legacy = db.scalar(select(model).where(field == old_value))
        current = db.scalar(select(model).where(field == new_value))
        if legacy is not None and current is None:
            setattr(legacy, field_name, new_value)
            db.flush()

    with SessionLocal.begin() as db:
        roles = {}
        for role_name in RoleName:
            roles[role_name] = upsert(
                db,
                Role,
                {"name": role_name},
                {"description": f"Vai trò {role_name.value} dùng cho hệ thống"},
            )

        for old_code, new_code in zip(
            ("DEMO-HC", "DEMO-KT", "DEMO-KD", "DEMO-CN", "DEMO-VH"),
            ("PB01", "PB02", "PB03", "PB04", "PB05"),
            strict=True,
        ):
            rename_legacy(db, Department, "code", old_code, new_code)

        department_data = [
            ("PB01", "Hành chính - Nhân sự"),
            ("PB02", "Kế toán"),
            ("PB03", "Kinh doanh"),
            ("PB04", "Công nghệ"),
            ("PB05", "Vận hành"),
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

        for old_code, new_code in zip(
            ("DEMO-NV", "DEMO-CV", "DEMO-TP", "DEMO-GS", "DEMO-KTV"),
            ("CV01", "CV02", "CV03", "CV04", "CV05"),
            strict=True,
        ):
            rename_legacy(db, Position, "code", old_code, new_code)

        position_data = [
            ("CV01", "Nhân viên"),
            ("CV02", "Chuyên viên"),
            ("CV03", "Trưởng phòng"),
            ("CV04", "Giám sát"),
            ("CV05", "Kỹ thuật viên"),
        ]
        positions = [
            upsert(db, Position, {"code": code}, {"name": name, "active": True})
            for code, name in position_data
        ]

        for old_code, new_code in zip(
            ("DEMO-HC", "DEMO-S1", "DEMO-S2", "DEMO-D1", "DEMO-LH"),
            ("CA01", "CA02", "CA03", "CA04", "CA05"),
            strict=True,
        ):
            rename_legacy(db, Shift, "code", old_code, new_code)

        shift_data = [
            ("CA01", "Hành chính", time(8), time(17), 60, 10, 10),
            ("CA02", "Ca sáng", time(7), time(15), 45, 5, 5),
            ("CA03", "Ca chiều", time(15), time(23), 45, 5, 5),
            ("CA04", "Ca đêm", time(22), time(6), 60, 10, 10),
            ("CA05", "Ca linh hoạt", time(9), time(18), 60, 15, 15),
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

        for old_code, new_code in zip(
            ("DEMO001", "DEMO002", "DEMO003", "DEMO004", "DEMO005"),
            ("NV001", "NV002", "NV003", "NV004", "NV005"),
            strict=True,
        ):
            rename_legacy(db, Employee, "employee_code", old_code, new_code)

        existing_admin = db.scalar(select(User).where(User.username == "admin"))
        seeded_admin = db.scalar(select(User).where(User.username == "user1"))
        if (
            existing_admin
            and seeded_admin
            and seeded_admin.role.name == RoleName.ADMIN
            and existing_admin.id != seeded_admin.id
        ):
            seeded_employee = db.get(Employee, seeded_admin.employee_id)
            previous_admin_employee = db.get(Employee, existing_admin.employee_id)
            db.execute(
                update(AttendanceAdjustment)
                .where(AttendanceAdjustment.requested_by == seeded_admin.id)
                .values(requested_by=existing_admin.id)
            )
            db.execute(
                update(AttendanceAdjustment)
                .where(AttendanceAdjustment.reviewed_by == seeded_admin.id)
                .values(reviewed_by=existing_admin.id)
            )
            db.execute(
                update(LeaveRequest)
                .where(LeaveRequest.reviewed_by == seeded_admin.id)
                .values(reviewed_by=existing_admin.id)
            )
            db.execute(
                update(SecurityAlert)
                .where(SecurityAlert.resolved_by == seeded_admin.id)
                .values(resolved_by=existing_admin.id)
            )
            db.execute(
                update(Notification)
                .where(Notification.user_id == seeded_admin.id)
                .values(user_id=existing_admin.id)
            )
            db.execute(
                update(AuditLog)
                .where(AuditLog.user_id == seeded_admin.id)
                .values(user_id=existing_admin.id)
            )
            db.execute(
                update(SystemSetting)
                .where(SystemSetting.updated_by == seeded_admin.id)
                .values(updated_by=existing_admin.id)
            )
            db.execute(delete(LoginSession).where(LoginSession.user_id == seeded_admin.id))
            seeded_admin.employee_id = None
            db.flush()
            existing_admin.employee_id = seeded_employee.id
            db.delete(seeded_admin)
            if previous_admin_employee and previous_admin_employee.id != seeded_employee.id:
                previous_admin_employee.employee_code = f"ARCHIVE{previous_admin_employee.id:03d}"
                previous_admin_employee.email = (
                    f"archived.{previous_admin_employee.id}@company.local"
                )
                previous_admin_employee.active = False
            db.flush()

        desired_usernames = ("admin", "manage", "user1", "user2", "user3")
        if not all(
            db.scalar(select(User).where(User.username == username))
            for username in desired_usernames
        ):
            current_usernames = ("admin", "user2", "user3", "user4", "user5")
            legacy_usernames = (
                "demo_admin",
                "demo_manager",
                "demo_nv01",
                "demo_nv02",
                "demo_nv03",
            )
            temporary_usernames = tuple(f"__seed_account_{index}__" for index in range(1, 6))
            for index, temporary_username in enumerate(temporary_usernames):
                account = db.scalar(
                    select(User).where(User.username == current_usernames[index])
                ) or db.scalar(select(User).where(User.username == legacy_usernames[index]))
                if account:
                    account.username = temporary_username
            db.flush()
            for temporary_username, desired_username in zip(
                temporary_usernames, desired_usernames, strict=True
            ):
                account = db.scalar(select(User).where(User.username == temporary_username))
                if account:
                    account.username = desired_username
            db.flush()

        employee_data = [
            (
                "NV001",
                "Nguyễn Minh Anh",
                "admin@company.local",
                "admin",
                "123456",
                RoleName.ADMIN,
                0,
                2,
            ),
            (
                "NV002",
                "Trần Hoàng Nam",
                "manage@company.local",
                "manage",
                "123456",
                RoleName.MANAGER,
                1,
                2,
            ),
            (
                "NV003",
                "Nguyễn An",
                "user1@company.local",
                "user1",
                "123456",
                RoleName.EMPLOYEE,
                1,
                0,
            ),
            (
                "NV004",
                "Trần Bình",
                "user2@company.local",
                "user2",
                "123456",
                RoleName.EMPLOYEE,
                3,
                4,
            ),
            (
                "NV005",
                "Lê Chi",
                "user3@company.local",
                "user3",
                "123456",
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

        for old_code, new_code in zip(
            (
                "DEMO_ATTENDANCE_VIEW",
                "DEMO_ATTENDANCE_REVIEW",
                "DEMO_LEAVE_REVIEW",
                "DEMO_REPORT_EXPORT",
                "DEMO_SYSTEM_ADMIN",
            ),
            (
                "ATTENDANCE_VIEW",
                "ATTENDANCE_REVIEW",
                "LEAVE_REVIEW",
                "REPORT_EXPORT",
                "SYSTEM_ADMIN",
            ),
            strict=True,
        ):
            rename_legacy(db, Permission, "code", old_code, new_code)

        permission_data = [
            ("ATTENDANCE_VIEW", "Xem dữ liệu chấm công"),
            ("ATTENDANCE_REVIEW", "Duyệt điều chỉnh chấm công"),
            ("LEAVE_REVIEW", "Duyệt nghỉ phép"),
            ("REPORT_EXPORT", "Xuất báo cáo"),
            ("SYSTEM_ADMIN", "Quản trị hệ thống"),
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
            fingerprint_hash = hash_token(f"DEVICE-FINGERPRINT-{index + 1:02d}")
            rename_legacy(
                db,
                Device,
                "fingerprint_hash",
                hash_token(f"DEMO-DEVICE-FINGERPRINT-{index + 1:02d}"),
                fingerprint_hash,
            )
            devices.append(
                upsert(
                    db,
                    Device,
                    {"fingerprint_hash": fingerprint_hash},
                    {
                        "employee_id": employee.id,
                        "device_name": f"PC-{index + 1:02d}",
                        "approved": index != 4,
                        "active": True,
                        "last_ip": f"127.0.0.{index + 1}",
                        "last_seen_at": now - timedelta(minutes=index * 15),
                    },
                )
            )

        # Các bản ghi vận hành thay đổi theo ngày. Xóa riêng dữ liệu phát sinh của
        # năm tài khoản kiểm thử để chạy script ở ngày khác vẫn luôn có 5 mẫu.
        demo_employee_ids = [employee.id for employee in employees]
        demo_attendance_ids = select(AttendanceRecord.id).where(
            AttendanceRecord.employee_id.in_(demo_employee_ids)
        )
        db.execute(delete(RandomCheck).where(RandomCheck.employee_id.in_(demo_employee_ids)))
        db.execute(
            delete(AttendanceAdjustment).where(
                AttendanceAdjustment.attendance_id.in_(demo_attendance_ids)
            )
        )
        db.execute(
            delete(AttendanceRecord).where(AttendanceRecord.employee_id.in_(demo_employee_ids))
        )
        db.execute(
            delete(ShiftAssignment).where(ShiftAssignment.employee_id.in_(demo_employee_ids))
        )
        db.flush()

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
                {"attendance_id": attendance.id, "reason": f"Điều chỉnh công #{index + 1:02d}"},
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

        for old_code, new_code in zip(
            ("DEMO-AL", "DEMO-SL", "DEMO-UL", "DEMO-WL", "DEMO-ML"),
            ("PN", "OM", "KLUONG", "CUOI", "TS"),
            strict=True,
        ):
            rename_legacy(db, LeaveType, "code", old_code, new_code)

        leave_type_data = [
            ("PN", "Phép năm", True, True),
            ("OM", "Nghỉ ốm", True, True),
            ("KLUONG", "Nghỉ không lương", False, False),
            ("CUOI", "Nghỉ cưới", True, False),
            ("TS", "Nghỉ thai sản", True, False),
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
            reason = f"Lý do nghỉ phép #{index + 1:02d}"
            rename_legacy(
                db,
                LeaveRequest,
                "reason",
                f"DEMO-LEAVE-{index + 1:02d}",
                reason,
            )
            upsert(
                db,
                LeaveRequest,
                {"employee_id": employee.id, "reason": reason},
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
                {"challenge_token_hash": hash_token(f"RANDOM-CHECK-{index + 1:02d}")},
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

        db.execute(delete(SecurityAlert).where(SecurityAlert.employee_id.in_(demo_employee_ids)))
        alert_data = [
            ("CONCURRENT_LOGIN", "MEDIUM", "Phát hiện phiên đăng nhập đồng thời"),
            ("RANDOM_CHECK_MISSED", "HIGH", "Không phản hồi Random Check đúng hạn"),
            ("NEW_DEVICE", "LOW", "Đăng nhập từ thiết bị mới"),
            ("UNUSUAL_IP", "MEDIUM", "Địa chỉ IP cần quản trị viên kiểm tra"),
            ("ATTENDANCE_ANOMALY", "HIGH", "Bản ghi chấm công có dấu hiệu bất thường"),
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
                    "description": description,
                    "evidence": {"source": "seed_data", "sample": index + 1},
                    "status": status,
                    "resolved_by": users[0].id if status != "OPEN" else None,
                    "resolution_note": "Cảnh báo mẫu đã được xem xét" if status != "OPEN" else None,
                    "resolved_at": now if status != "OPEN" else None,
                },
            )

        db.execute(
            delete(Notification).where(Notification.user_id.in_([user.id for user in users]))
        )
        notification_data = [
            ("Chào mừng", "Tài khoản đã sẵn sàng", "SYSTEM"),
            ("Phân ca mới", "Bạn đã được phân ca làm việc", "SHIFT"),
            ("Kết quả nghỉ phép", "Đơn nghỉ phép mẫu đã được duyệt", "LEAVE"),
            ("Nhắc chấm công", "Vui lòng kiểm tra trạng thái check-out", "ATTENDANCE"),
            ("Xác minh thiết bị", "Thiết bị đang chờ phê duyệt", "SECURITY"),
        ]
        for index, (title, message, category) in enumerate(notification_data):
            upsert(
                db,
                Notification,
                {"user_id": users[index].id, "title": title},
                {
                    "message": message,
                    "category": category,
                    "read_at": now if index in (0, 2) else None,
                },
            )

        db.execute(delete(SystemSetting).where(SystemSetting.key.like("demo.%")))
        setting_data = [
            ("company.name", {"text": "Công ty TNHH ABC"}, "Tên đơn vị"),
            ("work.timezone", {"value": "Asia/Ho_Chi_Minh"}, "Múi giờ làm việc"),
            ("random_check.policy", {"enabled": True, "minutes": 120}, "Random Check"),
            ("attendance.policy", {"allow_early_check_in": 30}, "Chấm công"),
            ("notification.policy", {"desktop": True}, "Thông báo"),
        ]
        for key, value, description in setting_data:
            upsert(
                db,
                SystemSetting,
                {"key": key},
                {"value": value, "description": description, "updated_by": users[0].id},
            )

        # Đưa các phiên đăng nhập của tài khoản kiểm thử về trạng thái cố định.
        # Đồng thời bỏ cảnh báo đăng nhập đồng thời phát sinh khi kiểm thử API.
        demo_user_ids = [user.id for user in users]
        db.execute(delete(LoginSession).where(LoginSession.user_id.in_(demo_user_ids)))
        db.flush()

        db.execute(
            delete(AuditLog).where(
                AuditLog.action.like("DEMO_SEED%") | AuditLog.action.like("SEED_DATA%")
            )
        )
        for index, user in enumerate(users):
            action = f"SEED_DATA_ACTION_{index + 1:02d}"
            db.add(
                AuditLog(
                    user_id=user.id,
                    action=action,
                    entity_type="SEED_DATA",
                    entity_id=str(employees[index].id),
                    client_ip=f"127.0.0.{index + 1}",
                    after_data={"seed": True, "sample": index + 1},
                )
            )

            session_id = f"seed-session-{index + 1:02d}"
            upsert(
                db,
                LoginSession,
                {"id": session_id},
                {
                    "user_id": user.id,
                    "token_hash": hash_token(f"SESSION-TOKEN-{index + 1:02d}"),
                    "client_ip": f"127.0.0.{index + 1}",
                    "device_fingerprint": f"DEVICE-{index + 1:02d}",
                    "expires_at": now + timedelta(days=1),
                    "revoked_at": now,
                    "last_seen_at": now - timedelta(minutes=index),
                },
            )

        db.flush()
        department_codes = [item[0] for item in department_data]
        position_codes = [item[0] for item in position_data]
        shift_codes = [item[0] for item in shift_data]
        leave_type_codes = [item[0] for item in leave_type_data]
        permission_codes = [item[0] for item in permission_data]
        setting_keys = [item[0] for item in setting_data]
        summary = {
            "Phòng ban": len(
                db.scalars(select(Department).where(Department.code.in_(department_codes))).all()
            ),
            "Chức vụ": len(
                db.scalars(select(Position).where(Position.code.in_(position_codes))).all()
            ),
            "Ca làm": len(db.scalars(select(Shift).where(Shift.code.in_(shift_codes))).all()),
            "Nhân viên": len(
                db.scalars(select(Employee).where(Employee.id.in_(demo_employee_ids))).all()
            ),
            "Tài khoản": len(db.scalars(select(User).where(User.id.in_(demo_user_ids))).all()),
            "Quyền hạn": len(
                db.scalars(select(Permission).where(Permission.code.in_(permission_codes))).all()
            ),
            "Phân ca": len(
                db.scalars(
                    select(ShiftAssignment).where(
                        ShiftAssignment.employee_id.in_(demo_employee_ids)
                    )
                ).all()
            ),
            "Chấm công": len(
                db.scalars(
                    select(AttendanceRecord).where(
                        AttendanceRecord.employee_id.in_(demo_employee_ids)
                    )
                ).all()
            ),
            "Điều chỉnh công": len(
                db.scalars(
                    select(AttendanceAdjustment)
                    .join(AttendanceRecord)
                    .where(AttendanceRecord.employee_id.in_(demo_employee_ids))
                ).all()
            ),
            "Loại nghỉ phép": len(
                db.scalars(select(LeaveType).where(LeaveType.code.in_(leave_type_codes))).all()
            ),
            "Quỹ phép": len(
                db.scalars(
                    select(LeaveBalance).where(LeaveBalance.employee_id.in_(demo_employee_ids))
                ).all()
            ),
            "Đơn nghỉ phép": len(
                db.scalars(
                    select(LeaveRequest).where(LeaveRequest.employee_id.in_(demo_employee_ids))
                ).all()
            ),
            "Thiết bị": len(
                db.scalars(select(Device).where(Device.employee_id.in_(demo_employee_ids))).all()
            ),
            "Random Check": len(
                db.scalars(
                    select(RandomCheck).where(RandomCheck.employee_id.in_(demo_employee_ids))
                ).all()
            ),
            "Cảnh báo": len(
                db.scalars(
                    select(SecurityAlert).where(SecurityAlert.employee_id.in_(demo_employee_ids))
                ).all()
            ),
            "Thông báo": len(
                db.scalars(
                    select(Notification).where(Notification.user_id.in_(demo_user_ids))
                ).all()
            ),
            "Cấu hình": len(
                db.scalars(select(SystemSetting).where(SystemSetting.key.in_(setting_keys))).all()
            ),
            "Nhật ký": len(
                db.scalars(select(AuditLog).where(AuditLog.action.like("SEED_DATA%"))).all()
            ),
            "Phiên đăng nhập": len(
                db.scalars(
                    select(LoginSession).where(LoginSession.user_id.in_(demo_user_ids))
                ).all()
            ),
        }

    return summary


def create_sample_backups(database_path: Path):
    backup_directory = database_path.parent.parent / "backups"
    backup_directory.mkdir(parents=True, exist_ok=True)
    for legacy_path in backup_directory.glob("attendance_demo_*.sqlite3"):
        legacy_path.unlink()
    with sqlite3.connect(database_path) as source:
        for index in range(1, 6):
            target_path = backup_directory / f"attendance_sample_{index:02d}.sqlite3"
            if target_path.exists():
                target_path.unlink()
            with sqlite3.connect(target_path) as target:
                source.backup(target)
    return backup_directory


def find_legacy_demo_values(database_path: Path) -> list[str]:
    findings = []
    with sqlite3.connect(database_path) as connection:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master " "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]
        for table in tables:
            quoted_table = table.replace('"', '""')
            columns = connection.execute(f'PRAGMA table_info("{quoted_table}")').fetchall()
            for column in columns:
                column_name = column[1]
                quoted_column = column_name.replace('"', '""')
                count = connection.execute(
                    f'SELECT COUNT(*) FROM "{quoted_table}" '
                    f'WHERE LOWER(CAST("{quoted_column}" AS TEXT)) LIKE ?',
                    ("%demo%",),
                ).fetchone()[0]
                if count:
                    findings.append(f"{table}.{column_name}: {count}")
    return findings


def main():
    configure_console_encoding()
    options = arguments()
    database_path = options.database.resolve()
    prepare_runtime(database_path)
    summary = seed(database_path)
    legacy_findings = find_legacy_demo_values(database_path)
    if legacy_findings:
        raise RuntimeError("Database vẫn còn chuỗi không hợp lệ: " + ", ".join(legacy_findings))
    backup_directory = None
    if not options.skip_backups:
        backup_directory = create_sample_backups(database_path)

    print("\nĐÃ NẠP DỮ LIỆU KIỂM THỬ THÀNH CÔNG")
    print(f"Database: {database_path}")
    for label, count in summary.items():
        print(f"- {label}: {count}")
    if backup_directory:
        print(f"- Bản sao lưu: 5 ({backup_directory})")
    print("\nTÀI KHOẢN KIỂM THỬ")
    print("- Admin:    admin / 123456")
    print("- Manager:  manage / 123456")
    print("- Employee: user1 / 123456")
    print("- Employee: user2 / 123456")
    print("- Employee: user3 / 123456")


if __name__ == "__main__":
    main()
