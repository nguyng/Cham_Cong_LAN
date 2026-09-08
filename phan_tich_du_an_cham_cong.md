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

## 4. 📊 Ma Trận So Sánh & Đánh Giá Tính Mới

> **Mục tiêu**: Đánh giá sự khác biệt của "Hệ Thống Chấm Công LAN" (dự án nhóm) so với các giải pháp hiện có trên thị trường.

| Tiêu chí / Chức năng | Máy Vân Tay Thủ Công | Cloud HRM (Misa, Base) | 🌟 LAN System (Dự án của nhóm) |
|----------------------|:--------------------:|:----------------------:|:------------------------------:|
| **Môi trường hoạt động** | Offline hoàn toàn | Bắt buộc có Internet | **Mạng nội bộ (LAN)** - Không cần Internet |
| **Yêu cầu phần cứng** | Máy quẹt vân tay / thẻ từ | Laptop / Smartphone | **Chỉ cần Laptop / PC có sẵn** |
| **Chi phí triển khai** | Cao (mua máy móc) | Trả phí hàng tháng | **0đ (Triển khai nội bộ)** |
| **Đồng bộ thời gian thực**| ❌ (Thường phải trút dữ liệu cuối tháng) | ✅ (Đồng bộ qua cloud) | ✅ **(Real-time qua WebSocket)** |
| **Chống gian lận: IP** | ➖ (Cố định tại máy) | ❌ (Có thể fake GPS/IP) | ✅ **(Chỉ nhận IP nội bộ công ty)** |
| **Chống gian lận: Random Check**| ❌ | ❌ (Rất hiếm phần mềm có) | ✅ **(Kích hoạt ngẫu nhiên bằng Python AI)** |
| **Gắn cờ bất thường tự động**| ❌ | ⚠️ (Chỉ ở bản cao cấp) | ✅ **(Thuật toán Data Analysis Python)** |
| **Kiến trúc hệ thống** | Standalone | Monolithic / Microservices trên Cloud | **Hybrid Microservices trong mạng LAN (Spring Boot + Python)** |
| **Bảo mật dữ liệu** | An toàn (lưu trên máy) | Rủi ro rò rỉ (lưu máy chủ bên thứ 3) | **Cực kỳ an toàn (Dữ liệu không bao giờ ra khỏi công ty)** |

### 🎯 Đánh Giá Tính Mới (Điểm Khác Biệt Của Dự Án):

1. **Kiến trúc Microservices trên LAN**: Việc triển khai Microservices (Java + Python) thường thấy trên Cloud, nhưng dự án áp dụng ngay trong môi trường mạng LAN nội bộ, giúp tận dụng tối đa thế mạnh của từng ngôn ngữ (Java xử lý lõi, Python phân tích dữ liệu).
2. **Cơ chế chống gian lận chủ động (Random Check)**: Khắc phục nhược điểm của máy vân tay (chấm hộ) và Cloud HRM (fake vị trí) bằng cách yêu cầu xác nhận ngẫu nhiên ngay tại màn hình làm việc trong giờ hành chính.
3. **Bảo mật dữ liệu tuyệt đối**: Các doanh nghiệp vừa và nhỏ thường e ngại đưa dữ liệu nhân sự lên Cloud. Hệ thống của nhóm giải quyết bài toán này bằng cách chạy hoàn toàn offline trên LAN mà vẫn giữ được tính năng hiện đại (Dashboard real-time).
4. **Không chi phí phần cứng**: Biến mọi máy tính trong mạng LAN thành "máy chấm công", giảm thiểu hoàn toàn chi phí mua sắm và bảo trì thiết bị đọc vân tay.

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
          ┌────────▼──────────────┬───────────────────┐
          │ ☕ Spring Boot :8080  │  🐍 Python  :8000 │
          │ - JWT / Phân quyền    │  - Chấm công vào/ra│
          │ - Quản lý nhân sự     │  - WebSocket RT    │
          │ - Ca làm / Nghỉ phép  │  - Random Check    │
          └────────┬──────────────┴─────────┬──────────┘
                   └────────────┬────────────┘
                                │ JPA / SQLAlchemy
                       ┌────────▼──────────┐
                       │   🗄️ MySQL DB     │
                       └───────────────────┘

  ❌ Không có kết nối ra ngoài Internet
