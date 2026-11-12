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
- Admin có quyền xóa dữ liệu quản trị. Manager được phê duyệt, thu hồi và loại bỏ
  thiết bị cũ trong phạm vi phòng ban.

## Phê duyệt thiết bị

Lần đầu nhân viên đăng nhập trên một máy, thiết bị sẽ ở trạng thái
chờ duyệt và chưa thể chấm công.

1. Mở `AttendanceAdmin.exe` và đăng nhập Admin hoặc Manager.
2. Chọn chức năng riêng **Phê duyệt thiết bị** trên thanh điều hướng.
3. Chọn đúng nhân viên/tên máy, sau đó nhấn **Phê duyệt**.
4. Quay lại Client và chấm công lại.

## Chức năng chính

- Check-in/check-out theo thời gian Server, thiết bị đã phê duyệt, geofencing và tọa độ GPS từ Windows; máy
  không có cảm biến GPS có thể dùng địa chỉ IP LAN nội bộ khi cờ dự phòng được bật.
- Admin/Manager xem riêng vĩ độ, kinh độ và sai số GPS lúc vào/ra trong **Quản lý chấm công**;
  Manager chỉ xem nhân viên thuộc phòng ban của mình.
- Lịch làm việc, lịch sử chấm công và yêu cầu điều chỉnh.
- Nghỉ phép, quỹ phép, phân ca và duyệt yêu cầu; nhân viên có nút **Hủy đơn** đối với đơn đang chờ
  hoặc đơn đã duyệt nhưng chưa bắt đầu.
- Random Check, cảnh báo và thông báo WebSocket.
- Cảnh báo lỗi rõ ràng cho lỗi nhập liệu, phân quyền, mạng LAN, timeout, cấu hình và lỗi Server.
- Một nút Làm mới để đặt lại bộ lọc, phân trang và tải lại dữ liệu; hỗ trợ xuất Excel có
  tiêu đề, màu sắc, bộ lọc, dòng xen kẽ và định dạng in đẹp; dòng đang chọn được làm nổi bật.
- Design system nhất quán: font Segoe UI dễ đọc, icon native rõ nét trên mọi nút, thanh công cụ
  cuộn ngang khi thiếu chỗ, bảng tự căn cột/hàng và giữ nguyên nội dung đầy đủ trong tooltip;
  Indigo cho nhân viên, Teal cho quản trị, thẻ bo góc và hiệu ứng chuyển trang nhẹ.
- Quản lý nhân viên, phòng ban, chức vụ, ca làm và tài khoản.
- Bảng lương tháng/năm cho Admin và Manager: tổng thực nhận, lương theo ngày công,
  thưởng chuyên cần, duyệt và tính tiền làm thêm giờ, biểu đồ màu, bảng chi tiết và xuất Excel. Manager chỉ xem/cập nhật
  nhân viên trong phòng ban của mình.
- Báo cáo Excel/PDF dùng font TrueType Unicode để hiển thị đúng tiếng Việt, sao lưu và khôi phục SQLite.
- Phân trang, nhật ký kiểm toán và tự dọn phiên dữ liệu cũ.

## Bật vị trí GPS trên Windows

Trước khi chấm công, mở **Settings → Privacy & security → Location**, bật **Location services**
và quyền vị trí cho ứng dụng desktop. Khi nhấn CHECK-IN/CHECK-OUT, Client sẽ hiển thị tọa độ
đang gửi. Nếu máy không có cảm biến GPS, Client chuyển sang xác minh bằng IP nội bộ khi cả hai cờ
sau được bật:

- Client `config.json`: `"allow_lan_ip_location_fallback": true`.
- Server `server.env`: `ALLOW_LAN_IP_LOCATION_FALLBACK=true`.

Server vẫn kiểm tra IP thuộc `ALLOWED_NETWORKS`, thiết bị đã được phê duyệt và lưu nguồn vị trí
`LAN_IP_FALLBACK` trong kết quả nghiệp vụ. Đặt một trong hai cờ thành `false` để bắt buộc GPS.

Để chỉ cho phép chấm công trong phạm vi công ty, cấu hình `server.env` rồi khởi động lại Server:

```env
GEOFENCING_ENABLED=true
COMPANY_LATITUDE=10.776889
COMPANY_LONGITUDE=106.700806
GEOFENCE_RADIUS_METERS=200
GEOFENCE_MAX_ACCURACY_METERS=250
```

