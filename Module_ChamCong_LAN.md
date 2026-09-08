# PHẦN MỀM CHẤM CÔNG TRÊN MẠNG LAN
## Mô Tả Các Module Chức Năng

> **Môn học**: Lập Trình Mạng  
> **Công nghệ**: Spring Boot + React + MySQL + WebSocket  
> **Môi trường**: Mạng nội bộ LAN (không cần Internet)

---

## Module 1: Chấm Công (Attendance)

Trung tâm của hệ thống — ghi nhận toàn bộ hoạt động vào/ra của nhân viên theo thời gian thực.

### 1.1. Chấm Công Vào / Ra
1.1.1. Nhân viên đăng nhập và bấm nút **"Chấm Công Vào"** — hệ thống tự động ghi nhận giờ vào, địa chỉ IP máy tính.  
1.1.2. Cuối ca, nhân viên bấm **"Chấm Công Ra"** — hệ thống tính tổng số giờ làm trong ngày.  
1.1.3. Tự động ghi nhận trạng thái: **Đúng giờ / Đi muộn / Về sớm** dựa trên ca làm việc đã được phân công.

### 1.2. Giới Hạn IP Chấm Công *(Điểm khác biệt)*
1.2.1. Chỉ cho phép chấm công từ các địa chỉ IP nằm trong dải IP nội bộ của công ty (VD: `192.168.1.x`).  
1.2.2. Khi nhân viên cố gắng chấm công từ IP bên ngoài → hệ thống từ chối và ghi log cảnh báo.  
1.2.3. Admin có thể cấu hình danh sách IP được phép chấm công.

### 1.3. Random Check — Xác Nhận Hiện Diện Ngẫu Nhiên *(Điểm khác biệt của app)*
1.3.1. Hệ thống tự động gửi thông báo bất ngờ đến màn hình nhân viên trong khung giờ làm việc.  
1.3.2. Nhân viên phải bấm **"Xác nhận tôi đang làm việc"** trong vòng X phút (Admin tự cấu hình).  
1.3.3. Nếu không phản hồi trong thời gian quy định → tự động cảnh báo Manager qua Dashboard real-time.  
1.3.4. Lịch sử các lần Random Check được lưu lại để Manager xem xét.

### 1.4. Phát Hiện & Gắn Cờ Bất Thường *(Điểm khác biệt)*
1.4.1. Tự động gắn cờ ⚠️ các ca chấm công đáng ngờ: vào/ra cách nhau dưới 10 phút, chấm công ngoài giờ quy định.  
1.4.2. Báo cáo danh sách các ca bất thường để Manager kiểm tra cuối ngày/tuần.

---

## Module 2: Quản Lý Nhân Sự (Human Resource Management)

Tổ chức cơ cấu nhân sự, phân công công việc và quản lý thông tin nhân viên.

### 2.1. Quản Lý Nhân Viên
2.1.1. Thêm / Sửa / Xóa thông tin nhân viên (Họ tên, Mã NV, Email, Số điện thoại, Phòng ban).  
2.1.2. Tìm kiếm và lọc nhân viên theo phòng ban, ca làm việc, trạng thái.  
2.1.3. Mỗi nhân viên được cấp tài khoản đăng nhập riêng với vai trò (Employee / Manager / Admin).

### 2.2. Quản Lý Phòng Ban
2.2.1. Tạo / Sửa / Xóa các phòng ban trong công ty.  
2.2.2. Gán nhân viên vào phòng ban, gán Manager phụ trách từng phòng.  
2.2.3. Xem danh sách nhân viên theo từng phòng ban.

### 2.3. Quản Lý Ca Làm Việc
2.3.1. Tạo các ca làm việc: Ca sáng, Ca chiều, Ca tối, Ca hành chính... với giờ bắt đầu/kết thúc cụ thể.  
2.3.2. Phân ca cho từng nhân viên theo tuần hoặc theo tháng.  
2.3.3. Xem lịch phân ca dưới dạng bảng (theo tuần/tháng).

---

## Module 3: Quản Lý Nghỉ Phép (Leave Management)

Tự động hóa luồng: **Xin phép → Duyệt → Cập nhật chuyên cần**.

### 3.1. Xin Nghỉ Phép
3.1.1. Nhân viên tạo đơn xin nghỉ: chọn loại nghỉ (Nghỉ phép, Nghỉ ốm, Nghỉ không lương...), ngày bắt đầu, ngày kết thúc, lý do.  
3.1.2. Đơn được gửi tự động đến Manager phụ trách qua hệ thống thông báo real-time (WebSocket).  
3.1.3. Nhân viên theo dõi trạng thái đơn: **Chờ duyệt / Đã duyệt / Bị từ chối**.

