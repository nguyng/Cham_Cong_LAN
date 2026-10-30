# LAN Attendance Management System — Python

Đây là phần triển khai Python theo yêu cầu mới. Các tài liệu gốc Java/React được giữ nguyên làm nguồn đối chiếu, không bị ghi đè.

## Chạy nhanh cho phát triển

```powershell
.\scripts\setup.ps1
Copy-Item server\.env.example server\.env
# Giữ DATABASE_URL SQLite, sửa JWT_SECRET và chứng chỉ trong server\.env
Set-Location server
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe ..\scripts\bootstrap_admin.py --username admin --employee-code AD001 --name "Quản trị" --email admin@company.local
Set-Location ..
.\scripts\run_server.ps1
```

Ở cửa sổ khác:

```powershell
$env:PYTHONPATH = "$PWD\client"
.\.venv\Scripts\python.exe -m app.main
```

Ứng dụng Admin:

```powershell
.\.venv\Scripts\python.exe .\admin\main.py
```

`AttendanceClient` luôn là cổng nhân viên. Khi tài khoản `manage` đăng nhập tại đây,
giao diện và dữ liệu chỉ hiển thị phần cá nhân của chính Manager. Các chức năng quản lý
phòng ban chỉ xuất hiện khi đăng nhập bằng `AttendanceAdmin`.

## Dữ liệu kiểm thử có sẵn

Database của bản portable đã được nạp 5 mẫu cho từng nhóm chức năng. Các tài khoản thử:

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Admin | `admin` | `123456` |
| Manager | `manage` | `123456` |
| Employee | `user1` | `123456` |
| Employee | `user2` | `123456` |
| Employee | `user3` | `123456` |

Muốn đưa dữ liệu kiểm thử về trạng thái ban đầu, hãy tắt Server rồi chạy lại lệnh sau từ thư mục dự án:

```powershell
.\.venv\Scripts\python.exe .\scripts\seed_sample_data.py `
  --database ".\dist_portable\AttendanceServer\data\attendance.db"
```

Lệnh có thể chạy lặp lại và không xóa dữ liệu thật. Bản sao trước khi nạp dữ liệu nằm trong thư mục `dist_portable\AttendanceServer\backups`.

## Kiểm thử và đóng gói

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m ruff check server client admin scripts tests
.\scripts\build.ps1
.\scripts\build_portable.ps1
```

Ba tệp one-file nằm trong `dist`. Ba gói không cần tự giải nén, phù hợp máy có Endpoint Protection nghiêm ngặt và đã được runtime smoke, nằm trong `dist_portable\AttendanceServer`, `dist_portable\AttendanceClient` và `dist_portable\AttendanceAdmin`. Khi chép gói portable phải giữ nguyên toàn bộ thư mục, không chỉ chép file `.exe`.

`AttendanceServer.exe` tự chạy Alembic migration trước khi mở API. Tạo Admin đầu tiên trên máy chỉ có bản đóng gói bằng:

```powershell
.\AttendanceServer.exe bootstrap-admin `
  --username admin --employee-code AD001 `
  --name "Quản trị" --email admin@company.local
```

Database vận hành là SQLite tại `server/data/attendance.db` khi chạy mã nguồn. Với bản đóng gói, đặt `server.env` cạnh `AttendanceServer.exe`; đường dẫn SQLite tương đối được tính từ thư mục chạy Server. Không đặt tệp `.db` trên thư mục chia sẻ mạng và không cho Client truy cập trực tiếp.

Xem [bảng đối chiếu](docs/IMPLEMENTATION_CHECKLIST.md), [kiến trúc/API](docs/API_AND_ARCHITECTURE.md), [triển khai LAN](docs/DEPLOYMENT_WINDOWS_LAN.md) và [kết quả kiểm thử](docs/TEST_REPORT.md).
