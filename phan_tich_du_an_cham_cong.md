# 📋 Phân Tích Dự Án: Phần Mềm Chấm Công Trên Mạng LAN

> **Môn học**: Lập Trình Mạng  
> **Dự án**: Xây dựng phần mềm chấm công trên mạng LAN  
> **Phạm vi**: Doanh nghiệp / Công ty  

---

## 1. 🎯 Mô Tả Tổng Quan Dự Án

Phần mềm chấm công LAN là hệ thống **Client-Server** chạy trong mạng nội bộ (LAN), cho phép:
- Nhân viên điểm danh vào/ra từ máy tính của mình
- Quản lý theo dõi chuyên cần theo thời gian thực
- Quản trị viên cấu hình hệ thống, tài khoản, ca làm việc
- Xuất báo cáo lương, ngày công cuối tháng

---

## 2. 👥 Đối Tượng Tham Gia Vào Chương Trình

| STT | Đối tượng | Mô tả | Quyền hạn |
|-----|-----------|-------|-----------|
| 1 | **Nhân viên (Employee)** | Người sử dụng hệ thống hàng ngày | Chấm công vào/ra, xem lịch sử cá nhân, xin nghỉ phép |
| 2 | **Quản lý (Manager)** | Trưởng phòng/bộ phận | Xem chuyên cần nhóm, duyệt đơn nghỉ phép, xem báo cáo phòng |
| 3 | **Quản trị viên (Admin)** | IT / HR quản trị hệ thống | Quản lý tài khoản, ca làm, thiết lập hệ thống, xuất báo cáo toàn công ty |
| 4 | **Server (Máy chủ)** | Không phải người dùng, nhưng là thành phần hệ thống | Lưu trữ dữ liệu, xử lý yêu cầu, phát broadcast trạng thái |

### Sơ đồ phân cấp đối tượng:
```
                    ┌─────────────┐
                    │   Admin     │  ← Toàn quyền hệ thống
                    └──────┬──────┘
                           │ quản lý
                    ┌──────▼──────┐
                    │   Manager   │  ← Quản lý theo phòng ban
                    └──────┬──────┘
                           │ giám sát
                    ┌──────▼──────┐
                    │  Employee   │  ← Người dùng cuối
                    └─────────────┘
```

---

## 3. ⚙️ Các Chức Năng Dự Kiến

### 3.1 Nhóm chức năng Chấm Công
| # | Chức năng | Mô tả |
|---|-----------|-------|
| CC01 | Chấm công vào | Nhân viên đăng nhập ghi nhận giờ vào |
| CC02 | Chấm công ra | Nhân viên ghi nhận giờ ra |
| CC03 | Xem lịch sử chấm công | Tra cứu lịch sử cá nhân theo ngày/tháng |
| CC04 | Chấm công muộn/sớm | Tự động ghi nhận đi muộn, về sớm |

### 3.2 Nhóm chức năng Chống Gian Lận Chấm Công ⭐ (Độc đáo)
| # | Chức năng | Mô tả |
|---|-----------|-------|
| CGL01 | **Giới hạn IP chấm công** | Chỉ cho phép chấm công từ địa chỉ IP nội bộ công ty, không thể chấm từ bên ngoài |
| CGL02 | **Random Check (Xác nhận ngẫu nhiên)** | Hệ thống gửi thông báo bất ngờ trong giờ làm, nhân viên phải xác nhận trong vòng X phút, không xác nhận = ghi nhận vắng mặt |
| CGL03 | **Lịch sử chấm công bất thường** | Tự động gắn cờ ⚠️ các ca chấm công đáng ngờ (vào/ra cách nhau quá nhanh, chấm công ngoài giờ...) |
| CGL04 | **Cảnh báo Manager real-time** | Khi nhân viên không phản hồi Random Check → gửi thông báo ngay cho Manager |

### 3.3 Nhóm chức năng Quản Lý Nhân Sự
| # | Chức năng | Mô tả |
|---|-----------|-------|
| NS01 | Quản lý nhân viên | Thêm/sửa/xóa thông tin nhân viên |
| NS02 | Quản lý phòng ban | Tổ chức cơ cấu phòng ban |
| NS03 | Quản lý ca làm việc | Định nghĩa ca sáng, chiều, tối... |
| NS04 | Phân ca cho nhân viên | Gán ca làm việc theo tuần/tháng |

