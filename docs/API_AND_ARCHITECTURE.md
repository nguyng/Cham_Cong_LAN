# Kiến Trúc Và API — Hệ Thống Chấm Công Hawa's Food Đà Nẵng

> **Dự án**: Xây dựng hệ thống quản lý và chấm công trực tuyến định vị Geofencing thời gian thực cho Quán Hawa's Food Đà Nẵng  
> **Người hướng dẫn khoa học**: TS. Đặng Hùng Vĩ — Nhóm: Huan rose và dong bon (Lớp 23CT1)  
> **Tài liệu tham chiếu**: [BAO_CAO_DO_AN_HAWAS_FOOD_13_SO_DO_HOAN_CHINH.docx](../BAO_CAO_DO_AN_HAWAS_FOOD_13_SO_DO_HOAN_CHINH.docx), [phan_tich_du_an_cham_cong.md](../phan_tich_du_an_cham_cong.md), [Module_ChamCong_LAN.md](../Module_ChamCong_LAN.md)

---

## 1. Mô Hình Kiến Trúc Tổng Thể

```text
       ┌─────────────────────────────────────────────────────────┐
       │   Client: Web Mobile / AttendanceClient / Admin (Qt)    │
       └────────────────────────────┬────────────────────────────┘
                                    │ HTTPS (REST API) + WSS (Live WebSocket) + UDP (Discovery)
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │     AttendanceServer (FastAPI / Uvicorn - Cổng 8000)    │
       ├─────────────────────────────────────────────────────────┤
       │ ├── MOD-01: Quản trị & Bảo mật hệ thống (JWT, RBAC)     │
       │ ├── MOD-02: Cấu hình Quán & Geofencing (Tọa độ, Wi-Fi)  │
       │ ├── MOD-03: Quản lý Ca làm & Phân ca (Chống trùng ca)   │
       │ ├── MOD-04: Điểm danh Geofencing (Haversine <= 50m)     │
       │ └── MOD-05: Giải trình sai lệch & Khóa sổ Excel         │
       └────────────────────────────┬────────────────────────────┘
                                    │ SQLAlchemy 2.0 + ACID Transactions
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │   SQLite Database Cục Bộ (WAL Mode + Foreign Keys)      │
       │   Đường dẫn: server/data/attendance.db                  │
       └─────────────────────────────────────────────────────────┘
```

---

## 2. Danh Sách 5 Thực Thể Cốt Lõi & 8 Bảng CSDL

Hệ thống quản lý thông tin qua 5 thực thể chính (Entities) và 8 bảng CSDL vật lý:

| Thực thể | Bảng CSDL | Mô tả nghiệp vụ |
|---|---|---|
| **ENT-01** | `users` | Hồ sơ nhân sự, tài khoản, mật khẩu băm Argon2, 5 vai trò RBAC |
| **ENT-02** | `shop_locations`, `shop_wifis` | Toạ độ định vị Geofencing ($R = 50\,\text{m}$) và danh mục IP Wi-Fi nội bộ quán |
| **ENT-03** | `shifts` | Danh mục ca làm việc (CA1 Sáng, CA2 Chiều, CA3 Tối, CAGAY Ca gãy) |
| **ENT-04** | `schedules` | Kế hoạch làm việc được phân bổ theo ngày cho từng nhân viên |
| **ENT-05** | `attendances`, `attendance_requests` | Kết quả điểm danh thực tế (giờ vào/ra, khoảng cách, cờ `is_locked`) và đơn giải trình |
| *Hệ thống* | `audit_logs` | Nhật ký an toàn mạng, ghi vết truy cập và thay đổi nhạy cảm |

---

## 3. Các Nhóm Đường Dẫn API Chính (FastAPI OpenAPI)

OpenAPI tương tác trực quan có tại: `http://127.0.0.1:8000/docs`.

### 3.1. Phân hệ MOD-01: Xác thực & Quản trị
- `POST /api/v1/auth/login`: Xác thực tài khoản, cấp phát Access Token JWT.
- `POST /api/v1/auth/logout`: Thu hồi token, kết thúc phiên làm việc.
- `POST /api/v1/auth/change-password`: Đổi mật khẩu tài khoản.
- `GET /api/v1/employees`, `POST /api/v1/employees`: Quản lý danh sách nhân sự quán.