### 3.2. Duyệt Nghỉ Phép (Manager)
3.2.1. Manager xem danh sách đơn nghỉ phép của phòng đang chờ duyệt.  
3.2.2. Chấp thuận hoặc từ chối kèm lý do — nhân viên nhận thông báo ngay lập tức.  
3.2.3. Khi duyệt, hệ thống tự động cập nhật số ngày phép còn lại của nhân viên đó.

### 3.3. Theo Dõi Ngày Phép
3.3.1. Mỗi nhân viên được xem số ngày phép còn lại trong năm.  
3.3.2. Admin cấu hình số ngày phép tối đa theo chính sách công ty.  
3.3.3. Cảnh báo khi nhân viên đã dùng hết ngày phép.

---

## Module 4: Báo Cáo & Thống Kê (Reports & Analytics)

Tổng hợp dữ liệu chuyên cần — đầu vào để tính lương và đánh giá hiệu suất.

### 4.1. Báo Cáo Theo Ngày
4.1.1. Danh sách nhân viên có mặt / vắng mặt / đi muộn trong ngày.  
4.1.2. Xem chi tiết giờ vào/ra của từng người.  
4.1.3. Dashboard real-time: hiển thị ai đang có mặt tại thời điểm hiện tại.

### 4.2. Báo Cáo Theo Tháng
4.2.1. Tổng hợp số ngày công, số giờ làm, số lần đi muộn của từng nhân viên.  
4.2.2. Thống kê theo phòng ban: phòng nào chuyên cần nhất.  
4.2.3. Liệt kê các ca Random Check không được phản hồi trong tháng.

### 4.3. Xuất Báo Cáo
4.3.1. Xuất file **Excel** (.xlsx) danh sách chuyên cần theo tháng để tính lương (dùng Apache POI).  
4.3.2. Xuất file **PDF** bảng tổng hợp ngày công.  
4.3.3. Lọc báo cáo theo phòng ban, ca làm, khoảng thời gian tùy chọn.

---

## Module 5: Hệ Thống & Bảo Mật (System & Security)

Nền tảng vận hành toàn bộ hệ thống trên mạng LAN.

### 5.1. Xác Thực & Phân Quyền
5.1.1. Đăng nhập bằng tài khoản nội bộ — xác thực qua **JWT Token**.  
5.1.2. 3 cấp quyền: **Employee** (chấm công, xem cá nhân) → **Manager** (quản lý phòng, duyệt phép) → **Admin** (toàn quyền).  
5.1.3. Token hết hạn sau thời gian quy định, yêu cầu đăng nhập lại.

### 5.2. Triển Khai Trên Mạng LAN *(Điểm khác biệt)*
5.2.1. **1 máy chủ duy nhất** trong công ty chạy Spring Boot (cổng 8080) + MySQL.  
5.2.2. Toàn bộ nhân viên truy cập qua trình duyệt bằng IP nội bộ (VD: `http://192.168.1.100:8080`).  
5.2.3. **Không cần Internet, không phụ thuộc dịch vụ bên ngoài** — dữ liệu hoàn toàn nội bộ.

### 5.3. Thông Báo Real-time (WebSocket)
5.3.1. Khi nhân viên chấm công → Dashboard Manager cập nhật ngay không cần F5.  
5.3.2. Khi có đơn nghỉ phép mới → Manager nhận thông báo tức thì.  
5.3.3. Khi Random Check được kích hoạt → Popup hiện trên màn hình nhân viên ngay lập tức.

### 5.4. Nhật Ký Hệ Thống (Audit Log)
5.4.1. Ghi lại toàn bộ hoạt động quan trọng: đăng nhập, chấm công, duyệt đơn, thay đổi cài đặt.  
5.4.2. Admin xem nhật ký để kiểm tra bảo mật và truy vết sự cố.  
5.4.3. Cảnh báo khi phát hiện đăng nhập từ IP lạ hoặc ngoài giờ hành chính.

---

## Tóm Tắt — Ma Trận Module

| Module | Chức năng chính | Điểm độc đáo |
|--------|----------------|-------------|
| **Module 1** — Chấm Công | Vào/Ra, tự động nhận diện muộn/sớm | 🌟 Giới hạn IP, Random Check, Gắn cờ bất thường |
| **Module 2** — Nhân Sự | CRUD nhân viên, phòng ban, ca làm | ➖ Học từ HRM thương mại |
| **Module 3** — Nghỉ Phép | Xin phép → Duyệt → Cập nhật tự động | 🌟 Thông báo real-time qua WebSocket |
| **Module 4** — Báo Cáo | Thống kê ngày công, xuất Excel/PDF | 🌟 Báo cáo Random Check không phản hồi |
| **Module 5** — Hệ Thống | JWT, phân quyền, audit log | 🌟 Chạy hoàn toàn trên LAN, không Internet |
