# Hệ Thống Chấm Công Trực Tuyến Hawa's Food Đà Nẵng — Hướng Dẫn Kỹ Thuật Python

> **Học phần**: Mạng máy tính / Lập trình mạng  
> **Đơn vị đào tạo**: Khoa Công Nghệ Thông Tin — Trường Đại học Kiến Trúc Đà Nẵng  
> **Người hướng dẫn khoa học**: TS. Đặng Hùng Vĩ  
> **Đề tài**: Xây dựng hệ thống quản lý và chấm công trực tuyến định vị Geofencing thời gian thực cho Quán Hawa's Food Đà Nẵng  
> **Nhóm thực hiện**: Huan rose và dong bon (Lớp 23CT1)  
> **Thành viên**: Ngô Đức An (Trưởng nhóm), Nguyễn Văn Nguyên, Trần Đức Trí, Nguyễn Ngọc Thương, Vũ Huy Hoàng  
> **Tài liệu phân tích chính thức**: [BAO_CAO_DO_AN_HAWAS_FOOD_13_SO_DO_HOAN_CHINH.docx](BAO_CAO_DO_AN_HAWAS_FOOD_13_SO_DO_HOAN_CHINH.docx), [phan_tich_du_an_cham_cong.md](phan_tich_du_an_cham_cong.md) và [Module_ChamCong_LAN.md](Module_ChamCong_LAN.md)

---

## 1. Kiến Trúc Triển Khai Thực Tế

Toàn bộ hệ thống được xây dựng và tối ưu hoàn toàn trên nền tảng **Python hiện đại**:
- **Backend API**: FastAPI + Uvicorn (Cổng TCP `8000`, WebSocket `/api/v1/ws`, UDP Discovery `37020`).
- **Giao diện Client/Admin**: PySide6 (Qt) Native Desktop Application (`AttendanceClient` và `AttendanceAdmin`).
- **Cơ sở dữ liệu**: SQLite tập trung tại máy Server (`server/data/attendance.db`) với chế độ WAL (Write-Ahead Logging), Foreign Keys và ACID Transaction.
- **Bảo mật & Định danh**: JWT Token (RFC 7519), mã hóa mật khẩu Argon2/bcrypt, RBAC Middleware 5 vai trò.
- **Định vị Geofencing**: Giải thuật khoảng cách hình cầu Haversine chạy tại Server với bán kính chuẩn $R = 50\,\text{m}$ quanh cơ sở Hawa's Food Đà Nẵng.

---

## 2. Khởi Động Nhanh Cho Lập Trình Viên

### Bước 1: Chuẩn bị môi trường và cấu hình
```powershell
.\scripts\setup.ps1
if (-not (Test-Path 'server\.env')) { Copy-Item 'server\.env.example' 'server\.env' }
```

### Bước 2: Nâng cấp CSDL và nạp dữ liệu kiểm thử Hawa's Food
```powershell
cd server
..\.venv\Scripts\python.exe -m alembic upgrade head
cd ..
.\.venv\Scripts\python.exe .\scripts\seed_sample_data.py --database .\server\data\attendance.db
```

### Bước 3: Khởi động Server
```powershell
.\.venv\Scripts\python.exe server_launcher.py
```
*(Server chạy tại `http://127.0.0.1:8000`, tài liệu Swagger UI tại `http://127.0.0.1:8000/docs`)*

### Bước 4: Mở ứng dụng Nhân viên & Quản trị (Ở cửa sổ Terminal riêng)
- **Giao diện Nhân viên (Attendance Client)**:
  ```powershell
  .\.venv\Scripts\python.exe client_launcher.py
  ```
- **Giao diện Quản trị / Quản lý ca (Attendance Admin)**:
  ```powershell
  .\.venv\Scripts\python.exe admin_launcher.py
  ```

---

## 3. Tài Khoản Kiểm Thử Nghiệp Vụ Có Sẵn

Database đã được nạp sẵn bộ dữ liệu mẫu chuẩn của quán Hawa's Food:

| Vai trò | Tên đăng nhập | Mật khẩu | Phạm vi & Đặc quyền |
|---|---|---|---|
| **System Admin** | `admin` | `123456` | Toàn quyền cấu hình hệ thống, quản trị tài khoản, xem Audit Log |
| **Quản lý ca / Shop Owner** | `manage` | `123456` | Lập lịch ca tuần, duyệt giải trình, xem Live WebSocket Monitor |
| **Nhân viên (Phục vụ)** | `user1` | `123456` | Xem lịch làm, điểm danh Geofencing GPS, nộp đơn giải trình |
| **Nhân viên (Pha chế)** | `user2` | `123456` | Xem lịch làm, điểm danh Geofencing GPS, nộp đơn giải trình |
| **Nhân viên (Thu ngân)** | `user3` | `123456` | Xem lịch làm, điểm danh Geofencing GPS, nộp đơn giải trình |

---

## 4. Kiểm Thử Tự Động & Đóng Gói

```powershell
# Kiểm tra định dạng và chuẩn mã nguồn
.\.venv\Scripts\python.exe -m ruff check server client admin scripts tests

# Chạy toàn bộ 101 unit/integration test cases
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider

# Đóng gói portable độc lập
.\scripts\build_portable.ps1
```

Gói portable không cần cài đặt Python trên máy người dùng, nằm tại:
- `dist_portable\AttendanceServer`: Gói máy chủ chạy tại quán.
- `dist_portable\AttendanceClient`: Gói ứng dụng nhân viên.
- `dist_portable\AttendanceAdmin`: Gói ứng dụng quản lý ca / kế toán.
