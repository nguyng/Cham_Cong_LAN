# Hệ thống chấm công qua mạng LAN

Hệ thống chấm công nội bộ chạy hoàn toàn trong mạng LAN, được xây dựng bằng
Python. Dự án gồm một Server FastAPI, một ứng dụng nhân viên và một ứng dụng
quản trị PySide6. Dữ liệu được lưu tập trung bằng SQLite trên máy Server.

## Chạy nhanh bản portable trên một máy

Mở PowerShell tại thư mục chứa `Cham_Cong_LAN`, sau đó chạy:

```powershell
$root = Resolve-Path ".\Cham_Cong_LAN\dist_portable"

Start-Process "$root\AttendanceServer\AttendanceServer.exe" `
    -WorkingDirectory "$root\AttendanceServer" `
    -WindowStyle Hidden

Start-Sleep -Seconds 4

Start-Process "$root\AttendanceAdmin\AttendanceAdmin.exe" `
    -WorkingDirectory "$root\AttendanceAdmin"

Start-Process "$root\AttendanceClient\AttendanceClient.exe" `
    -WorkingDirectory "$root\AttendanceClient"
```

Nếu PowerShell đang ở ngay trong thư mục `Cham_Cong_LAN`, thay dòng đầu bằng:

```powershell
$root = Resolve-Path ".\dist_portable"
```

Dừng toàn bộ chương trình:

```powershell
Get-Process AttendanceServer,AttendanceAdmin,AttendanceClient `
    -ErrorAction SilentlyContinue | Stop-Process -Force
```

## Tài khoản có sẵn

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Admin | `admin` | `123456` |
| Manager | `manage` | `123456` |
| Nhân viên | `user1` | `123456` |
| Nhân viên | `user2` | `123456` |
| Nhân viên | `user3` | `123456` |

### Phân biệt Client và Admin

- `AttendanceClient` là cổng nhân viên. Tài khoản `manage` đăng nhập tại đây chỉ
  thấy giao diện và dữ liệu cá nhân của chính mình.
- `AttendanceAdmin` là cổng quản lý. Admin có quyền toàn hệ thống; Manager chỉ
  quản lý dữ liệu thuộc phòng ban của mình.
- Tài khoản nhân viên không được phép đăng nhập `AttendanceAdmin`.

## Chức năng chính

### Nhân viên

- Check-in/check-out theo thời gian chính thức từ Server.
- Hiển thị ca làm, giờ vào, giờ ra và tổng thời gian làm trong ngày.
- Xem lịch sử chấm công và gửi yêu cầu điều chỉnh.
- Xem lịch phân ca.
- Tạo, theo dõi và hủy đơn nghỉ phép hợp lệ.
- Nhận thông báo và Random Check qua WebSocket.
- Đổi mật khẩu và xem hồ sơ cá nhân.

### Admin và Manager

- Dashboard theo dõi nhân sự, chấm công, nghỉ phép và cảnh báo.
- Quản lý nhân viên, phòng ban, chức vụ, ca làm và phân ca.
- Duyệt yêu cầu điều chỉnh công và nghỉ phép.
- Quản lý loại nghỉ phép và quỹ phép.
- Gửi Random Check và xử lý cảnh báo bất thường.
- Phê duyệt thiết bị được phép chấm công.
- Xem Client trực tuyến, tài khoản, nhật ký và cấu hình hệ thống.
- Xuất báo cáo Excel/PDF, sao lưu và khôi phục SQLite.
- Danh sách lớn có phân trang; menu Admin có thanh cuộn riêng.

## Kiến trúc

```text
AttendanceClient.exe        AttendanceAdmin.exe
          \                       /
           \ REST API + WebSocket
            \                   /
              AttendanceServer.exe
                       |
            SQLAlchemy + Alembic
                       |
              SQLite (WAL + FK)
```

| Thành phần | Công nghệ |
|---|---|
| Server | Python 3.12, FastAPI, Uvicorn |
| Giao diện | PySide6, Qt Charts |
| Database | SQLite, SQLAlchemy, Alembic |
| Xác thực | JWT, phiên đăng nhập có thể thu hồi, Argon2 |
| Thời gian thực | WebSocket |
| Báo cáo | OpenPyXL, ReportLab |
| Đóng gói | PyInstaller |

SQLite chỉ nằm trên máy Server. Client không truy cập trực tiếp file database;
toàn bộ dữ liệu được trao đổi qua API.

## Cấu trúc thư mục

```text
Cham_Cong_LAN/
├── server/                 FastAPI, model, migration và nghiệp vụ
├── client/                 Ứng dụng PySide6 dùng chung cho Client/Admin
├── admin/                  Điểm khởi chạy Admin khi phát triển
├── scripts/                Cài đặt, chạy, seed, build và kiểm tra LAN
├── packaging/              Cấu hình PyInstaller portable
├── tests/                  Kiểm thử API, SQLite, phân quyền và UI
├── docs/                   Tài liệu kiến trúc, triển khai và test
└── dist_portable/          Ba gói chạy portable (không được commit)
```

## Chạy từ mã nguồn

### 1. Chuẩn bị môi trường

Yêu cầu Windows 10/11 và Python 3.12.

```powershell
.\scripts\setup.ps1
Copy-Item .\server\.env.example .\server\.env
```

Trước khi dùng thực tế, thay `JWT_SECRET` trong `server\.env` bằng một chuỗi ngẫu
nhiên dài tối thiểu 32 ký tự.

### 2. Migration database

```powershell
Set-Location .\server
..\.venv\Scripts\python.exe -m alembic upgrade head
Set-Location ..
```

### 3. Chạy Server

```powershell
.\scripts\run_server.ps1
```

Server mặc định lắng nghe tại `http://0.0.0.0:8000`. Kiểm tra trạng thái:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

