# Kết quả kiểm thử

Ngày chạy: 29/10/2026 (Asia/Saigon).

## Đã xác nhận

- Python 3.12.10, môi trường `.venv` riêng.
- Alembic initial migration chạy thành công trên database kiểm thử; tạo 22 bảng nghiệp vụ (72 database objects gồm index/constraint).
- `pytest`: **27 passed**.
- `ruff`: **All checks passed** đối với mã mới.
- PyInstaller tạo đủ:
  - `AttendanceServer.exe` — 32,640,832 bytes.
  - `AttendanceClient.exe` — 53,567,673 bytes.
  - `AttendanceAdmin.exe` — 53,567,685 bytes.

Phạm vi test tự động gồm xác thực đúng/sai, khóa sau đăng nhập sai, logout/thu hồi phiên, đổi mật khẩu, RBAC, giới hạn dữ liệu Manager theo phòng ban, check-in/check-out, idempotency, chống chấm công trùng, ca qua đêm, thiếu phân ca, thiết bị chờ duyệt/phê duyệt, yêu cầu và duyệt điều chỉnh công, nghỉ phép và trừ quỹ, thống kê ngày nghỉ, Random Check, WebSocket broadcast, đánh dấu thông báo, báo cáo API, Excel, PDF, 20 request health đồng thời, liệt kê/backup/restore SQLite, kiểm tra PRAGMA SQLite (foreign key, WAL, busy timeout), từ chối URL MySQL, dữ liệu Client đang kết nối, dashboard quản trị và smoke test tạo đủ màn hình/widget PySide6 (gồm empty-state và chọn ngày phân ca).

- Bản portable đã được chạy trực tiếp từ `.exe` trên máy build:
  - Server tự migration database mới lên revision `20261029_0001`, tạo 23 bảng kể cả `alembic_version`, rồi trả `/api/v1/health` với HTTP 200.
  - Lệnh `AttendanceServer.exe bootstrap-admin` tạo đúng tài khoản vai trò ADMIN; mật khẩu lưu bằng Argon2 hash, không lưu plaintext.
  - Client và Admin vượt qua splash, mở màn hình đăng nhập và duy trì tiến trình trong Qt offscreen; PySide6 và Qt Charts có trong gói.

## Chưa được phép tuyên bố đã xác nhận

- Kiểm thử tải dài hạn SQLite với số lượng Client và dữ liệu sản xuất thực tế.
- HTTPS với CA nội bộ và Windows Firewall trên mạng doanh nghiệp thật.
- Hai hoặc nhiều máy Windows vật lý trong cùng LAN.
- Trải nghiệm UI thủ công ở nhiều độ phân giải.
- Chạy tệp one-file `.exe` trên máy đích. Máy xây dựng hiện tại chặn bootloader one-file tạo cấu trúc thư mục tự giải nén, nhưng bản portable không cần tự giải nén đã vượt qua runtime smoke đầy đủ.

Các mục trên tiếp tục để **Pending** trong checklist cho đến khi có đúng hạ tầng nghiệm thu.
