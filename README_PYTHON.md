# LAN Attendance Management System — chạy bằng Python

Hệ thống chạy trực tiếp từ mã nguồn trên Windows 10/11 với Python 3.12. Server dùng
FastAPI và SQLite; Client/Admin dùng PySide6. Client không truy cập trực tiếp database.

## Cài đặt và chạy

Mở PowerShell tại thư mục `Cham_Cong_LAN`:

```powershell
.\scripts\setup.ps1
.\scripts\run_all.ps1
```

`setup.ps1` tạo `.venv`, cài dependency, sinh `server/.env` với JWT secret ngẫu nhiên và
chỉ nạp dữ liệu mẫu khi database chưa có tài khoản. Nó không đặt lại database đang sử dụng.

`run_all.ps1` mở ba cửa sổ riêng cho Server, Admin và User. Khi cửa sổ Server đóng,
watchdog sẽ dừng hẳn hai ứng dụng còn lại, kể cả khi chúng đang ở màn hình đăng nhập.

Múi giờ nghiệp vụ mặc định là UTC+7 (`Asia/Ho_Chi_Minh`). Server lưu timestamp theo
UTC và Client/Admin luôn chuyển sang UTC+7 khi hiển thị, không phụ thuộc múi giờ Windows.

Muốn gỡ lỗi từng thành phần, mở ba PowerShell tại thư mục dự án và chạy lần lượt:

```powershell
.\.venv\Scripts\python.exe .\server_launcher.py
.\.venv\Scripts\python.exe .\admin_launcher.py
.\.venv\Scripts\python.exe .\client_launcher.py
```

Không dùng `python -m app.main` từ thư mục gốc; các launcher tự thiết lập đúng đường dẫn module.

## Tài khoản mẫu

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Admin | `admin` | `123456` |
| Manager | `manage` | `123456` |
| Employee | `user1` | `123456` |
| Employee | `user2` | `123456` |
| Employee | `user3` | `123456` |

Client luôn là cổng cá nhân. Tài khoản `manage` đăng nhập ở Client chỉ thấy dữ liệu cá nhân;
chức năng quản lý chỉ xuất hiện khi đăng nhập bằng cửa sổ Admin.

Muốn chủ động đưa dữ liệu kiểm thử về trạng thái mẫu, hãy dừng Server và chạy:

```powershell
.\.venv\Scripts\python.exe .\scripts\seed_sample_data.py
```

Lệnh trên cập nhật dữ liệu mẫu trong `server/data/attendance.db` và tạo bản sao tại
`server/backups`. Không chạy lệnh này trên database vận hành cần giữ nguyên dữ liệu.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m ruff check server client admin scripts tests
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q
```

Database nguồn nằm tại `server/data/attendance.db`. Không đặt `.db` trên thư mục chia sẻ mạng,
OneDrive hoặc Google Drive; không cho Client truy cập trực tiếp tệp này.

Xem [bảng đối chiếu](docs/IMPLEMENTATION_CHECKLIST.md),
[kiến trúc/API](docs/API_AND_ARCHITECTURE.md),
[triển khai LAN](docs/DEPLOYMENT_WINDOWS_LAN.md) và
[kết quả kiểm thử](docs/TEST_REPORT.md).