OpenAPI có tại `http://127.0.0.1:8000/docs`.

### 4. Chạy Client

Mở một PowerShell khác:

```powershell
$env:PYTHONPATH = "$PWD\client"
.\.venv\Scripts\python.exe -m app.main
```

### 5. Chạy Admin

```powershell
.\.venv\Scripts\python.exe .\admin\main.py
```

## Cấu hình cho nhiều máy trong LAN

1. Chọn một máy làm Server và đặt IP tĩnh, ví dụ `192.168.1.100`.
2. Cho phép cổng TCP `8000` và UDP `37020` trên Windows Firewall.
3. Trên máy Client, sửa `AttendanceClient\config.json`:

```json
{
  "server_url": "http://192.168.1.100:8000",
  "verify_tls": false,
  "discovery_port": 37020,
  "request_timeout_seconds": 10
}
```

4. Giữ nguyên toàn bộ thư mục portable khi sao chép; không chỉ chép file `.exe`.

Có thể tạo rule Firewall bằng script:

```powershell
.\scripts\configure_firewall.ps1
```

Xem hướng dẫn chi tiết tại [docs/DEPLOYMENT_WINDOWS_LAN.md](docs/DEPLOYMENT_WINDOWS_LAN.md).

## Dữ liệu mẫu

Nạp lại dữ liệu mẫu cho bản portable:

```powershell
.\.venv\Scripts\python.exe .\scripts\seed_sample_data.py `
    --database ".\dist_portable\AttendanceServer\data\attendance.db"
```

Hãy dừng Server trước khi chạy lệnh seed. Script có thể chạy lặp lại, tự sao lưu
database và không lưu mật khẩu dưới dạng plaintext.

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m ruff check `
    server client admin scripts tests `
    server_launcher.py client_launcher.py admin_launcher.py

$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q
```

Trạng thái hiện tại: **34 bài kiểm thử đạt** và Ruff không phát hiện lỗi.

## Đóng gói

Tạo bản portable khuyến nghị:

```powershell
.\scripts\build_portable.ps1
```

Kết quả:

```text
dist_portable/
├── AttendanceServer/
├── AttendanceClient/
└── AttendanceAdmin/
```

Script build giữ lại `server.env`, `config.json`, database SQLite và các bản sao lưu
hiện có. Không xóa `dist_portable\AttendanceServer\data` khi còn dữ liệu cần giữ.

Tạo bản one-file:

```powershell
.\scripts\build.ps1
```

Bản portable ổn định hơn trên các máy có Endpoint Protection nghiêm ngặt.

## Bảo mật và vận hành

- Mật khẩu được hash bằng Argon2.
- Access token gắn với phiên đăng nhập có thể thu hồi khi logout hoặc đổi mật khẩu.
- RBAC được kiểm tra tại Server, không chỉ ẩn nút trên giao diện.
- Check-in/check-out kiểm tra mạng LAN, ca làm và thiết bị đã phê duyệt.
- SQLite bật WAL, foreign key và `busy_timeout`.
- Bản ghi idempotency và phiên đăng nhập cũ được dọn theo chu kỳ.
- Không commit `server/.env`, `client/config.json`, database hoặc bản sao lưu.
- Khi triển khai thực tế, nên dùng HTTPS với chứng chỉ nội bộ.

## Xử lý lỗi thường gặp

### `WorkingDirectory` không hợp lệ

Kiểm tra đã build `dist_portable` và dùng `Resolve-Path` như lệnh chạy nhanh ở đầu
README. Không chạy lệnh từ một thư mục không chứa dự án.

### Không đăng nhập được

1. Kiểm tra `AttendanceServer.exe` đang chạy.
2. Mở `http://127.0.0.1:8000/api/v1/health`.
3. Kiểm tra `config.json` trỏ đúng IP Server.
4. Kiểm tra Firewall và hai máy đang cùng mạng LAN.

### Không thể chấm công

- Tài khoản phải có ca làm phù hợp trong ngày.
- Thiết bị phải được Admin phê duyệt.
- Client phải kết nối từ dải IP được khai báo trong `ALLOWED_NETWORKS`.
- Mỗi ca chỉ được CHECK-IN một lần.

## Tài liệu

- [Kiến trúc và API](docs/API_AND_ARCHITECTURE.md)
- [Triển khai Windows LAN](docs/DEPLOYMENT_WINDOWS_LAN.md)
- [Checklist hiện thực](docs/IMPLEMENTATION_CHECKLIST.md)
- [Kết quả kiểm thử](docs/TEST_REPORT.md)
- [Phân tích dự án](phan_tich_du_an_cham_cong.md)

## Phạm vi sử dụng

Dự án phù hợp cho doanh nghiệp hoặc nhóm nội bộ quy mô nhỏ và vừa trong một
mạng LAN. Trước khi dùng cho môi trường sản xuất lớn, cần kiểm thử tải, HTTPS,
chính sách sao lưu và phục hồi trên hạ tầng thực tế.