### 3.2. Phân hệ MOD-02: Cấu hình Quán & Geofencing
- `GET/PUT /api/v1/system/settings`: Cấu hình toạ độ quán Hawa's Food ($lat, lng$), bán kính $50\,\text{m}$.
- `GET /api/v1/system/client-connections`: Danh sách máy trạm kết nối trong mạng.

### 3.3. Phân hệ MOD-03: Quản lý Ca làm & Phân ca
- `GET/POST /api/v1/shifts`: Danh mục ca làm việc (khung giờ bắt đầu, kết thúc).
- `GET/POST /api/v1/shift-assignments` (hoặc `/schedules`): Lập lịch phân ca theo tuần, tự động kiểm tra xung đột trùng ca.

### 3.4. Phân hệ MOD-04: Điểm danh Geofencing & Live WebSocket
- `POST /api/v1/attendance/check-in`: Điểm danh vào ca; Server thẩm định toạ độ bằng giải thuật Haversine ($d \le 50\,\text{m}$).
- `POST /api/v1/attendance/check-out`: Điểm danh ra ca; tính toán tổng giờ làm việc thực tế (`work_hours`).
- `GET /api/v1/attendance/history`: Xem lịch sử điểm danh cá nhân hoặc toàn quán.
- `GET /api/v1/ws`: Kênh WebSocket Full-duplex phát sự kiện chấm công thời gian thực $(< 100\,\text{ms})$ lên Dashboard Quản lý ca.

### 3.5. Phân hệ MOD-05: Giải trình, Khóa sổ & Báo cáo
- `POST /api/v1/attendance/adjustments` (hoặc requests): Gửi đơn giải trình quên bấm công kèm lý do/ảnh.
- `POST /api/v1/attendance/adjustments/{id}/approve`: Quản lý phê duyệt giải trình, tự động bù giờ công.
- `POST /api/v1/leaves`, `POST /api/v1/leaves/{id}/cancel`: Quản lý và hủy đơn nghỉ phép.
- `GET /api/v1/reports/summary`, `GET /api/v1/reports/excel`: Tổng hợp ngày công và xuất file Excel (.xlsx).
- `POST /api/v1/admin/backup`, `/admin/restore/{filename}`: Sao lưu và khôi phục SQLite online.

---

## 4. Cơ Chế Thẩm Định Toạ Độ Geofencing (Haversine)

Công thức tính khoảng cách hình cầu Haversine chạy hoàn toàn tại Server:
$$\Delta\phi = \phi_2 - \phi_1, \quad \Delta\lambda = \lambda_2 - \lambda_1$$
$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)$$
$$d = R \cdot c \quad (\text{với } R = 6.371.000\,\text{m})$$

- Nếu $d \le 50\,\text{m}$: Bản ghi chấm công hợp lệ $\rightarrow$ ghi nhận vào CSDL và broadcast qua WebSocket.
- Nếu $d > 50\,\text{m}$: Server từ chối ghi nhận và gửi thông báo lỗi kèm khoảng cách thực tế đang cách quán.
- Khi không có GPS: Hệ thống kích hoạt cơ chế dự phòng kiểm tra IP Client phải thuộc mạng Wi-Fi nội bộ của quán (`ALLOW_LAN_IP_LOCATION_FALLBACK`).

---

## 5. An Toàn Dữ Liệu SQLite & Toàn Vẹn Kiểm Toán

1. **Khóa sổ kỳ công (`is_locked = TRUE`)**: Sau khi kết thúc kỳ tháng và kiểm toán xong, dữ liệu điểm danh được đóng băng, chuyển sang chế độ chỉ đọc.
2. **SQLite WAL Mode**: Tệp CSDL nằm cục bộ trên máy chủ Server, bật `PRAGMA journal_mode=WAL;` và `PRAGMA foreign_keys=ON;` phục vụ đồng thời nhiều Client mà không gây khóa chết (Deadlock).
3. **Idempotency Key**: Mọi request check-in/out gửi lên đều có khóa định danh duy nhất chống nhân đôi bản ghi khi mạng chập chờn.
