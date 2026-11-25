# Hệ thống chấm công qua mạng LAN

Hệ thống chấm công nội bộ gồm Server FastAPI, ứng dụng nhân viên và
ứng dụng quản lý PySide6. Dữ liệu được lưu tập trung bằng SQLite trên máy
Server; Client không truy cập trực tiếp database.

## Chạy nhanh từ mã nguồn

Mở PowerShell tại đúng thư mục `Cham_Cong_LAN`. Lần đầu tiên, chạy:

```powershell
.\scripts\setup.ps1
```

`setup.ps1` tạo `.venv`, sinh `server/.env` với JWT secret ngẫu nhiên và chỉ nạp năm
tài khoản mẫu khi database chưa có tài khoản. Script không ghi đè database đang sử dụng.

Mỗi lần sử dụng, chỉ cần một lệnh để mở ba cửa sổ terminal riêng cho Server, Admin và User:

```powershell
.\scripts\run_all.ps1
```

`run_all.ps1` dùng đúng các entry point nguồn, chờ Server mở cổng rồi mới mở giao diện.
Một watchdog ẩn theo dõi đúng ba cây tiến trình vừa tạo; khi cửa sổ Server đóng, Admin và
User cũng được dừng hẳn, kể cả khi đang ở màn hình đăng nhập.

## Tài khoản mẫu

| Vai trò | Tài khoản | Mật khẩu |
|---|---|---|
| Admin | `admin` | `123456` |
| Manager | `manage` | `123456` |
| Nhân viên | `user1`, `user2`, `user3` | `123456` |

- `admin` là Admin gốc. Admin được tạo sau chỉ thấy tài khoản `admin` trong mục
  **Tài khoản** và không thể sửa, mở khóa hoặc xóa tài khoản gốc. Admin gốc quản lý
  được các tài khoản còn lại.
- Nút **Xóa** xóa bản ghi khỏi database; dữ liệu phụ thuộc bắt buộc cũng bị xóa,
  còn liên kết tùy chọn được gỡ. Thao tác không thể hoàn tác.
- `AttendanceClient`: cổng nhân viên. Tài khoản `manage` đăng nhập tại đây
  chỉ thấy dữ liệu cá nhân.
- `AttendanceAdmin`: cổng quản lý. Admin quản lý toàn hệ thống; Manager
  chỉ quản lý nhân viên thuộc phòng ban của mình.
- Admin có quyền xóa dữ liệu quản trị. Manager được phê duyệt, thu hồi và loại bỏ
  thiết bị cũ trong phạm vi phòng ban.

## Phê duyệt thiết bị

Lần đầu nhân viên đăng nhập trên một máy, thiết bị sẽ ở trạng thái
chờ duyệt và chưa thể chấm công.

1. Mở cửa sổ Admin và đăng nhập Admin hoặc Manager.
2. Chọn chức năng riêng **Phê duyệt thiết bị** trên thanh điều hướng.
3. Chọn đúng nhân viên/tên máy, sau đó nhấn **Phê duyệt**.
4. Quay lại Client và chấm công lại.

## Chức năng chính

- Toàn bộ nghiệp vụ và hiển thị thời gian dùng UTC+7 (`Asia/Ho_Chi_Minh`). Check-in
  chỉ được thực hiện trong giờ của ca đã phân; check-in muộn từ phút 15 sẽ cảnh báo.
  Mỗi ca chỉ có một lần check-in và một lần check-out; giờ vào, giờ ra và tổng phút
  làm được lưu trong cơ sở dữ liệu, rồi hiển thị thành giờ/phút. Check-out sau giờ
  kết thúc ca vẫn được ghi nhận để tính thời gian làm thêm.
- Check-in/check-out theo thời gian Server, thiết bị đã phê duyệt, geofencing và tọa độ GPS từ Windows; máy
  không có cảm biến GPS có thể dùng địa chỉ IP LAN nội bộ khi cờ dự phòng được bật.
- Admin/Manager xem riêng vĩ độ, kinh độ và sai số GPS lúc vào/ra trong **Quản lý chấm công**;
  Manager chỉ xem nhân viên thuộc phòng ban của mình.
- Lịch làm việc, lịch sử chấm công và yêu cầu điều chỉnh.
- Phân ca có bảng lịch tuần 7 ngày ngay dưới danh sách; Admin/Manager xem ca theo từng nhân viên,
  nhân viên xem ca của mình trong trang Lịch làm việc. Có thể chuyển sang tuần trước/sau.