```

---

## 6. 🛠️ Công Nghệ Triển Khai (Chính Thức)

| Tầng | Công nghệ | Mục đích |
|------|-----------|----------|
| **Frontend** | React + Axios + SockJS | Giao diện người dùng, gọi API, nhận WebSocket |
| **Core Backend (Java)** | Spring Boot 3.x + Spring Security + JWT | Bảo mật, nhân sự, ca làm, nghỉ phép |
| **Data/RT Backend (Python)** | FastAPI + APScheduler + openpyxl | Chấm công, Real-time WebSocket, Random Check, xuất báo cáo |
| **Database** | MySQL 8 + JPA (Java) / SQLAlchemy (Python) | Lưu trữ toàn bộ dữ liệu (dùng chung 1 DB) |
| **Build tool** | Maven (Java) + Vite (React) + pip (Python) | Quản lý dependencies |
| **API Style** | RESTful API + WebSocket | Giao tiếp Frontend ↔ 2 Backend |

### Lý do chọn kiến trúc Microservices (Spring Boot + Python):
- ✅ **Java (Spring Boot)**: Mạnh về bảo mật, transaction, quản lý cấu trúc tổ chức phức tạp
- ✅ **Python (FastAPI)**: Mạnh về xử lý real-time, thuật toán, xuất báo cáo
- ✅ **React**: Giao diện mượt, kết nối được cả 2 backend
- ✅ **Deploy LAN**: Chạy 2 server trên 1 máy, không cần Internet

---



> Mỗi thành viên đảm nhận đúng **5–6 nhiệm vụ** — không ai ít hơn hay nhiều hơn.

### Tổng quan phân công:

| Thành viên | Ngôn ngữ | Mảng phụ trách | Số nhiệm vụ |
|---|---|---|:---:|
| **Member 1** | Spring Boot | Bảo mật + Nhân viên + Phòng ban + Ca làm việc | 5 |
| **Member 2** | Python FastAPI | Chấm công + IP filter + WebSocket + Random Check + Gắn cờ | 5 |
| **Member 3** | Spring Boot + DevOps | Nghỉ phép + Báo cáo + ERD + Deploy LAN | 6 |
| **Member 4** | React | Trang nhân viên: Login, chấm công, popup, lịch sử, xin nghỉ | 6 |
| **Member 5** | React | Trang quản lý: Dashboard, Admin, duyệt nghỉ, báo cáo, biểu đồ | 5 |

---

### Chi tiết nhiệm vụ từng người:

#### 👤 Member 1 — Backend Java (Spring Boot) — Bảo Mật & Nhân Sự
1. API **Đăng nhập** / JWT / Spring Security
2. **Phân quyền** 3 cấp: Employee → Manager → Admin
3. API **Quản lý nhân viên** (Thêm / Sửa / Xóa / Tìm kiếm)
4. API **Quản lý phòng ban** (CRUD + gán Manager phụ trách)
5. API **Quản lý ca làm việc** (CRUD) + Phân ca cho nhân viên theo tuần/tháng

#### 👤 Member 2 — Backend Python (FastAPI) — Chấm Công & Real-time
1. API **Chấm công vào/ra** + Tự động nhận trạng thái Đúng giờ / Đi muộn / Về sớm
2. **Kiểm tra IP**: chỉ chấp nhận chấm công từ IP nội bộ công ty
3. **WebSocket**: broadcast real-time ai đang có mặt lên Dashboard Manager
4. Engine **Random Check**: dùng APScheduler gửi thông báo ngẫu nhiên + xử lý phản hồi
5. Thuật toán **gắn cờ ⚠️ bất thường** (vào/ra cách nhau dưới 10 phút, ngoài giờ)

#### 👤 Member 3 — Spring Boot + DevOps — Nghỉ Phép & Báo Cáo & Deploy
1. API **Xin nghỉ phép** (tạo đơn, theo dõi trạng thái) + **Duyệt nghỉ phép** (Manager)
2. API **Báo cáo** ngày công theo ngày / tháng + Xuất **Excel** (Apache POI)
3. Thiết kế **ERD** + Viết script **SQL** tạo bảng + dữ liệu mẫu
4. Cấu hình **CORS** để React gọi được cả Spring Boot (8080) và Python (8000)
5. Viết **`start_server.bat`**: tự động bật MySQL + Java + Python 1 cú click
6. **Hướng dẫn deploy LAN**: cài đặt + cho các máy khác truy cập qua IP

#### 👤 Member 4 — Frontend Lead (React) — Giao Diện Nhân Viên
1. Setup project **React + Vite**, cấu hình **Axios** gọi được cả 2 backend
2. Trang **Đăng nhập** (gọi Spring Boot, lưu JWT vào localStorage)
3. Trang **Chấm Công**: nút Vào/Ra + Đồng hồ giờ thực (gọi FastAPI)
4. Kết nối **WebSocket** + Popup **Random Check** (đếm ngược X phút, nút xác nhận)
5. Trang **Lịch sử chấm công** cá nhân (xem theo ngày/tháng)
6. Trang **Xin nghỉ phép** (tạo đơn, xem trạng thái)

#### 👤 Member 5 — Frontend Dev (React) — Dashboard & Quản Lý
1. **Layout** tổng thể: Sidebar, Navbar, Route bảo vệ theo vai trò
2. **Dashboard Manager**: ai đang có mặt (nhận real-time từ WebSocket Python)
3. Dashboard **cảnh báo**: nhân viên không phản hồi Random Check
4. Trang **Admin**: quản lý nhân viên, phòng ban, ca làm (gọi Spring Boot)
5. Trang **Duyệt nghỉ phép** (Manager) + Trang **Báo cáo** + Nút xuất Excel/PDF + **Biểu đồ** ngày côngật
- [ ] Cài đặt project Spring Boot, cấu hình Maven, kết nối MySQL
- [ ] API **Đăng nhập / JWT / Spring Security** / Phân quyền 3 cấp (Employee, Manager, Admin)
- [ ] API **Quản lý nhân viên** (CRUD) + Quản lý phòng ban
- [ ] API **Quản lý ca làm việc** (CRUD) + phân ca theo tuần/tháng
- [ ] API **Xin nghỉ phép** (tạo đơn) + **Duyệt nghỉ phép** (Manager chấp thuận/từ chối)
- [ ] Logic theo dõi số ngày phép còn lại của từng nhân viên

#### 👤 Member 2 — Backend Python (FastAPI) — Phụ trách Chấm Công & Real-time
- [ ] Cài đặt project FastAPI, cấu hình SQLAlchemy kết nối MySQL
- [ ] API **Chấm công vào/ra**: ghi nhận giờ, kiểm tra IP nội bộ
- [ ] **WebSocket**: broadcast real-time trạng thái ai đang có mặt lên Dashboard
- [ ] Engine **Random Check**: dùng APScheduler gửi thông báo ngẫu nhiên + xử lý phản hồi
- [ ] Thuật toán **gắn cờ bất thường** (vào/ra quá nhanh, ngoài giờ)
- [ ] Xuất báo cáo **Excel** (openpyxl) và **PDF** (reportlab) ngày công theo tháng

#### 👤 Member 3 — Database + DevOps + Tích hợp
- [ ] Thiết kế sơ đồ **ERD** đầy đủ (dùng chung 1 MySQL cho cả Java và Python)
- [ ] Viết script **SQL** tạo bảng + dữ liệu mẫu
- [ ] Cấu hình **CORS** để React gọi được cả 2 backend (Java port 8080, Python port 8000)
- [ ] Viết **REST call** từ Spring Boot → FastAPI khi cần lấy dữ liệu chấm công
- [ ] Viết file **`start_server.bat`**: tự động bật MySQL + Java Server + Python Server cùng lúc
- [ ] **Hướng dẫn deploy LAN**: các máy khác truy cập qua IP

#### 👤 Member 4 — Frontend Lead (React) — Giao Diện Nhân Viên
- [ ] Cài đặt project React + Vite, cấu hình **Axios** gọi được cả 2 API (port 8080 và 8000)
- [ ] Trang **Đăng nhập** (JWT lưu localStorage, gọi Spring Boot)
- [ ] Trang **Chấm Công**: nút Vào/Ra, hiển thị giờ thực (gọi FastAPI)
- [ ] Kết nối **WebSocket** nhận thông báo từ Python real-time
- [ ] Popup **Random Check**: đếm ngược X phút, nút xác nhận hiện diện
- [ ] Trang **Lịch sử chấm công** cá nhân + Trang **Xin nghỉ phép**

#### 👤 Member 5 — Frontend Dev (React) — Dashboard & Admin
- [ ] Layout tổng thể: **Sidebar, Navbar, Route bảo vệ** theo vai trò
- [ ] **Dashboard Manager**: danh sách ai đang có mặt (real-time từ WebSocket Python)
- [ ] Dashboard **cảnh báo**: nhân viên không phản hồi Random Check
- [ ] Trang **Admin**: quản lý nhân viên, phòng ban, ca làm (gọi Spring Boot)
- [ ] Trang **Duyệt nghỉ phép** (Manager) + Trang **Báo cáo**
- [ ] Nút **Xuất Excel/PDF** (gọi FastAPI Python) + Hiển thị **biểu đồ** ngày công

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
- [ ] Trình bày ma trận so sánh (Máy vân tay / Cloud HRM / LAN System)
- [ ] Giải thích kiến trúc Microservices LAN: Spring Boot + Python + React
- [ ] Trình bày phân công 5 thành viên (cân bằng Java ↔ Python)
- [ ] Trình bày lịch tiến độ 6 tuần
