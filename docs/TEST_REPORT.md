# Kết quả kiểm thử

Ngày chạy: 13/11/2026 (Asia/Ho_Chi_Minh, UTC+7).

## Kết quả tự động

- Python 3.12.10 trong môi trường `.venv` riêng.
- `pytest -p no:cacheprovider`: **126 passed**.
- `ruff check --no-cache server client admin scripts tests *.py`: **All checks passed**.
- `pip check`: không phát hiện dependency hỏng hoặc xung đột.
- Tất cả script PowerShell trong `scripts/` được PowerShell parser chấp nhận.
- OpenAPI có 55 đường dẫn và 69 thao tác, không trùng `operationId` hoặc thiếu tag.
- Alembic migration chạy đến revision `20261113_0006` trên SQLite.

Mỗi tiến trình pytest dùng một tệp SQLite riêng trong `.test-runtime` và tự dọn khi kết thúc,
tránh lỗi ngẫu nhiên khi chạy nhiều nhóm test đồng thời.

## Phạm vi đã kiểm tra

- Xác thực, khóa tài khoản, logout, đổi mật khẩu, thu hồi phiên và RBAC.
- Phạm vi dữ liệu Admin/Manager/Employee; bảo vệ Admin cuối cùng và tài khoản đang sử dụng.
- Đăng ký/phê duyệt thiết bị, fingerprint ổn định và nhiều tài khoản trên cùng máy.
- Check-in/check-out, ca qua đêm, UTC+7, ngưỡng muộn 14/15/16 phút, phút làm,
  idempotency, GPS, geofence và dự phòng IP LAN.
- Điều chỉnh chấm công, nghỉ phép/hủy đơn, quỹ phép, OT, lương và thưởng chuyên cần.
- Random Check, cảnh báo, thông báo và WebSocket dùng Authorization header; JWT không nằm
  trong query string.
- Dashboard, pagination, retention cleanup, Excel/PDF Unicode, backup/restore SQLite và ghi
  file nguyên tử.
- Các màn hình PySide6, logout quay lại đăng nhập, payload realtime lỗi, countdown,
  vị trí nút Random Check, hiệu ứng 3D và tương phản sáng/tối của nút/bảng.
- Khởi tạo lần đầu chỉ seed database chưa có tài khoản; không ghi đè database đang sử dụng.
- `run_all.ps1` dùng đúng ba launcher và có watchdog dừng Admin/User khi Server đóng.

## Các lỗi hồi quy vừa được bổ sung test

- Tạo nhân viên trùng dữ liệu trả 409 thay vì lỗi 500.
- IP máy trạm sai định dạng bị từ chối có kiểm soát.
- Dashboard Admin tính cả cảnh báo hệ thống không gắn nhân viên.
- Ca chưa check-out không được tính lương hoặc thưởng.
- Thư mục backup tương đối không phụ thuộc thư mục terminal hiện tại.
- WebSocket acceptance không truyền token trong URL.
- Dữ liệu mẫu mặc định đi đúng `server/data/attendance.db` và chế độ `--if-empty` giữ nguyên
  dữ liệu hiện hữu.

## Chưa được xác nhận trên hạ tầng thật

- Kiểm thử tải dài hạn với số lượng Client và dữ liệu sản xuất lớn.
- HTTPS với CA nội bộ và Windows Firewall trên mạng doanh nghiệp thật.
- Hai hoặc nhiều máy Windows vật lý trong cùng LAN.
- Độ chính xác GPS thực tế trên từng loại thiết bị.
- Trải nghiệm UI thủ công trên nhiều độ phân giải và tỉ lệ DPI.

Các mục này cần được nghiệm thu trên đúng hạ tầng triển khai; kết quả test tự động không thay thế
kiểm thử vận hành thực tế.
