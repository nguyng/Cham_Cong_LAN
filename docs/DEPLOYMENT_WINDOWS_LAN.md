# Triển khai Windows trong mạng LAN với SQLite

## 1. Chuẩn bị máy Server

1. Cài Python 3.12 x64 nếu chạy mã nguồn. SQLite đã tích hợp trong Python, không cần cài database server.
2. Chạy `scripts\setup.ps1`; dependency chỉ được cài trong `.venv` của dự án.
3. Sao chép `server\.env.example` thành `server\.env` và đặt một `JWT_SECRET` ngẫu nhiên tối thiểu 32 ký tự.
4. Giữ cấu hình database:

   ```env
   DATABASE_URL=sqlite:///./data/attendance.db
   ```

5. Tại thư mục `server`, chạy migration: `..\.venv\Scripts\python.exe -m alembic upgrade head`.
6. Tạo Admin đầu tiên:

   ```powershell
   ..\.venv\Scripts\python.exe ..\scripts\bootstrap_admin.py `
     --username admin --employee-code AD001 `
     --name "Quản trị" --email admin@company.local
   ```

SQLite được cấu hình tự động với foreign keys, WAL, synchronous NORMAL và thời gian chờ khóa 30 giây. Tệp database phải nằm trên ổ đĩa cục bộ của máy Server. Không đặt `.db` trên SMB/OneDrive/Google Drive và không chia sẻ tệp cho Client; Client chỉ truy cập HTTPS API.

## 2. Bản đóng gói

Khuyến nghị dùng nguyên thư mục `dist_portable\AttendanceServer` trên Server và các thư mục portable tương ứng trên Client/Admin. Bản portable không tự giải nén khi chạy nên tương thích tốt hơn với Endpoint Protection. Không lấy riêng file `.exe` ra khỏi thư mục `_internal` đi kèm.

Đặt các tệp theo cấu trúc:

```text
C:\LANAttendance\
├── AttendanceServer.exe
├── server.env
├── data\
├── backups\
└── certs\
```

Với bản `.exe`, tệp cấu hình phải tên `server.env` và nằm cạnh `AttendanceServer.exe`:

```env
ENVIRONMENT=production
DATABASE_URL=sqlite:///./data/attendance.db
JWT_SECRET=THAY_BANG_CHUOI_NGAU_NHIEN_TOI_THIEU_32_KY_TU
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
BACKUP_DIRECTORY=backups
TLS_CERT_FILE=C:\LANAttendance\certs\server.crt
TLS_KEY_FILE=C:\LANAttendance\certs\server.key
```

Không đóng gói database, JWT secret hoặc chứng chỉ riêng vào tệp thực thi.

Server tự chạy Alembic migration khi khởi động. Sau lần chạy đầu, tạo tài khoản quản trị mà không cần cài Python:

```powershell
.\AttendanceServer.exe bootstrap-admin `
  --username admin --employee-code AD001 `
  --name "Quản trị" --email admin@company.local
```

Mật khẩu được nhập hai lần ở chế độ ẩn và chỉ lưu dưới dạng Argon2 hash. Sau đó chạy `AttendanceServer.exe` không có tham số để mở dịch vụ.

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
- Với bản đóng gói, đặt `config.json` cạnh ứng dụng theo hướng dẫn phát hành hoặc dùng nút **Tìm Server** qua UDP discovery.
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