### 3.4 Nhóm chức năng Nghỉ Phép
| # | Chức năng | Mô tả |
|---|-----------|-------|
| NP01 | Gửi đơn xin nghỉ phép | Nhân viên tạo đơn nghỉ |
| NP02 | Duyệt đơn nghỉ phép | Manager chấp thuận/từ chối |
| NP03 | Theo dõi số ngày phép còn lại | Hiển thị số ngày phép tồn |

### 3.5 Nhóm chức năng Báo Cáo & Thống Kê
| # | Chức năng | Mô tả |
|---|-----------|-------|
| BC01 | Báo cáo chuyên cần theo ngày | Danh sách vào/ra trong ngày |
| BC02 | Báo cáo tháng | Tổng hợp ngày công mỗi nhân viên |
| BC03 | Xuất Excel/PDF | Xuất file để tính lương |
| BC04 | Dashboard real-time | Hiển thị ai đang có mặt hiện tại |

### 3.6 Nhóm chức năng Mạng LAN (Đặc thù dự án)
| # | Chức năng | Mô tả |
|---|-----------|-------|
| LAN01 | Kiến trúc Client-Server | Server trung tâm, nhiều Client kết nối |
| LAN02 | Truyền thông TCP/UDP | Gửi dữ liệu chấm công qua socket |
| LAN03 | Broadcast trạng thái | Server phát thông báo cho tất cả Client |
| LAN04 | Phát hiện Server tự động | Client tự tìm Server trong LAN |
| LAN05 | Xử lý đồng thời (Multithread) | Server xử lý nhiều Client cùng lúc |

### 3.7 Nhóm chức năng Hệ Thống
| # | Chức năng | Mô tả |
|---|-----------|-------|
| HT01 | Đăng nhập / Đăng xuất | Xác thực người dùng |
| HT02 | Phân quyền | Giới hạn chức năng theo vai trò |
| HT03 | Nhật ký hệ thống (Log) | Ghi lại các hoạt động quan trọng |
| HT04 | Sao lưu dữ liệu | Backup database định kỳ |

---

## 4. 📊 Ma Trận So Sánh Chức Năng

> **Giải thích**: So sánh với các phần mềm chấm công phổ biến: **HanetAI**, **TimekeepingPro**, **Misa HRM**, **Google Sheets thủ công**

| Chức năng | Phần mềm thương mại có | Phần mềm của mình có | Tính mới / Độc đáo |
|-----------|:---------------------:|:-------------------:|:-------------------:|
| **Chấm công vào/ra** | ✅ | ✅ | ➖ Học từ các phần mềm khác |
| **Quản lý nhân viên** | ✅ | ✅ | ➖ Học từ các phần mềm khác |
| **Quản lý ca làm việc** | ✅ | ✅ | ➖ Học từ các phần mềm khác |
| **Xin/Duyệt nghỉ phép** | ✅ | ✅ | ➖ Học từ các phần mềm khác |
| **Báo cáo tháng / xuất Excel** | ✅ | ✅ | ➖ Học từ các phần mềm khác |
| **Dashboard real-time** | ✅ (một số) | ✅ | ➖ Học từ một số phần mềm |
| **Chạy hoàn toàn trên LAN nội bộ (không cần Internet)** | ❌ (hầu hết cần cloud) | ✅ | 🌟 **ĐỘC ĐÁO** |
| **Tự động phát hiện Server trong LAN (Auto-discovery)** | ❌ | ✅ | 🌟 **ĐỘC ĐÁO** |
| **Broadcast thông báo real-time qua WebSocket** | ❌ | ✅ | 🌟 **ĐỘC ĐÁO** |
| **Xử lý đa luồng (Multithread Server)** | ❌ (ẩn bên trong) | ✅ (tường minh) | 🌟 **HỌC TẬP & TRÌNH BÀY** |
| **Không phụ thuộc thiết bị phần cứng (vân tay, thẻ từ)** | ❌ (thường cần HW) | ✅ | 🌟 **ĐỘC ĐÁO** |
| **Chi phí bằng 0 (open source / tự phát triển)** | ❌ (trả phí) | ✅ | 🌟 **ĐỘC ĐÁO** |
| **Giới hạn IP chấm công (chỉ trong LAN)** | ❌ | ✅ | 🌟 **ĐỘC ĐÁO** |
| **Random Check — xác nhận hiện diện ngẫu nhiên** | ❌ (rất hiếm) | ✅ | 🌟 **ĐỘC ĐÁO** |
| **Cảnh báo Manager khi nhân viên không phản hồi** | ❌ | ✅ | 🌟 **ĐỘC ĐÁO** |
| **Tự động gắn cờ chấm công bất thường** | ⚠️ (một số HRM đắt tiền) | ✅ | 🌟 **ĐỘC ĐÁO** |

