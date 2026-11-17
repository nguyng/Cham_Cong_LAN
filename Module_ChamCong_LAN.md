# HỆ THỐNG QUẢN LÝ VÀ CHẤM CÔNG TRỰC TUYẾN ĐỊNH VỊ GEOFENCING THỜI GIAN THỰC
## MÔ TẢ CÁC PHÂN HỆ VÀ MODULE CHỨC NĂNG (HAWA'S FOOD ĐÀ NẴNG)

> **Học phần**: Mạng máy tính / Lập trình mạng  
> **Đơn vị đào tạo**: Khoa Công Nghệ Thông Tin — Trường Đại học Kiến Trúc Đà Nẵng  
> **Người hướng dẫn khoa học**: TS. Đặng Hùng Vĩ  
> **Đơn vị ứng dụng thực tế**: Quán Hawa's Food Đà Nẵng (Chuỗi F&B ẩm thực nhanh và giải khát)  
> **Tên nhóm thực hiện**: Huan rose và dong bon — **Lớp**: 23CT1 — **Khóa**: 2023  
> **Kiến trúc mạng**: Client – Server tập trung (Web Mobile / Desktop App + RESTful API HTTPS + Live WebSocket + UDP Discovery)

---

## 👥 Danh Sách Thành Viên & Phân Công Trách Nhiệm Phân Hệ

| STT | Họ và tên | MSSV | Vai trò đồ án | Phân hệ phụ trách chính | Tác nhân liên đới |
|:---:|---|:---:|---|---|---|
| 1 | **Ngô Đức An** | 114534 | Trưởng nhóm | **MOD-01: Quản trị & Bảo mật hệ thống** | System Admin |
| 2 | **Nguyễn Văn Nguyên** | 115201 | Thành viên | **MOD-02: Cấu hình Quán & Geofencing** | Shop Owner (Chủ quán) |
| 3 | **Trần Đức Trí** | 114889 | Thành viên | **MOD-03: Quản lý Ca làm & Lập lịch phân ca** | Shift Manager (Quản lý ca) |
| 4 | **Vũ Huy Hoàng** | 114776 | Thành viên | **MOD-04: Điểm danh Geofencing & Live WebSocket** | Employee (Nhân viên) |
| 5 | **Nguyễn Ngọc Thương** | 115042 | Thành viên | **MOD-05: Giải trình sai lệch & Khóa sổ công Excel** | Accountant / Timekeeper (Kế toán) |

---

## 🏗️ Tổng Quan 5 Phân Hệ Nghiệp Vụ Cốt Lõi (MOD-01 đến MOD-05)

```text
               ┌─────────────────────────────────────────────────────────┐
               │    HỆ THỐNG QUẢN LÝ & CHẤM CÔNG QUÁN HAWA'S FOOD        │
               └───────────────────────────┬─────────────────────────────┘
                                           │
         ┌───────────────────┬─────────────┴───────┬───────────────────┬───────────────────┐
         ▼                   ▼                     ▼                   ▼                   ▼
     ┌─────────┐         ┌─────────┐           ┌─────────┐         ┌─────────┐         ┌─────────┐
     │ MOD-01  │         │ MOD-02  │           │ MOD-03  │         │ MOD-04  │         │ MOD-05  │
     │Quản trị │         │Cấu hình │           │Quản lý  │         │Điểm danh│         │Giải     │
     │& Bảo mật│         │Quán &   │           │Ca làm & │         │Geofence │         │trình &  │
     │hệ thống │         │Geofence │           │Phân ca  │         │WebSocket│         │Khóa sổ  │
     └─────────┘         └─────────┘           └─────────┘         └─────────┘         └─────────┘
```

---

## 1. PHÂN HỆ MOD-01: QUẢN TRỊ & BẢO MẬT HỆ THỐNG
> 👤 **Người phụ trách**: Ngô Đức An (Trưởng nhóm — MSSV: 114534)  
> 🎯 **Mục tiêu**: Đảm bảo an toàn mạng, xác thực định danh và phân quyền truy cập RBAC.

### 1.1. Module MOD-01-01: Đăng nhập an toàn & Xác thực phiên qua JWT
- **Input**: `username`, `password` (tối thiểu 6 ký tự), IP kết nối.
- **Xử lý**:
  1. Kiểm tra tài khoản trong bảng `users`, xác thực trạng thái `is_active = TRUE`.
  2. Đối chiếu mật khẩu bằng thuật toán băm an toàn (`Argon2` / `bcrypt`). Khóa tài khoản sau 5 lần nhập sai liên tiếp.
  3. Cấp phát Access Token chuẩn JSON Web Token (RFC 7519) chứa `user_id`, `role`, thời hạn hiệu lực 480 phút.