Khi bật geofencing, Server tự tính khoảng cách theo tọa độ WGS-84, từ chối GPS vượt bán kính hoặc
có sai số quá lớn và lưu khoảng cách tại thời điểm check-in/check-out. Muốn tuyệt đối bắt buộc GPS,
đặt thêm `ALLOW_LAN_IP_LOCATION_FALLBACK=false`.

## Cách tính lương và thưởng chuyên cần

Trong `AttendanceAdmin`, chọn **Lương & chuyên cần**, chọn kỳ lương rồi cập nhật
**Lương cơ bản/tháng**, **Thưởng chuyên cần/tháng** và **Hệ số làm thêm** cho từng nhân viên.

- Lương theo công = lương tháng × ngày được tính công / ngày đã phân ca.
- Ngày chấm công và ngày phép hưởng lương đều được tính công.
- Thời gian checkout sau giờ kết thúc ca được đưa vào **Duyệt làm thêm giờ**. Chỉ số phút được
  Admin/Manager duyệt mới được tính vào tiền làm thêm và tổng thực nhận.
- Thưởng chuyên cần được cộng khi nhân viên đủ công trong tháng và không đi muộn,
  về sớm hoặc có bản ghi chấm công bất thường.
- Tháng hiện tại chỉ tính đến ngày hôm nay; ngày phân ca trong tương lai không bị
  xem là thiếu công.

## Chạy từ mã nguồn

Yêu cầu Windows 10/11 và Python 3.12.

```powershell
.\scripts\setup.ps1
.\scripts\run_server.ps1
```

`setup.ps1` tự tạo `server/.env` cùng JWT secret ngẫu nhiên ở lần chạy đầu và không ghi đè
cấu hình hiện có. Không chép nguyên giá trị `CHANGE_...` trong file mẫu vào môi trường chạy.

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

Khi chạy cả ba luồng trên cùng một máy, Client và Admin sẽ tự thoát sau vài giây nếu cửa sổ
Server đã đóng. Cơ chế này chỉ áp dụng khi `server_url` trỏ về localhost, tên máy hoặc một IP LAN
của chính máy đang chạy; Client trên máy khác vẫn giữ mở khi kết nối LAN bị gián đoạn.

## Chạy trong mạng LAN

1. Đặt IP tĩnh cho máy Server.
2. Mở cổng TCP `8000` và UDP `37020` trên Firewall.
3. Sửa `config.json` của Client/Admin, ví dụ:

```json
{
  "server_url": "http://192.168.1.100:8000",
  "verify_tls": false,
  "allow_lan_ip_location_fallback": true,
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

Trạng thái hiện tại: **101 kiểm thử đạt**, Ruff không phát hiện lỗi.

## Thư mục quan trọng

```text
server/          API, model, migration và nghiệp vụ
client/          Giao diện Client/Admin
scripts/         Cài đặt, chạy, seed và build
tests/           Kiểm thử tự động
docs/            Tài liệu chi tiết
dist_portable/   Ba gói portable, không commit lên Git
```

Các tệp lớn đã được tách theo trách nhiệm để dễ bảo trì và trình bày đồ án:

- `server/app/api/application.py`: khởi tạo FastAPI, lifecycle và ghép router.
- `server/app/api/common.py`: kiểm tra phạm vi, chuyển đổi dữ liệu và audit dùng chung.
- `server/app/api/routes/attendance.py`, `leave.py`, `reporting.py`: API chấm công, nghỉ phép,
  bảng lương và báo cáo được tách theo domain.
- `client/app/ui/main_window.py`: khung cửa sổ và điều hướng.
- `client/app/ui/catalog.py`: tên trang, cột bảng và nhãn trạng thái.
- `client/app/ui/attendance_portal.py`, `leave_portal.py`, `payroll_ui.py`: nghiệp vụ giao diện
  chấm công, nghỉ phép và bảng lương.

Không commit `server/.env`, `client/config.json`, database SQLite hoặc bản sao
lưu. Không xóa `dist_portable/AttendanceServer/data` nếu còn dữ liệu cần giữ.

Tài liệu triển khai chi tiết: [docs/DEPLOYMENT_WINDOWS_LAN.md](docs/DEPLOYMENT_WINDOWS_LAN.md).
