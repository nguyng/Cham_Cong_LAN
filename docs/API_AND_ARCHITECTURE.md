# Kiến trúc và API

```text
AttendanceClient.exe / AttendanceAdmin.exe (PySide6)
      │ HTTPS REST + WSS (JWT)
      ▼
AttendanceServer.exe (FastAPI/Uvicorn)
      ├── Authentication / RBAC / session
      ├── HR / Shift / Attendance / Leave
      ├── Random Check / alert / notification
      ├── Report Excel/PDF / backup
      ├── WebSocket broadcast
      └── UDP discovery (metadata không nhạy cảm)
                 │ SQLAlchemy + transaction
                 ▼
       SQLite (WAL + foreign keys)
```

OpenAPI tương tác có tại `/docs` khi Server chạy. Các nhóm đường dẫn chính:

- `/api/v1/auth/*`: đăng nhập, đăng xuất, đổi mật khẩu.
- `/api/v1/employees`, `/departments`, `/positions`: nhân sự.
- `/api/v1/shifts`, `/shift-assignments`: ca và phân ca.
- `/api/v1/attendance/*`: check-in/out, lịch sử, điều chỉnh.
- `/api/v1/leaves`, `/leave-types`, `/leave-balances`: nghỉ phép.
- `/api/v1/random-checks/*`, `/security-alerts`: xác minh và cảnh báo.
- `/api/v1/reports/*`: thống kê, Excel và PDF.
- `/api/v1/ws`: thông báo thời gian thực.
- `/api/v1/admin/backup`, `/admin/backups`, `/admin/restore/{filename}`: quản trị dữ liệu.

Mọi thời gian chấm công được tạo ở Server. Request check-in/out có khóa idempotency; unique constraint ở database là lớp bảo vệ thứ hai.

SQLite chỉ nằm trên ổ đĩa cục bộ của máy Server. Client không mở hoặc chia sẻ trực tiếp tệp database; mọi truy cập vẫn qua FastAPI. Chế độ WAL, `busy_timeout=30000`, transaction và foreign keys được bật khi tạo kết nối để phục vụ nhiều Client LAN ở quy mô nội bộ.

Launcher của Server chạy `alembic upgrade head` trước Uvicorn ở cả mã nguồn và bản đóng gói. Bản đóng gói hỗ trợ lệnh `bootstrap-admin` để tạo quản trị viên đầu tiên mà không cần Python trên máy đích.