### Tóm tắt ma trận:
- **Chức năng học từ phần mềm khác**: Chấm công, quản lý nhân sự, ca làm, nghỉ phép, báo cáo
- **Chức năng mới / độc đáo**: Hoàn toàn LAN, auto-discovery server, broadcast WebSocket real-time, không cần phần cứng, miễn phí, **giới hạn IP**, **Random Check chống gian lận**, **cảnh báo Manager**, **gắn cờ bất thường**

---

## 5. 🏗️ Kiến Trúc Hệ Thống

```
         🏢 MẠNG NỘI BỘ CÔNG TY (LAN)
  ─────────────────────────────────────────────────────

  💻 Máy NV 1          💻 Máy NV 2          💻 Máy Manager
  Chrome Browser        Chrome Browser        Chrome Browser
  React App            React App             React App
       │                    │                     │
       └───────────┬─────────┘                    │
                   │          ┌───────────────────┘
                   │   HTTP REST API / WebSocket
                   │
          ┌────────▼──────────────────┐
          │   💻 MÁY CHỦ NỘI BỘ      │
          │   Spring Boot (port 8080) │
          │   IP: 192.168.1.100       │
          │   - REST API Controller   │
          │   - WebSocket Handler     │
          │   - JWT Auth              │
          │   - Random Check Engine   │
          └────────┬──────────────────┘
                   │  JPA / Hibernate
          ┌────────▼──────────────────┐
          │   🗄️ MySQL Database       │
          │   - employees             │
          │   - attendance_logs       │
          │   - departments           │
          │   - shifts                │
          │   - leave_requests        │
          └───────────────────────────┘

  ❌ Không có kết nối ra ngoài Internet
```

---

## 6. 🛠️ Công Nghệ Triển Khai (Chính Thức)

| Tầng | Công nghệ | Mục đích |
|------|-----------|----------|
| **Frontend** | React + Axios + SockJS | Giao diện người dùng, gọi API, nhận WebSocket |
| **Backend** | Spring Boot 3.x (Java) | REST API, xử lý logic nghiệp vụ |
| **Real-time** | Spring WebSocket + STOMP | Broadcast chấm công, Random Check, cảnh báo |
| **Bảo mật** | Spring Security + JWT | Đăng nhập, phân quyền theo vai trò |
| **Database** | MySQL 8 + JPA/Hibernate | Lưu trữ toàn bộ dữ liệu |
| **Build tool** | Maven (Backend) + Vite (Frontend) | Quản lý dependencies |
| **API Style** | RESTful API | Giao tiếp Frontend ↔ Backend |

### Lý do chọn Stack này:
- ✅ Cả nhóm đều có kinh nghiệm Spring Boot + React
- ✅ Spring Boot tích hợp WebSocket rất dễ (real-time)
- ✅ Deploy LAN đơn giản: chạy `.jar` trên 1 máy là xong
- ✅ React chạy trên browser, nhân viên không cần cài gì

---

## 7. 👨‍💻 Phân Công 5 Thành Viên

### Tổng quan phân công:

| Thành viên | Vai trò | Mảng chính |
|---|---|---|
| **Member 1** | Backend Lead | API chấm công + chống gian lận + WebSocket |
| **Member 2** | Backend Dev | API nhân sự + ca làm + nghỉ phép |
| **Member 3** | Frontend Lead | Giao diện nhân viên + trang chấm công |
| **Member 4** | Frontend Dev | Giao diện Admin + Manager + Dashboard |
| **Member 5** | Database + Tích hợp | Thiết kế DB + Deploy LAN + kết nối FE-BE |

