# 📋 Phần Mềm Chấm Công LAN

Dự án môn **Lập Trình Mạng** — Xây dựng phần mềm chấm công trên mạng LAN.

## 🛠️ Công nghệ (Kiến trúc Microservices)
- **Frontend (Giao diện)**: React + Vite + Axios
- **Core Backend (Java)**: Spring Boot 3.x + Spring Security (Xử lý nghiệp vụ chính, bảo mật, CRUD)
- **Data/AI Backend (Python)**: FastAPI + Pandas/OpenCV (Xử lý biểu đồ báo cáo, xuất Excel/PDF, AI phát hiện gian lận chấm công)
- **Database**: MySQL 8
- **Giao tiếp mạng**: REST API nội bộ LAN

## 👥 Phân Công Nhóm (5 Người) - Cân Bằng Khối Lượng
Để đảm bảo điểm số đồng đều, Backend được chia thành 2 service hoạt động độc lập (50/50 khối lượng):

1. **Member 1 — Backend (Spring Boot)**: Phụ trách toàn bộ **Nghiệp vụ Nhân sự (HR)**
   - API Quản lý nhân viên, phòng ban, ca làm việc.
   - API Đăng nhập, phân quyền, xin nghỉ phép & duyệt phép.
   - Xử lý các logic nghiệp vụ phức tạp về cơ cấu tổ chức (JPA/Hibernate).

2. **Member 2 — Backend (Python FastAPI)**: Phụ trách toàn bộ **Chấm công & Real-time**
   - API Chấm công vào/ra (chịu tải cao).
   - WebSocket: Bắn thông báo real-time khi có người chấm công (đẩy lên Dashboard).
   - Xử lý thuật toán chống gian lận (Random Check, check IP) & Xuất báo cáo (Excel/PDF).

3. **Member 3 — Database & DevOps (Java/Python)**
   - Thiết kế ERD, cấu hình MySQL.
   - Code cầu nối (Inter-service) để Spring Boot nói chuyện được với Python.
   - Setup môi trường LAN, viết script tự động chạy 2 server cùng lúc.

4. **Member 4 — Frontend Lead (React)**
   - Trang Chấm công cho Nhân viên, xử lý nhận thông báo Random Check (từ Python).
   - Trang Xin nghỉ phép (gọi API Spring Boot).
   - Ghép nối JWT Token cho cả 2 backend.

5. **Member 5 — Frontend Dev (React)**
   - Trang Dashboard cho Manager (Real-time update ai đang có mặt).
   - Màn hình Admin quản lý nhân sự, phòng ban, phân ca.
   - Vẽ biểu đồ báo cáo chuyên cần.

## 🚀 Hướng dẫn chạy

### Backend
```bash
cd backend
mvn spring-boot:run
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📁 Tài liệu
- [Phân tích dự án](./phan_tich_du_an_cham_cong.md)
