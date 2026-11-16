# Triển khai Windows trong mạng LAN với SQLite

## 1. Chuẩn bị máy Server

1. Cài Python 3.12 x64 nếu chạy mã nguồn. SQLite đã tích hợp trong Python, không cần cài database server.
2. Chạy `scripts\setup.ps1`; dependency chỉ được cài trong `.venv`, `server\.env` được tạo
   với JWT secret ngẫu nhiên và dữ liệu mẫu chỉ được nạp nếu database chưa có tài khoản.
3. Giữ cấu hình database:

   ```env
   DATABASE_URL=sqlite:///./data/attendance.db
   ```

4. Chạy `scripts\run_all.ps1` để mở Server, Admin và User. Server tự chạy migration trước khi
   nhận kết nối.

SQLite được cấu hình tự động với foreign keys, WAL, synchronous NORMAL và thời gian chờ khóa 30 giây. Tệp database phải nằm trên ổ đĩa cục bộ của máy Server. Không đặt `.db` trên SMB/OneDrive/Google Drive và không chia sẻ tệp cho Client; Client chỉ truy cập HTTPS API.

## 2. Chạy bằng terminal

Lệnh được khuyến nghị trên máy chạy cả ba thành phần:

```powershell
.\scripts\run_all.ps1
```

Script chờ Server sẵn sàng rồi mở hai giao diện. Watchdog chỉ theo dõi đúng các cây tiến trình
vừa tạo và dừng Admin/User khi cửa sổ Server đóng, kể cả lúc chưa đăng nhập. Muốn chạy từng
thành phần để gỡ lỗi, dùng `server_launcher.py`, `admin_launcher.py` và `client_launcher.py`.

## 3. HTTPS nội bộ

Dùng chứng chỉ do CA nội bộ cấp cho tên DNS/IP máy Server. Cài CA gốc vào `Trusted Root Certification Authorities` trên từng Client. Không tắt `verify_tls` trong vận hành.

## 4. Windows Firewall

Mở PowerShell **Run as Administrator** trên Server và thay subnet đúng của công ty:

```powershell
.\scripts\configure_firewall.ps1 -RemoteSubnet 192.168.1.0/24
```

Script chỉ tạo rule TCP/8000 và UDP/37020 cho `Domain,Private`, giới hạn đúng subnet được nhập. Script không tạo rule Public, không cấu hình port-forwarding và không mở cổng ra Internet.

## 5. Chạy Client

- Sao chép `client\config.example.json` thành `config.json`, đặt `server_url`, rồi chạy Client từ mã nguồn.
- Có thể dùng nút **Tìm Server** qua UDP discovery nếu chưa biết địa chỉ máy Server.
- Mọi Client gọi Server; không Client nào mở `attendance.db`.

## 6. Sao lưu và khôi phục

API Admin dùng SQLite Online Backup API nên có thể tạo bản sao nhất quán khi Server đang chạy. Mỗi tệp backup được kiểm tra bằng `PRAGMA integrity_check`.

Khi khôi phục:

1. Đặt cửa sổ bảo trì và cho Client đăng xuất.
2. Tạo thêm một bản backup hiện trạng.
3. Chọn tệp `.sqlite3` trong đúng `BACKUP_DIRECTORY`.
4. Server kiểm tra toàn vẹn trước khi chép dữ liệu vào database vận hành.
5. Khởi động lại Server, chạy health check và đối chiếu số bản ghi.

Sao chép thư mục `backups` định kỳ sang thiết bị lưu trữ khác sau khi backup hoàn tất; không chạy trực tiếp database vận hành từ thiết bị đó.

## 7. Kiểm thử chấp nhận trên hai máy

Từ máy Client thật, chạy kiểm tra health, xác minh chuỗi chứng chỉ, UDP discovery, đăng nhập, WebSocket ping/pong và logout:

```powershell
.\.venv\Scripts\python.exe .\scripts\acceptance_lan.py `
  --server-url https://attendance.company.local:8000 `
  --username nhanvien01
```

Nếu CA chưa được cài vào Windows trust store của máy nghiệm thu, có thể chỉ rõ file PEM bằng `--ca-file C:\certs\company-root-ca.pem`. Không dùng chế độ bỏ qua TLS.

- Client thứ hai khám phá đúng Server và xác minh chứng chỉ HTTPS.
- Hai tài khoản check-in đồng thời không tạo bản ghi trùng.
- Ngắt rồi nối lại mạng: trạng thái và WebSocket tự phục hồi.
- Random Check đến đúng Client; hết hạn chỉ tạo cảnh báo xem xét.
- Admin xuất Excel/PDF, backup, kiểm tra toàn vẹn và restore trên database nghiệm thu.

Các bước này phải thực hiện trên thiết bị thật; unit/API test không thay thế kiểm thử LAN vật lý.