- **Output**: Token JWT, thông tin vai trò người dùng hoặc thông báo từ chối truy cập.

### 1.2. Module MOD-01-02: Phân quyền vai trò người dùng (RBAC Middleware)
- **Cơ chế**: Middleware chặn mọi request, giải mã JWT, kiểm tra quyền theo 5 vai trò:
  - `ADMIN`: Toàn quyền hệ thống, cấu hình tham số mạng, quản trị người dùng.
  - `OWNER` (Chủ quán): Quản lý vị trí quán, toạ độ Geofencing, danh mục ca và xem toàn bộ báo cáo.
  - `MANAGER` (Quản lý ca): Lập lịch phân ca, giám sát Live WebSocket, duyệt giải trình trong phạm vi ca trực.
  - `ACCOUNTANT` (Kế toán đối soát): Đối soát giờ công, phát hiện ca bất thường, khóa sổ kỳ công và xuất Excel.
  - `EMPLOYEE` (Nhân viên): Xem lịch cá nhân, điểm danh Geofencing GPS, gửi đơn giải trình.

### 1.3. Module MOD-01-03: Quản lý hồ sơ tài khoản
- Cấp phát tài khoản mới theo chuẩn mã nhân viên (`NVxxx`).
- Đổi mật khẩu định kỳ, thu hồi token khi người dùng đổi mật khẩu hoặc đăng xuất.

### 1.4. Module MOD-01-04: Giám sát nhật ký an toàn mạng (Audit Trail & Logging)
- Tự động ghi lại các sự kiện an ninh mạng vào bảng `audit_logs`: địa chỉ IP Client, URL endpoint, phương thức HTTP, mã phản hồi, dấu thời gian Server.

---

## 2. PHÂN HỆ MOD-02: CẤU HÌNH QUÁN & GEOFENCING
> 👤 **Người phụ trách**: Nguyễn Văn Nguyên (Thành viên — MSSV: 115201)  
> 🎯 **Mục tiêu**: Thiết lập ranh giới địa lý ảo và hạ tầng mạng điểm danh tại Quán Hawa's Food Đà Nẵng.

### 2.1. Module MOD-02-01: Thiết lập toạ độ địa lý & Ghim bản đồ quán
- **Input**: Tên cơ sở quán, toạ độ vĩ độ (`latitude`), kinh độ (`longitude`), bán kính Geofencing (`radius_meters` = 50m).
- **Xử lý**: Kiểm tra tính hợp lệ toạ độ (vĩ độ thuộc [-90, 90], kinh độ thuộc [-180, 180]), lưu trữ vào bảng `shop_locations`.
- **Output**: Bản ghi địa điểm quán chính thức, hiển thị tâm quán và vòng tròn bán kính 50m trên bản đồ trực quan.

### 2.2. Module MOD-02-02: Đăng ký dải IP & Wi-Fi nội bộ của quán
- Lưu danh sách mạng Wi-Fi hợp lệ của quán vào bảng `shop_wifis` (BSSID, SSID, dải subnet IP nội bộ ví dụ `192.168.1.0/24`).
- Phục vụ cơ chế thẩm định kép (Dual Verification): kết hợp GPS với IP Wi-Fi nội bộ chống Fake GPS.

### 2.3. Module MOD-02-03: Cài đặt quy chế làm việc & Dung sai giờ giấc
- Cấu hình thời gian cho phép điểm danh vào ca sớm tối đa 30 phút (`early_arrival_buffer_minutes = 30`).
- Cấu hình dung sai đi muộn cho phép (ví dụ: tối đa 5 phút không bị phạt công).

---

## 3. PHÂN HỆ MOD-03: QUẢN LÝ CA LÀM & LẬP LỊCH PHÂN CA
> 👤 **Người phụ trách**: Trần Đức Trí (Thành viên — MSSV: 114889)  
> 🎯 **Mục tiêu**: Số hóa lịch làm việc, tự động hóa phân bổ nhân lực và ngăn ngừa chồng chéo ca kíp.