---

### Chi tiết nhiệm vụ từng người:

#### 👤 Member 1 — Backend Lead (Spring Boot)
- [ ] Cài đặt project Spring Boot, cấu hình Maven, kết nối MySQL
- [ ] API Đăng nhập / JWT / Spring Security / Phân quyền
- [ ] API Chấm công vào/ra, lịch sử chấm công
- [ ] Logic giới hạn IP chấm công (filter theo IP nội bộ)
- [ ] Tích hợp WebSocket: broadcast trạng thái real-time
- [ ] Engine **Random Check**: lập lịch gửi thông báo ngẫu nhiên + xử lý phản hồi
- [ ] Logic gắn cờ ⚠️ chấm công bất thường

#### 👤 Member 2 — Backend Dev (Spring Boot)
- [ ] API Quản lý nhân viên (CRUD)
- [ ] API Quản lý phòng ban (CRUD)
- [ ] API Quản lý ca làm việc (CRUD) + phân ca
- [ ] API Xin nghỉ phép + duyệt nghỉ phép
- [ ] API Báo cáo: theo ngày, theo tháng
- [ ] Xuất file Excel (dùng Apache POI)

#### 👤 Member 3 — Frontend Lead (React)
- [ ] Cài đặt project React + Vite, cấu hình Axios
- [ ] Trang Đăng nhập (JWT lưu localStorage)
- [ ] Trang Chấm Công: nút Vào/Ra, hiển thị giờ thực
- [ ] Kết nối WebSocket nhận thông báo Real-time
- [ ] Popup **Random Check**: đếm ngược X phút, nút xác nhận
- [ ] Trang Lịch sử chấm công cá nhân
- [ ] Trang Xin nghỉ phép

#### 👤 Member 4 — Frontend Dev (React)
- [ ] Layout tổng thể: Sidebar, Navbar, Route bảo vệ
- [ ] **Dashboard Manager**: danh sách ai đang có mặt (real-time)
- [ ] Dashboard cảnh báo: nhân viên không phản hồi Random Check
- [ ] Trang Admin: quản lý nhân viên, phòng ban, ca làm
- [ ] Trang Duyệt nghỉ phép (Manager)
- [ ] Trang Báo cáo + nút xuất Excel

#### 👤 Member 5 — Database + DevOps + Tích hợp
- [ ] Thiết kế sơ đồ ERD đầy đủ
- [ ] Viết script SQL tạo bảng + dữ liệu mẫu
- [ ] Cấu hình `application.properties` (Spring Boot ↔ MySQL)
- [ ] Hỗ trợ kết nối Frontend ↔ Backend (CORS, API URL)
- [ ] **Deploy trên LAN**: cài MySQL + chạy `.jar` trên máy chủ
- [ ] Hướng dẫn các máy khác truy cập qua IP
- [ ] Viết tài liệu hướng dẫn sử dụng

---

### 📅 Lịch Tiến Độ Dự Kiến:

| Tuần | Công việc |
|------|----------|
| **Tuần 1** | Trình bày phân tích, thiết kế DB, dựng project skeleton |
| **Tuần 2** | Backend: API chấm công, đăng nhập, nhân sự |
| **Tuần 3** | Frontend: giao diện chính, kết nối API |
| **Tuần 4** | WebSocket real-time, Random Check, Dashboard |
| **Tuần 5** | Tích hợp hoàn chỉnh, deploy LAN, test thực tế |
| **Tuần 6** | Sửa lỗi, hoàn thiện báo cáo, demo |

---

## 8. 📅 Checklist Trình Bày Tuần Sau

- [ ] Slide giới thiệu tổng quan dự án
- [ ] Trình bày danh sách đối tượng + sơ đồ phân cấp
- [ ] Trình bày bảng chức năng dự kiến (7 nhóm)
- [ ] Trình bày ma trận so sánh (highlight 10 điểm độc đáo)
- [ ] Giải thích kiến trúc LAN: Spring Boot + React + MySQL
- [ ] Trình bày phân công 5 thành viên
- [ ] Trình bày lịch tiến độ 6 tuần
