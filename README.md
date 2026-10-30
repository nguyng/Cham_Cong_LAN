# Hệ thống chấm công qua mạng LAN

Hệ thống chấm công nội bộ gồm Server FastAPI, ứng dụng nhân viên và
ứng dụng quản lý PySide6. Dữ liệu được lưu tập trung bằng SQLite trên máy
Server; Client không truy cập trực tiếp database.

## Chạy nhanh bản portable

Mở PowerShell tại thư mục `Cham_Cong_LAN` và chạy:

```powershell
$root = Resolve-Path ".\dist_portable"
$serverDir = Join-Path $root "AttendanceServer"
$adminDir = Join-Path $root "AttendanceAdmin"
$clientDir = Join-Path $root "AttendanceClient"

$server = Start-Process "$serverDir\AttendanceServer.exe" -WorkingDirectory $serverDir -PassThru
Start-Sleep -Seconds 4
$admin = Start-Process "$adminDir\AttendanceAdmin.exe" -WorkingDirectory $adminDir -PassThru
$client = Start-Process "$clientDir\AttendanceClient.exe" -WorkingDirectory $clientDir -PassThru

try {
    while (-not $admin.HasExited -or -not $client.HasExited) {
        Start-Sleep -Seconds 1
        $admin.Refresh()
        $client.Refresh()
    }
}
finally {
    foreach ($process in @($client, $admin, $server)) {
        if ($null -ne $process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force
        }
    }
}
```

Server hiện trong cửa sổ console riêng. Khi Admin và Client đã đóng, lệnh
trên sẽ dừng Server để không chạy ngầm.

Dừng khẩn cấp tất cả tiến trình:

```powershell
Get-Process AttendanceServer,AttendanceAdmin,AttendanceClient `
    -ErrorAction SilentlyContinue | Stop-Process -Force
```

## Tài khoản mẫu

| Vai trò | Tài khoản | Mật khẩu |
|---|---|---|
| Admin | `admin` | `123456` |
| Manager | `manage` | `123456` |
| Nhân viên | `user1`, `user2`, `user3` | `123456` |

- `AttendanceClient`: cổng nhân viên. Tài khoản `manage` đăng nhập tại đây
  chỉ thấy dữ liệu cá nhân.
- `AttendanceAdmin`: cổng quản lý. Admin quản lý toàn hệ thống; Manager
  chỉ quản lý nhân viên thuộc phòng ban của mình.
- Chỉ Admin có quyền xóa. Manager được phê duyệt/thu hồi thiết bị
  trong phạm vi phòng ban.

## Phê duyệt thiết bị

Lần đầu nhân viên đăng nhập trên một máy, thiết bị sẽ ở trạng thái
chờ duyệt và chưa thể chấm công.

1. Mở `AttendanceAdmin.exe` và đăng nhập Admin hoặc Manager.
2. Chọn **Thiết bị**.
3. Chọn đúng nhân viên/tên máy, sau đó nhấn **Phê duyệt**.
4. Quay lại Client và chấm công lại.

## Chức năng chính

- Check-in/check-out theo thời gian Server và thiết bị đã phê duyệt.
- Lịch làm việc, lịch sử chấm công và yêu cầu điều chỉnh.
- Nghỉ phép, quỹ phép, phân ca và duyệt yêu cầu.
- Random Check, cảnh báo và thông báo WebSocket.
- Quản lý nhân viên, phòng ban, chức vụ, ca làm và tài khoản.
- Báo cáo Excel/PDF, sao lưu và khôi phục SQLite.
- Phân trang, nhật ký kiểm toán và tự dọn phiên dữ liệu cũ.

## Chạy từ mã nguồn

Yêu cầu Windows 10/11 và Python 3.12.

```powershell
.\scripts\setup.ps1
Copy-Item .\server\.env.example .\server\.env
.\scripts\run_server.ps1
```

Mở Client trong PowerShell khác:

```powershell
$env:PYTHONPATH = "$PWD\client"
.\.venv\Scripts\python.exe -m app.main
```

Mở Admin:

```powershell
.\.venv\Scripts\python.exe .\admin\main.py
```

API mặc định: `http://127.0.0.1:8000`; OpenAPI: `http://127.0.0.1:8000/docs`.

## Chạy trong mạng LAN

1. Đặt IP tĩnh cho máy Server.
2. Mở cổng TCP `8000` và UDP `37020` trên Firewall.
3. Sửa `config.json` của Client/Admin, ví dụ:

```json
{
  "server_url": "http://192.168.1.100:8000",
  "verify_tls": false,
  "discovery_port": 37020,
  "request_timeout_seconds": 10
}
```

Khi sao chép bản portable sang máy khác, phải sao chép cả thư mục, không
chỉ sao chép file `.exe`.

## Kiểm thử và đóng gói

```powershell
.\.venv\Scripts\python.exe -m ruff check server client admin scripts tests
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q
.\scripts\build_portable.ps1
```

Trạng thái hiện tại: **40 kiểm thử đạt**, Ruff không phát hiện lỗi.

## Thư mục quan trọng

```text
server/          API, model, migration và nghiệp vụ
client/          Giao diện Client/Admin
scripts/         Cài đặt, chạy, seed và build
tests/           Kiểm thử tự động
docs/            Tài liệu chi tiết
dist_portable/   Ba gói portable, không commit lên Git
```

Không commit `server/.env`, `client/config.json`, database SQLite hoặc bản sao
lưu. Không xóa `dist_portable/AttendanceServer/data` nếu còn dữ liệu cần giữ.

Tài liệu triển khai chi tiết: [docs/DEPLOYMENT_WINDOWS_LAN.md](docs/DEPLOYMENT_WINDOWS_LAN.md).
