import argparse
import ctypes
import getpass
import sys
from pathlib import Path

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "server"))

import uvicorn  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.database.sqlite import sqlite_database_path  # noqa: E402


def configure_console_encoding():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            continue


def configure_console_window():
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.kernel32.SetConsoleTitleW("Attendance Server - LAN")
    except (AttributeError, OSError):
        pass


def run_migrations(database_url: str):
    database_path = sqlite_database_path(database_url)
    if database_path != Path(":memory:"):
        database_path.parent.mkdir(parents=True, exist_ok=True)
    config_path = ROOT / "server" / "alembic.ini"
    script_path = ROOT / "server" / "alembic"
    if not config_path.is_file() or not script_path.is_dir():
        raise RuntimeError("Không tìm thấy tài nguyên migration Alembic trong bản phát hành")
    config = Config(str(config_path))
    config.set_main_option("script_location", str(script_path))
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")


def command_line():
    parser = argparse.ArgumentParser(description="LAN Attendance Server")
    commands = parser.add_subparsers(dest="command")
    bootstrap = commands.add_parser("bootstrap-admin", help="Tạo Admin đầu tiên")
    bootstrap.add_argument("--username", required=True)
    bootstrap.add_argument("--employee-code", required=True)
    bootstrap.add_argument("--name", required=True)
    bootstrap.add_argument("--email", required=True)
    return parser.parse_args()


def main():
    configure_console_encoding()
    configure_console_window()
    arguments = command_line()
    settings = get_settings()
    run_migrations(settings.database_url)
    if arguments.command == "bootstrap-admin":
        from app.database.session import SessionLocal
        from app.services.bootstrap import create_initial_admin

        password = getpass.getpass("Mật khẩu Admin (tối thiểu 10 ký tự): ")
        confirmation = getpass.getpass("Nhập lại mật khẩu Admin: ")
        if password != confirmation:
            raise SystemExit("Hai lần nhập mật khẩu không khớp")
        try:
            with SessionLocal.begin() as db:
                create_initial_admin(
                    db,
                    username=arguments.username,
                    employee_code=arguments.employee_code,
                    full_name=arguments.name,
                    email=arguments.email,
                    password=password,
                )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        print("Đã tạo Admin an toàn. Không ghi mật khẩu ra tệp hoặc màn hình.")
        return
    print("=" * 64)
    print("ATTENDANCE SERVER — CỬA SỔ QUẢN LÝ SERVER")
    print(f"Địa chỉ: {settings.server_host}:{settings.server_port}")
    print("Nhấn Ctrl+C hoặc đóng cửa sổ này để dừng Server.")
    print("=" * 64)
    uvicorn.run(
        "app.main:app",
        host=settings.server_host,
        port=settings.server_port,
        ssl_certfile=settings.tls_cert_file,
        ssl_keyfile=settings.tls_key_file,
    )


if __name__ == "__main__":
    main()
