# Kết quả kiểm thử

Ngày chạy: 30/10/2026 (Asia/Saigon).

## Đã xác nhận

- Python 3.12.10, môi trường `.venv` riêng.
- Alembic migration chạy thành công đến revision `20261104_0003`; schema gồm 22 bảng nghiệp vụ cùng index phục vụ truy vấn và dọn dữ liệu định kỳ.
- `pytest`: **54 passed**.
- `ruff`: **All checks passed** đối với mã mới.
- PyInstaller tạo đủ:
  - `AttendanceServer.exe` — 13,404,100 bytes.
  - `AttendanceClient.exe` — 3,792,974 bytes.
  - `AttendanceAdmin.exe` — 3,792,986 bytes.

Phạm vi test tự động gồm xác thực đúng/sai, khóa sau đăng nhập sai, logout/thu hồi phiên, đổi mật khẩu, RBAC, bảo vệ Admin đang đăng nhập, thu hồi phiên khi đổi vai trò, giới hạn dữ liệu Manager theo phòng ban, Manager phê duyệt/thu hồi thiết bị trong đúng phòng ban, quyền xóa chỉ dành cho Admin, lưu trữ danh mục, xóa và đăng ký lại thiết bị, nhiều tài khoản dùng chung một máy, bắt buộc fingerprint khi chấm công, migration ràng buộc thiết bị cũ, kiểm tra thứ tự giờ điều chỉnh, check-in/check-out, idempotency, chống chấm công trùng, ca qua đêm, thiếu phân ca, yêu cầu, duyệt và hủy đơn nghỉ phép, kiểm tra loại nghỉ/quỹ phép, Random Check, WebSocket broadcast, phân trang, dọn dữ liệu hết hạn, đánh dấu thông báo, báo cáo API, Excel, PDF, 20 request health đồng thời, liệt kê/backup/restore SQLite, kiểm tra PRAGMA SQLite (foreign key, WAL, busy timeout), từ chối URL MySQL, dữ liệu Client đang kết nối, dashboard quản trị, bộ nạp dữ liệu chạy lặp không nhân đôi và smoke test tạo đủ màn hình/widget PySide6.

- Bản portable đã được chạy trực tiếp từ `.exe` trên máy build:
  - Server tự migration database lên revision `20261104_0003`, trả `/api/v1/health` với HTTP 200, đăng nhập đúng ba vai trò và trả metadata phân trang cho danh sách nghiệp vụ/backup.
  - Lệnh `AttendanceServer.exe bootstrap-admin` tạo đúng tài khoản vai trò ADMIN; mật khẩu lưu bằng Argon2 hash, không lưu plaintext.
  - Client và Admin vượt qua splash, mở màn hình đăng nhập và duy trì tiến trình trong Qt offscreen; PySide6 và Qt Charts có trong gói.
  - Luồng WebSocket được hủy an toàn khi đăng xuất; kiểm thử với Server thật xác nhận `QThread` đã dừng và tiến trình không còn bị Qt cưỡng bức kết thúc.
  - Tài khoản Manager trong AttendanceClient chỉ nhận dữ liệu cá nhân qua `mine=true`; cùng tài khoản trong AttendanceAdmin vẫn có đúng phạm vi quản lý phòng ban.
  - Server portable hiển thị console có tiêu đề riêng, log khởi động và hướng dẫn `Ctrl+C`; kiểm thử dừng từ console đã tắt Uvicorn đúng trình tự.

## Chưa được phép tuyên bố đã xác nhận

- Kiểm thử tải dài hạn SQLite với số lượng Client và dữ liệu sản xuất thực tế.
- Kiểm thử cảnh báo lỗi Client cho validation, timeout, cấu hình sai và phản hồi Server không hợp lệ.
- Kiểm thử Manager xóa thiết bị cũ đúng phạm vi và lưu trữ thiết bị đã có lịch sử chấm công.
- HTTPS với CA nội bộ và Windows Firewall trên mạng doanh nghiệp thật.
- Hai hoặc nhiều máy Windows vật lý trong cùng LAN.
- Trải nghiệm UI thủ công ở nhiều độ phân giải.
- Chạy tệp one-file `.exe` trên máy đích. Máy xây dựng hiện tại chặn bootloader one-file tạo cấu trúc thư mục tự giải nén, nhưng bản portable không cần tự giải nén đã vượt qua runtime smoke đầy đủ.

Các mục trên tiếp tục để **Pending** trong checklist cho đến khi có đúng hạ tầng nghiệm thu.