- Màn phân ca dùng lịch chọn ngày trực quan, nút nhanh Hôm nay/Tuần này/Tuần sau/30 ngày,
  hiển thị số ngày dự kiến phân ca và tên ca kèm giờ bắt đầu/kết thúc để chọn dễ dàng.
- Các ô lọc Từ ngày/Đến ngày hiển thị rộng, có lịch popup dạng lưới với tuần bắt đầu Thứ Hai.
- Một nhân viên không thể có hai ca khác nhau trong cùng một ngày; giao diện báo trước ngày trùng
  và khóa nút lưu, Server từ chối yêu cầu trùng ca.
- Nghỉ phép, quỹ phép, phân ca và duyệt yêu cầu; nhân viên có nút **Hủy đơn** đối với đơn đang chờ
  hoặc đơn đã duyệt nhưng chưa bắt đầu.
- Nút **Gửi Random Check** nằm riêng trong **Xác minh ngẫu nhiên**, cho phép chọn
  nhân viên đang hoạt động; cảnh báo và thông báo được cập nhật qua WebSocket.
- Cảnh báo lỗi rõ ràng cho lỗi nhập liệu, phân quyền, mạng LAN, timeout, cấu hình và lỗi Server.
- Một nút Làm mới để đặt lại bộ lọc, phân trang và tải lại dữ liệu; hỗ trợ xuất Excel có
  tiêu đề, màu sắc, bộ lọc, dòng xen kẽ và định dạng in đẹp; dòng đang chọn được làm nổi bật.
- Design system nhất quán: font Segoe UI dễ đọc, icon native rõ nét, nút/thẻ 3D
  có gradient, viền nổi, bóng đổ và hiệu ứng nhấn; bảng có màu xen kẽ và dòng chọn nổi bật.
  Thanh công cụ cuộn khi thiếu chỗ; cả chế độ sáng/tối đều giữ đúng tương phản màu.
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
Dải mạng mặc định hỗ trợ IPv4 nội bộ, IPv6 loopback, ULA và link-local; địa chỉ IPv4 được
Windows biểu diễn dưới dạng IPv6-mapped sẽ được chuẩn hóa trước khi kiểm tra.
Nếu client kết nối qua Radmin VPN, chỉ thêm `26.0.0.0/8` vào `ALLOWED_NETWORKS` khi server
không mở cổng ra Internet và các client thuộc mạng Radmin đáng tin cậy.

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
.\scripts\run_all.ps1
```

`setup.ps1` tự tạo `server/.env` cùng JWT secret ngẫu nhiên ở lần chạy đầu và không ghi đè
cấu hình hoặc database đã có dữ liệu. Không chép nguyên giá trị `CHANGE_...` trong file mẫu
vào môi trường chạy.

Nếu muốn chạy riêng từng thành phần để gỡ lỗi, mở ba PowerShell và dùng lần lượt:

```powershell
.\.venv\Scripts\python.exe .\server_launcher.py
.\.venv\Scripts\python.exe .\admin_launcher.py
.\.venv\Scripts\python.exe .\client_launcher.py
```

API mặc định: `http://127.0.0.1:8000`; OpenAPI: `http://127.0.0.1:8000/docs`.

Khi chạy bằng `run_all.ps1`, đóng cửa sổ Server sẽ dừng cả Admin và User qua watchdog.
Client trên máy khác vẫn giữ mở khi kết nối LAN bị gián đoạn.

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

## Kiểm thử

```powershell
.\.venv\Scripts\python.exe -m ruff check server client admin scripts tests
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q
```

Trạng thái hiện tại: **126 kiểm thử đạt**, Ruff không phát hiện lỗi.

## Thư mục quan trọng

```text
server/          API, model, migration và nghiệp vụ
client/          Giao diện Client/Admin
scripts/         Cài đặt, chạy, seed và build
tests/           Kiểm thử tự động
docs/            Tài liệu chi tiết
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

Không commit hoặc xóa nhầm `server/.env`, `client/config.json`, database SQLite hay bản sao lưu.

Tài liệu triển khai chi tiết: [docs/DEPLOYMENT_WINDOWS_LAN.md](docs/DEPLOYMENT_WINDOWS_LAN.md).
