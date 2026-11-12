# Kết quả kiểm thử

Ngày chạy: 12/11/2026 (Asia/Saigon).

## Đã xác nhận

- Python 3.12.10, môi trường `.venv` riêng.
- Alembic migration chạy thành công đến revision `20261113_0006`; schema gồm 22 bảng nghiệp vụ, hồ sơ lương/OT nhân viên, tọa độ GPS, khoảng cách geofence lúc vào/ra và index phục vụ truy vấn/dọn dữ liệu định kỳ.
- `pytest`: **101 passed**.
- `ruff`: **All checks passed** đối với mã mới.
- GPS: kiểm thử cả hai nhánh tọa độ thật và dự phòng IP LAN, geofence, bán kính và giới hạn sai số.
- PDF: font TrueType được xác nhận có đủ glyph tiếng Việt (`Đặng Nguyễn Trường`).
- Nghỉ phép: Client có nút Hủy đơn; API kiểm tra trạng thái, phạm vi nhân viên và hoàn quỹ phép.
- Excel: xuất bảng Client/Admin và báo cáo Server thành workbook `.xlsx` có tiêu đề, màu header,
  bộ lọc, dòng xen kẽ, định dạng tiền/phần trăm, trạng thái tô màu và thiết lập in ngang.
- PyInstaller tạo đủ:
  - `AttendanceServer.exe` — 13,450,113 bytes.
  - `AttendanceClient.exe` — 4,892,231 bytes.
  - `AttendanceAdmin.exe` — 4,892,243 bytes.

Phạm vi test tự động gồm xác thực đúng/sai, khóa sau đăng nhập sai, logout/thu hồi phiên, đổi mật khẩu, RBAC, bảo vệ Admin đang đăng nhập, thu hồi phiên khi đổi vai trò, lưu `last_seen_at`, giới hạn dữ liệu Manager theo phòng ban, Manager phê duyệt/thu hồi/xóa thiết bị đúng phạm vi, chặn vô hiệu hóa nhân viên hoặc thiết bị khi còn ca mở, quyền xóa chỉ dành cho Admin, lưu trữ và lọc danh mục, nhiều tài khoản dùng chung một máy, fingerprint kết hợp MachineGuid/ổ đĩa/mã cài đặt và không phụ thuộc MAC, kiểm tra/lưu GPS và khoảng cách geofence, từ chối vị trí ngoài bán kính hoặc sai số quá lớn, migration ràng buộc thiết bị cũ, kiểm tra thứ tự giờ điều chỉnh, chống yêu cầu điều chỉnh trùng, check-in/check-out theo múi giờ Việt Nam, idempotency, chống chấm công trùng, ca qua đêm, thiếu phân ca, phát hiện/duyệt/từ chối và tính tiền OT, yêu cầu/duyệt/hủy đơn nghỉ phép, hoàn quỹ phép giao năm, tính lương theo công, từ chối kỳ lương tương lai, Random Check gắn ca và tạo cảnh báo khi quá hạn, WebSocket chỉ dùng Authorization header, từ chối token query và không broadcast IP/GPS, phân trang tự kẹp phạm vi, dọn dữ liệu hết hạn, đánh dấu thông báo, báo cáo API, chống công thức Excel/markup PDF, ghi file nguyên tử, 20 request health đồng thời, liệt kê/backup/restore SQLite, kiểm tra PRAGMA SQLite, từ chối URL MySQL, validation cấu hình, dữ liệu Client đang kết nối, dashboard quản trị, bảng sort vẫn chọn đúng bản ghi, GPS bất đồng bộ không dùng nested UI event loop, bộ nạp dữ liệu chạy lặp không nhân đôi và smoke test tạo đủ màn hình/widget PySide6.

- Bản portable đã được chạy trực tiếp từ `.exe` trên máy build:
  - `server.env` được tạo với cấu hình production và JWT secret ngẫu nhiên 64 ký tự; bản build từ chối khởi động nếu thiếu tệp cấu hình này thay vì dùng khóa mặc định.
  - Server tự migration database lên revision `20261113_0006`, trả `/api/v1/health` với HTTP 200; Admin đọc 5/5 và Manager đọc 2/2 bản ghi đúng phạm vi có tọa độ GPS; API bảng lương trả 5 nhân viên và tính OT đã duyệt.
  - Lệnh `AttendanceServer.exe bootstrap-admin` tạo đúng tài khoản vai trò ADMIN; mật khẩu lưu bằng Argon2 hash, không lưu plaintext.
  - Client và Admin vượt qua splash, mở màn hình đăng nhập và duy trì tiến trình trong Qt offscreen; PySide6, Qt Charts và Qt Positioning có trong gói. Kiểm thử UI ở `900×600` xác nhận mọi nút có icon, toolbar Admin nằm trong trang và cuộn ngang, CHECK-IN/CHECK-OUT không giao nhau, trang dài cuộn dọc và hàng/header bảng đủ chiều cao.
  - Luồng WebSocket được hủy an toàn khi đăng xuất; kiểm thử với Server thật xác nhận `QThread` đã dừng và tiến trình không còn bị Qt cưỡng bức kết thúc.
  - Tài khoản Manager trong AttendanceClient chỉ nhận dữ liệu cá nhân qua `mine=true`; cùng tài khoản trong AttendanceAdmin vẫn có đúng phạm vi quản lý phòng ban.
  - Server portable hiển thị console có tiêu đề riêng, log khởi động và hướng dẫn `Ctrl+C`; kiểm thử dừng từ console đã tắt Uvicorn đúng trình tự.

## Chưa được phép tuyên bố đã xác nhận

- Kiểm thử tải dài hạn SQLite với số lượng Client và dữ liệu sản xuất thực tế.
- HTTPS với CA nội bộ và Windows Firewall trên mạng doanh nghiệp thật.
- Hai hoặc nhiều máy Windows vật lý trong cùng LAN.
- Độ chính xác GPS thực tế trên từng máy Windows và chính sách quyền vị trí của doanh nghiệp.
- Trải nghiệm UI thủ công ở nhiều độ phân giải.
- Chạy tệp one-file `.exe` trên máy đích. Máy xây dựng hiện tại chặn bootloader one-file tạo cấu trúc thư mục tự giải nén, nhưng bản portable không cần tự giải nén đã vượt qua runtime smoke đầy đủ.

Các mục trên tiếp tục để **Pending** trong checklist cho đến khi có đúng hạ tầng nghiệm thu.