### 3.1. Module MOD-03-01: Quản lý danh mục ca làm việc (Shifts)
- Định nghĩa các ca làm việc của Hawa's Food trong bảng `shifts`:
  - **Ca Sáng (CA1)**: 06:30 – 11:30
  - **Ca Chiều (CA2)**: 11:30 – 17:30
  - **Ca Tối (CA3)**: 17:30 – 23:00
  - **Ca Gãy (CAGAY)**: 10:30 – 14:30 hoặc ca cao điểm cuối tuần.

### 3.2. Module MOD-03-02: Lập lịch phân ca tuần & Kiểm tra xung đột trùng ca
- **Input**: `user_id`, `shift_id`, `work_date`.
- **Xử lý**: Thuật toán quét xung đột thời gian:
  1. Lấy khoảng thời gian [Start_new, End_new] của ca dự kiến gán.
  2. Truy vấn tất cả ca làm việc đã có của nhân viên đó trong cùng ngày `work_date`.
  3. Kiểm tra điều kiện giao thoa: `max(Start_new, Start_old) < min(End_new, End_old)`.
  4. Nếu có xung đột: Server từ chối và báo lỗi *"Nhân viên đã được phân ca trùng khung giờ"*.
  5. Nếu không trùng: Thêm bản ghi vào bảng `schedules` với trạng thái `PUBLISHED`.
- **Output**: Lịch làm việc tuần được công bố, đồng bộ tức thời xuống giao diện của nhân viên.

### 3.3. Module MOD-03-03: Đổi ca & Bàn giao ca trực
- Cho phép nhân viên gửi yêu cầu đổi ca giữa 2 người; Quản lý ca phê duyệt trên giao diện quản trị.

---

## 4. PHÂN HỆ MOD-04: ĐIỂM DANH GEOFENCING & LIVE WEBSOCKET
> 👤 **Người phụ trách**: Vũ Huy Hoàng (Thành viên — MSSV: 114776)  
> 🎯 **Mục tiêu**: Tự động hóa đo khoảng cách toạ độ GPS, xác thực điểm danh an toàn và phát sự kiện thời gian thực.

### 4.1. Module MOD-04-01: Thu thập toạ độ GPS an toàn từ Client
- Client (Web Mobile / Desktop) trích xuất toạ độ người dùng qua W3C Geolocation API: toạ độ `(lat, lng)`, sai số `accuracy`.
- Đóng gói gửi kèm Token JWT và `schedule_id` qua đường truyền mã hóa HTTPS đến Server.

### 4.2. Module MOD-04-02: Engine thẩm định Geofencing Haversine tại Server
- **Công thức lượng giác hình cầu Haversine**:
  - $\Delta\phi = \phi_2 - \phi_1$, $\Delta\lambda = \lambda_2 - \lambda_1$
  - $a = \sin^2(\Delta\phi / 2) + \cos(\phi_1) \cdot \cos(\phi_2) \cdot \sin^2(\Delta\lambda / 2)$
  - $c = 2 \cdot \text{atan2}(\sqrt{a}, \sqrt{1 - a})$
  - $d = R \cdot c$ (với $R = 6.371.000\,\text{m}$)
- **Quy tắc thẩm định**:
  - Nếu $d \le 50\,\text{m}$: Hợp lệ $\rightarrow$ Server ghi nhận `check_in_time`, khoảng cách thực tế, đánh giá trạng thái (`ON_TIME` hoặc `LATE`).
  - Nếu $d > 50\,\text{m}$: Không hợp lệ $\rightarrow$ Từ chối ghi nhận, trả thông báo: *"Bạn đang ở ngoài phạm vi quán (cách tâm quán thực tế, tối đa 50m)"*.

### 4.3. Module MOD-04-03: Check-out cuối ca & Tính tổng giờ công thực tế
- Ghi nhận thời điểm ra ca `check_out_time`, đo lại khoảng cách $d_{out} \le 50\,\text{m}$.
- Tính toán tổng thời gian làm việc thực tế (`work_hours`), tự động phát hiện tình trạng về sớm (`EARLY_LEAVE`).

### 4.4. Module MOD-04-04: Kênh truyền thông hai chiều Live WebSocket (RFC 6455)
- Server duy trì WebSocket Pool (kênh `/api/v1/ws`).
- Ngay khi một nhân viên Check-in hoặc Check-out thành công:
  - Server tạo gói tin JSON chứa họ tên, mã nhân viên, ca làm, khoảng cách, trạng thái.
  - Broadcast gói tin tức thời tới Dashboard Quản lý ca với độ trễ $< 100\,\text{ms}$.
  - Giao diện Dashboard của Quản lý tự cập nhật danh sách có mặt mà không cần F5 / Reload trang.

