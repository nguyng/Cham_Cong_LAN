# Bảng đối chiếu triển khai

Nguồn: `README.md`, `phan_tich_du_an_cham_cong.md`, `Module_ChamCong_LAN.md`, `Module_ChamCong_LAN_content.txt` và yêu cầu Codex đính kèm. Trạng thái chỉ chuyển sang **Done** sau khi có mã thực thi và kiểm thử phù hợp.

| ID | Chức năng | Nguồn yêu cầu | Module | Trạng thái | Kiểm thử |
|---|---|---|---|---|---|
| F001 | Đăng nhập JWT, giới hạn đăng nhập sai | Yêu cầu §5A, HT01 | Authentication | Implemented | Automated |
| F002 | Đăng xuất, thu hồi phiên | Yêu cầu §5A | Authentication | Implemented | Automated |
| F003 | Đổi mật khẩu | Yêu cầu §5A | Authentication | Implemented | Automated |
| F004 | Phân quyền Employee/Manager/Admin | Tài liệu §2, yêu cầu §5A | Authorization | Implemented | Automated |
| F005 | Quản lý nhân viên, hồ sơ, tìm kiếm/lọc | NS01, yêu cầu §5B | HR | Implemented | Automated |
| F006 | Quản lý phòng ban và Manager | NS02, Module 2.3 | HR | Implemented | Automated |
| F007 | Quản lý chức vụ | Yêu cầu §5B | HR | Implemented | Automated |
| F008 | Quản lý ca làm, kể cả ca qua đêm | NS03, yêu cầu §5C | Shift | Implemented | Automated |
| F009 | Phân ca tuần/tháng | NS04, Module 2.4 | Shift | Implemented | Automated |
| F010 | Check-in dùng giờ Server | CC01, yêu cầu §5C | Attendance | Implemented | Automated |
| F011 | Check-out, tổng giờ, giờ nghỉ | CC02, yêu cầu §5C | Attendance | Implemented | Automated |
| F012 | Đi muộn, về sớm | CC04, Module 1.1 | Attendance | Implemented | Automated |
| F013 | Chống bản ghi chấm công trùng/idempotency | Yêu cầu §5C, §5G | Attendance | Implemented | Automated |
| F014 | Lịch sử và tra cứu chấm công | CC03, yêu cầu §5C | Attendance | Implemented | Automated |
| F015 | Yêu cầu/duyệt điều chỉnh công, lịch sử sửa | Yêu cầu §5C | Attendance | Implemented | Automated |
| F016 | Kiểm tra IP theo mạng cấu hình | CGL01, Module 1.2 | Security | Implemented | Automated |
| F017 | Đăng ký và kiểm tra thiết bị | Yêu cầu §5D | Security | Implemented | Automated |
| F018 | Phát hiện phiên trùng/đăng nhập bất thường | Yêu cầu §5D | Security | Implemented | Automated |
| F019 | Random Check WebSocket, phản hồi, hết hạn | CGL02, Module 1.3 | Security | Implemented | Automated |
| F020 | Cảnh báo nghi vấn và xử lý thủ công | CGL03/CGL04, yêu cầu §5D | Security | Implemented | Automated |
| F021 | Loại nghỉ phép và quỹ phép | NP03, Module 3.3 | Leave | Implemented | Automated |
| F022 | Gửi/theo dõi đơn nghỉ phép | NP01, Module 3.1 | Leave | Implemented | Automated |
| F023 | Duyệt/từ chối có lý do và trừ quỹ phép | NP02, Module 3.2 | Leave | Implemented | Automated |
| F024 | Thông báo kết quả thời gian thực | Module 3, 5.3 | Notification | Implemented | Automated |
| F025 | Báo cáo ngày/tháng/phòng ban/nhân viên | BC01/BC02, yêu cầu §5F | Reporting | Implemented | Automated |
| F026 | Tổng giờ/ngày công/muộn/sớm/nghỉ phép | Yêu cầu §5F | Reporting | Implemented | Automated |
| F027 | Xuất Excel | BC03 | Reporting | Implemented | Automated |
| F028 | Xuất PDF | BC03 | Reporting | Implemented | Automated |
| F029 | Dashboard real-time và biểu đồ | BC04 | Dashboard | Implemented | API + UI construction automated; visual manual pending |
| F030 | REST API qua TCP/IP | LAN01/LAN02 | LAN | Implemented | Automated |
| F031 | WebSocket broadcast | LAN03 | LAN | Implemented | Automated |
| F032 | UDP discovery, không truyền dữ liệu nhạy cảm | LAN04, yêu cầu §5G | LAN | Implemented | Automated |
| F033 | Mất kết nối/tự kết nối lại/timeout | Yêu cầu §5G | Client network | Implemented | Automated |
| F034 | Nhiều Client đồng thời | LAN05 | LAN | Implemented | Automated |
| F035 | Cấu hình hệ thống | Yêu cầu §5H | System | Implemented | Automated |
| F036 | Nhật ký đăng nhập/hệ thống/thay đổi | HT03, Module 5.4 | Audit | Implemented | Automated |
| F037 | Danh sách Client đang kết nối | Yêu cầu §4.3, §5H | System | Implemented | Automated |
| F038 | Sao lưu SQLite nhất quán | HT04, yêu cầu §5H, thay đổi người dùng | Backup | Implemented | Automated |
| F039 | Kiểm tra toàn vẹn và khôi phục SQLite | Yêu cầu §5H, thay đổi người dùng | Backup | Implemented | Automated round-trip |
| F040 | Splash/Login/Employee Dashboard | Yêu cầu §6 | Client UI | Implemented | UI construction automated; visual manual pending |
| F041 | Chấm công/lịch sử/lịch làm/nghỉ phép | Yêu cầu §6 | Client UI | Implemented | API automated + UI construction automated |
| F042 | Thông báo/hồ sơ/đổi mật khẩu | Yêu cầu §6 | Client UI | Implemented | API automated + UI construction automated |
| F043 | Admin Dashboard riêng/nhân viên/phòng ban, tìm kiếm và empty-state | Yêu cầu §6 | Admin UI | Implemented | API automated + UI construction automated |
| F044 | Ca/phân ca chọn ngày/quản lý công/duyệt điều chỉnh và phép | Yêu cầu §6 | Admin UI | Implemented | API automated + UI construction automated |
| F045 | Cảnh báo/Random Check/Client chi tiết/báo cáo có bộ lọc/cấu hình | Yêu cầu §6 | Admin UI | Implemented | API automated + UI construction automated |
| F046 | Light/Dark, sidebar, card, toast, loading và giao diện Admin riêng | Yêu cầu §6 | UI Design | Implemented | UI construction automated + offscreen render inspected; visual manual pending |
| F047 | Alembic migration, PK/FK/index/unique | Yêu cầu §7 | Database | Implemented | Automated |
| F048 | HTTPS nội bộ và cấu hình Firewall | Yêu cầu §10 | Deployment | Implemented | TLS/Firewall tooling automated; trusted CA deployment pending |
| F049 | Script chạy/build 3 tệp exe | Yêu cầu §12 | Packaging | Done | Portable Server/Client/Admin runtime smoke; one-file build verified |
| F050 | Triển khai thực tế trên hai máy Windows | Yêu cầu §10 | Acceptance | Pending | Not tested |

## Quy tắc nghiệp vụ đã chốt từ tài liệu

- Thời gian chấm công luôn lấy từ Server theo múi giờ cấu hình; Client không gửi thời gian chính thức.
- Random Check thất bại chỉ tạo cảnh báo để Manager/Admin xem xét, không tự kết luận gian lận.
- Ca qua đêm thuộc ngày bắt đầu ca; check-out có thể ở ngày tiếp theo.
- Manager chỉ thao tác dữ liệu thuộc phòng ban mình quản lý; Admin có phạm vi toàn công ty.
- UDP chỉ trả về tên dịch vụ, IP, cổng HTTPS và phiên bản giao thức.
- Xóa nhân viên được thể hiện bằng ngừng hoạt động để giữ lịch sử và toàn vẹn báo cáo.
