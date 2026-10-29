import argparse
import getpass
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.database.session import SessionLocal  # noqa: E402
from app.services.bootstrap import create_initial_admin  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Khởi tạo tài khoản Admin đầu tiên")
    parser.add_argument("--username", required=True)
    parser.add_argument("--employee-code", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Mật khẩu Admin (tối thiểu 10 ký tự): ")
    try:
        with SessionLocal.begin() as db:
            create_initial_admin(
                db,
                username=args.username,
                employee_code=args.employee_code,
                full_name=args.name,
                email=args.email,
                password=password,
            )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print("Đã tạo Admin an toàn. Không ghi mật khẩu ra tệp hoặc màn hình.")


if __name__ == "__main__":
    main()