---

## 5. PHÂN HỆ MOD-05: GIẢI TRÌNH SAI LỆCH & KHÓA SỔ CÔNG EXCEL
> 👤 **Người phụ trách**: Nguyễn Ngọc Thương (Thành viên — MSSV: 115042)  
> 🎯 **Mục tiêu**: Xử lý ngoại lệ chấm công linh hoạt, bảo đảm tính toàn vẹn dữ liệu và trích xuất báo cáo đối soát.

### 5.1. Module MOD-05-01: Gửi đơn giải trình quên bấm công (Attendance Request)
- Áp dụng khi nhân viên quên bấm giờ vào/ra hoặc máy gặp sự cố mạng:
  - Nhân viên chọn ca làm việc, chọn loại giải trình (`MISSING_CHECK_IN`, `MISSING_CHECK_OUT`, `DEVICE_ERROR`).
  - Nhập lý do giải trình, tải kèm ảnh chụp minh chứng (ví dụ camera tại quán).
  - Bản ghi được tạo trong bảng `attendance_requests` với trạng thái `PENDING`.

### 5.2. Module MOD-05-02: Phê duyệt đơn giải trình & Cập nhật giờ công
- Quản lý ca / Kế toán đối chiếu dữ liệu camera và sổ ca:
  - Bấm **Chấp thuận** (`APPROVED`): Hệ thống tự động điền giờ chấm công bổ sung vào bảng `attendances`, tính lại tổng giờ công trong cùng một Database Transaction.
  - Bấm **Từ chối** (`REJECTED`): Nhập lý do từ chối gửi lại nhân viên.

### 5.3. Module MOD-05-03: Cảnh báo tự động các ca chấm công bất thường
- Hệ thống tự động quét và gắn cờ cảnh báo `ABNORMAL` đối với:
  - Ca làm việc có check-in nhưng không có check-out khi ca đã kết thúc quá 2 giờ.
  - Ca có khoảng cách $d$ mấp mé ngưỡng $50\,\text{m}$ kèm toạ độ nhảy bất thường.
  - Ca làm vào/ra cách nhau dưới 15 phút.

### 5.4. Module MOD-05-04: Khóa sổ chấm công kỳ tháng (Monthly Freeze) & Xuất Excel
- **Khóa sổ công (`is_locked = TRUE`)**:
  - Cuối kỳ tháng (ngày chốt công), Kế toán kích hoạt chức năng Khóa sổ.
  - Toàn bộ các bản ghi `attendances` của tháng được bật cờ `is_locked = TRUE`.
  - Mọi thao tác thêm/sửa/xóa hoặc duyệt bù sau khi đã khóa sổ đều bị hệ thống chặn tuyệt đối nhằm bảo đảm tính toàn vẹn kiểm toán.
- **Xuất báo cáo bảng công Excel (.xlsx)**:
  - Sử dụng thư viện xử lý bảng tính chuẩn để sinh file Excel báo cáo:
    - Tiêu đề: *BẢNG TỔNG HỢP CÔNG THÁNG — QUÁN HAWA'S FOOD ĐÀ NẴNG*.
    - Bảng chi tiết: Họ tên, Mã NV, Tổng ca phân bổ, Ca đúng giờ, Số lần đi muộn, Về sớm, Số ca giải trình được duyệt, Tổng số giờ công thực nhận.
    - Định dạng trực quan: màu sắc nổi bật các ca trễ, tự động căn lề in chuẩn khổ giấy A4 ngang.

---

## 📋 Bảng Quy Tắc Nghiệp Vụ Cốt Lõi (Business Rules - BR)

| Mã BR | Tên quy tắc nghiệp vụ | Định nghĩa & Tiêu chí xử lý kỹ thuật |
|---|---|---|
| **BR-01** | Bán kính Geofencing chuẩn | Điểm danh chỉ hợp lệ khi khoảng cách Haversine $d \le 50\,\text{m}$. Nếu $d > 50\,\text{m}$, hệ thống từ chối và thông báo khoảng cách thực tế. |
| **BR-02** | Khung giờ vào ca cho phép | Nhân viên được phép check-in sớm tối đa 30 phút trước giờ ca bắt đầu. Bấm sớm hơn 30 phút sẽ bị chặn. |
| **BR-03** | Phân loại trạng thái chấm công | - Đến đúng giờ hoặc trong dung sai: `ON_TIME`  <br>- Đến muộn sau giờ quy định: `LATE`  <br>- Rời ca trước giờ kết thúc: `EARLY_LEAVE`  <br>- Không có bản ghi điểm danh: `ABSENT` |
| **BR-04** | Đóng băng dữ liệu khóa sổ | Khi `is_locked = TRUE`, bản ghi chấm công chuyển sang trạng thái chỉ đọc (Read-only), không ai (kể cả Admin) được tự ý sửa đổi. |
| **BR-05** | Quy chế duyệt đơn giải trình | Đơn giải trình chỉ được duyệt khi trạng thái ca chưa bị khóa sổ (`is_locked = FALSE`) và phải có lý do kèm ảnh đối soát hợp lệ. |
| **BR-06** | Thẩm định mạng kép (Dual Check) | Khi nhân viên bật GPS, hệ thống ưu tiên toạ độ vệ tinh. Nếu thiết bị không có GPS, hệ thống kiểm tra IP kết nối phải thuộc mạng Wi-Fi của quán. |

---

## 🗄️ Thiết Kế Cơ Sở Dữ Liệu (8 Bảng CSDL Chuẩn)

Hệ thống quản lý dữ liệu tập trung qua 8 bảng quan hệ:

1. **`users`**: Lưu hồ sơ nhân sự, tài khoản, mật khẩu hash Argon2, vai trò (`ADMIN`, `OWNER`, `MANAGER`, `ACCOUNTANT`, `EMPLOYEE`).
2. **`shop_locations`**: Toạ độ GPS vĩ độ/kinh độ cơ sở Hawa's Food, bán kính 50m.
3. **`shop_wifis`**: Danh mục IP subnet, SSID mạng Wi-Fi tại cơ sở quán.
4. **`shifts`**: Danh mục các ca làm việc tiêu chuẩn (CA1, CA2, CA3, CAGAY).
5. **`schedules`**: Lịch phân ca chi tiết cho từng nhân viên theo từng ngày (`work_date`).
6. **`attendances`**: Dữ liệu điểm danh thực tế (giờ vào, giờ ra, toạ độ, khoảng cách Haversine, trạng thái, cờ `is_locked`).
7. **`attendance_requests`**: Đơn giải trình bổ sung giờ công kèm minh chứng và lý do.
8. **`audit_logs`**: Nhật ký an toàn thông tin, lưu trữ dấu vết truy cập mạng và các thao tác nhạy cảm.

---

## 🗺️ Danh Mục 13 Trang Sơ Đồ Kỹ Thuật Draw.io (Phụ Lục A)

Hệ thống được thiết kế và mô hình hóa đầy đủ trên 13 trang sơ đồ kỹ thuật:
1. **Trang 1**: Sơ đồ luồng dữ liệu (DFD Mức 0 Context Diagram & Mức 1 phân rã 5 tiến trình).
2. **Trang 2**: Sơ đồ ca sử dụng (Use Case Diagram tổng quát toàn hệ thống).
3. **Trang 3**: Sơ đồ quan hệ thực thể (Physical ERD 8 bảng CSDL chuẩn vật lý).
4. **Trang 4**: Sơ đồ quy trình tổng thể (Workflow Activity Diagram vòng đời chấm công khép kín).
5. **Trang 5**: Sơ đồ quy trình chi tiết điểm danh Geofencing Haversine 50m.
6. **Trang 6**: Sơ đồ quy trình lập lịch phân ca và thuật toán chống trùng ca.
7. **Trang 7**: Sơ đồ quy trình giám sát trực tiếp Live WebSocket (RFC 6455).
8. **Trang 8**: Sơ đồ quy trình giải trình sai lệch và phê duyệt quên bấm công.
9. **Trang 9**: Sơ đồ quy trình khóa sổ kỳ công và xuất bảng công Excel.
10. **Trang 10**: Sơ đồ kiến trúc liên kết phân hệ chức năng (Component Integration).
11. **Trang 11**: Sơ đồ tuần tự (UML Sequence Diagram chi tiết 7 Lifelines).
12. **Trang 12**: Sơ đồ máy trạng thái (UML State Machine Diagram vòng đời ca làm việc).
13. **Trang 13**: Sơ đồ phân rã chức năng dạng khối hình cây (FDD 5 phân hệ và 21 module con).
