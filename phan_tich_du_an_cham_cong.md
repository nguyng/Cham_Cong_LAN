TRƯỜNG ĐẠI HỌC KIẾN TRÚC ĐÀ NẴNG
KHOA CÔNG NGHỆ THÔNG TIN
PHÂN TÍCH HỆ THỐNG THÔNG TIN
HỌC PHẦN: MẠNG MÁY TÍNH / LẬP TRÌNH MẠNG
ĐỀ TÀI:
XÂY DỰNG HỆ THỐNG QUẢN LÝ VÀ CHẤM CÔNG TRỰC TUYẾN ĐỊNH VỊ GEOFENCING THỜI GIAN THỰC CHO QUÁN HAWA'S FOOD ĐÀ NẴNG

| Người hướng dẫn khoa học:  TS. Đặng Hùng Vĩ Tên nhóm thực hiện:  Huan rose và dong bon Lớp:  23CT1          Khóa:  2023 Nhóm sinh viên thực hiện (5 thành viên): 1. Ngô Đức An (Trưởng nhóm - MSSV: 114534) - Phân hệ MOD-01 & An ninh mạng 2. Nguyễn Văn Nguyên (Thành viên - MSSV: 115201) - Phân hệ MOD-02 & CSDL ERD 3. Trần Đức Trí (Thành viên - MSSV: 114889) - Phân hệ MOD-03 & Thuật toán xếp ca 4. Nguyễn Ngọc Thương (Thành viên - MSSV: 115042) - Phân hệ MOD-05 & Đối soát Excel 5. Vũ Huy Hoàng (Thành viên - MSSV: 114776) - Phân hệ MOD-04 & Geofencing / WebSocket |
| --- |

Đà Nẵng, năm 2026
DANH MỤC TỪ VIẾT TẮT

| Ký hiệu | Thuật ngữ tiếng Anh đầy đủ | Ý nghĩa nghiệp vụ trong đề tài |
| --- | --- | --- |
| FR | Functional Requirement | Yêu cầu chức năng của hệ thống chấm công |
| NFR | Non-Functional Requirement | Yêu cầu phi chức năng (Hiệu năng, an toàn, bảo mật đường truyền) |
| IPO | Input – Process – Output | Mô hình mô tả chi tiết: Đầu vào – Các bước xử lý – Đầu ra |
| CRUD | Create – Read – Update – Delete | 4 thao tác dữ liệu cơ bản: Tạo mới, Xem, Cập nhật, Xóa |
| PK / FK / UQ | Primary Key / Foreign Key / Unique | Khóa chính / Khóa ngoại / Ràng buộc duy nhất trong CSDL |
| ERD | Entity Relationship Diagram | Sơ đồ quan hệ thực thể mô hình hóa cơ sở dữ liệu |
| DFD | Data Flow Diagram | Sơ đồ luồng dữ liệu (Cấp 0 ngữ cảnh, Cấp 1 phân rã tiến trình) |
| Geofencing | Geographic Fencing | Hàng rào địa lý ảo dùng toạ độ GPS vệ tinh để giới hạn vùng chấm công |
| WebSocket | Full-duplex TCP Protocol (RFC 6455) | Giao thức truyền thông hai chiều thời gian thực giữa Client và Server |
| JWT | JSON Web Token (RFC 7519) | Chuỗi mã hóa phi trạng thái dùng xác thực phiên làm việc an toàn |
| TLS / HTTPS | Transport Layer Security / HTTP Secure | Giao thức mã hóa an toàn tầng giao vận bảo vệ thông tin toạ độ trên đường truyền |
| RBAC | Role-Based Access Control | Kiểm soát quyền truy cập dựa trên vai trò người dùng |
| NTP | Network Time Protocol | Giao thức đồng bộ giờ chuẩn máy chủ nhằm chống gian lận giờ thiết bị |
| ACID | Atomicity, Consistency, Isolation, Durability | Các đặc tính bảo đảm tính toàn vẹn tuyệt đối của giao dịch CSDL |

MỤC LỤC
- LỜI MỞ ĐẦU
- 1. ĐẶT TÊN ĐỀ TÀI
- 1.1. Tên ứng dụng đề xuất
- 1.2. Bối cảnh và vấn đề cần giải quyết
- 1.3. Mục tiêu và phạm vi
- 1.4. Khảo sát các ứng dụng liên quan
- 2. ĐẶC TẢ YÊU CẦU CHỨC NĂNG
- 2.1. Quy ước và nguồn yêu cầu
- 2.2. Yêu cầu phi chức năng và tiêu chí kiểm tra
- 2.3. Quy tắc nghiệp vụ chung
- 3. PHÂN TÍCH ĐỐI TƯỢNG VÀ NHÓM CHỨC NĂNG
- 3.1. Danh sách đối tượng
- 3.2. Phân hệ nhóm chức năng
- 3.3. Tác nhân và hệ thống liên quan
- 4. PHÂN TÍCH CHỨC NĂNG ĐẾN TẬN CÙNG
- 4.1. Cấu trúc phân rã chức năng (WBS & FDD)
- 4.1.1. Sơ đồ phân rã chức năng dạng khối hình cây (FDD)
- 4.1.2. Sơ đồ kiến trúc liên kết phân hệ chức năng
- 4.2. Mô tả module theo IPO
- 4.2.1. Phân hệ Quản trị & Bảo mật hệ thống
- 4.2.2. Phân hệ Cấu hình Quán & Geofencing
- 4.2.3. Phân hệ Quản lý Ca làm & Lập lịch phân ca
- 4.2.4. Phân hệ Điểm danh Geofencing, WebSocket & Sơ đồ tuần tự (Sequence Diagram)
- 4.2.5. Phân hệ Giải trình sai lệch & Khóa sổ công Excel
- 5. LUỒNG DỮ LIỆU LIÊN QUAN ĐẾN ĐỐI TƯỢNG VÀ CHỨC NĂNG
- 5.1. Ma trận đối tượng và chức năng CRUD
- 5.2. Mô tả luồng dữ liệu chính (DF-01 đến DF-06)
- 5.3. Minh họa liên kết xuyên suốt (End-to-End Scenario)
- 5.4. Sơ đồ máy trạng thái (State Machine Diagram) - Vòng đời ca làm việc & Bản ghi chấm công
- 5.5. Sơ đồ quy trình nghiệp vụ tổng thể khép kín (Workflow)
- 6. THIẾT KẾ CƠ SỞ DỮ LIỆU
- 6.1. Danh sách bảng
- 6.2. Chi tiết thuộc tính từng bảng (8 bảng CSDL)
- 6.3. Sơ đồ quan hệ ERD
- 6.3.1. Phân loại cấu trúc Gốc – Cành – Lá và quan hệ tiêu biểu
- 6.3.2. Toàn vẹn tham chiếu và cơ chế giao dịch ACID
- 7. CHIA VÀ QUẢN LÝ CÔNG VIỆC THEO NHÓM
- 7.1. Phân công vai trò trong nhóm
- 7.1.1. Phân công theo năm phân hệ
- 7.2. Cách thức chia công việc theo giai đoạn
- 7.3. Theo dõi và nghiệm thu công việc
- 7.4. Tiêu chí bàn giao và kiểm tra chéo
- 7.5. Kế hoạch kiểm thử nghiệp vụ trọng tâm (16 Test Cases)
- KẾT LUẬN
- TÀI LIỆU THAM KHẢO
- PHỤ LỤC A: TÀI LIỆU THAM CHIẾU 10 TRANG SƠ ĐỒ KỸ THUẬT DRAW.IO
LỜI MỞ ĐẦU
Trong lĩnh vực kinh doanh dịch vụ ăn uống (F&B - Food & Beverage), việc quản lý nhân sự và giám sát chấm công hàng ngày luôn là bài toán đau đầu đối với các chủ cửa hàng và quản lý ca. Đặc thù của ngành ẩm thực là nhân viên làm việc theo ca kíp linh hoạt (ca sáng, ca chiều, ca tối, ca gãy), tỷ lệ nhân viên bán thời gian (part-time) cao và giờ vào ca thường diễn ra dồn dập trong khoảng 5 – 10 phút trước khi bắt đầu phục vụ khách hàng.
Hiện nay, nhiều cửa hàng vẫn sử dụng các phương thức điểm danh truyền thống như:
1. Máy chấm công vân tay vật lý: Thường xuyên xảy ra hiện tượng mòn vân tay do nhân viên phục vụ, pha chế và rửa chén tiếp xúc liên tục với nước và hóa chất tẩy rửa; đồng thời gây tắc nghẽn cục bộ trước cửa quán vào giờ giao ca và tốn chi phí bảo trì phần cứng.
2. Điểm danh bằng sổ sách hoặc bảng tính Excel thủ công: Dễ xảy ra sai sót, ghi chép gian lận hoặc bao che giờ đi làm trễ giữa các nhân viên.
3. Thẻ từ hoặc chấm công chụp hình thông thường: Dễ dàng bị gian lận bằng hình thức quẹt thẻ hộ hoặc gửi ảnh chụp từ xa.
Nhằm giải quyết triệt để các tồn tại trên, nhóm sinh viên nghiên cứu và phát triển đề tài: “Xây dựng hệ thống quản lý và chấm công trực tuyến định vị Geofencing thời gian thực cho quán Hawa's Food Đà Nẵng”. Đề tài được xây dựng theo kiến trúc Mạng máy tính Client – Server hiện đại:
- Phía Client (Thiết bị di động của nhân viên & Trình duyệt máy tính của quản lý): Ứng dụng Web Mobile cho phép nhân viên sử dụng chính chiếc điện thoại cá nhân có kết nối Internet để thực hiện thao tác điểm danh nhanh chóng thông qua trích xuất toạ độ định vị toàn cầu (GPS API) và gửi yêu cầu xác thực qua giao thức bảo mật HTTPS.
- Đường truyền an toàn: Toàn bộ dữ liệu toạ độ, định danh người dùng và thời gian thực được bảo vệ bằng cơ chế mã hóa kênh truyền TLS/HTTPS và kiểm thực không trạng thái JWT (JSON Web Token), ngăn chặn hoàn toàn các cuộc tấn công bắt lén (Sniffing) hoặc giả mạo gói tin (Man-In-The-Middle).
- Phía Server (Máy chủ trung tâm): Đóng vai trò “bộ não” xử lý tính toán khoảng cách thực tế bằng giải thuật lượng giác hình cầu Haversine giữa vị trí nhân viên với vị trí toạ độ chính thức của quán. Chỉ khi khoảng cách $d \le 50\,\text{m}$ và đối soát hợp lệ với dải mạng Wi-Fi nội bộ, máy chủ mới chấp thuận ghi nhận bản ghi chấm công. Đồng thời, máy chủ kích hoạt kênh truyền thông hai chiều WebSocket (TCP Full-duplex) để phát thông báo tức thời (Live Event) lên màn hình giám sát của Quản lý ca mà không cần tải lại trang.
Báo cáo này được cấu trúc chặt chẽ theo 7 nội dung học thuật chuẩn mực, từ phân tích bài toán, xác định yêu cầu chức năng/phi chức năng, mô hình hóa luồng dữ liệu DFD, thiết kế CSDL quan hệ ERD chuẩn hóa, đến phân rã module IPO và tổ chức phân công công việc chi tiết cho 5 thành viên trong nhóm.
1. ĐẶT TÊN ĐỀ TÀI
1.1. Tên ứng dụng đề xuất
- Tên tiếng Việt chuẩn học thuật: Hệ thống Quản lý và Chấm công Trực tuyến Định vị Geofencing Thời gian thực cho Quán Hawa's Food Đà Nẵng.
- Tên tiếng Anh: Real-time Geofencing-based Online Attendance Management System for Hawa's Food Da Nang.
- Cấu trúc 3 thành phần theo chuẩn kỹ thuật phần mềm:
1. *Loại hình / Nền tảng:* Hệ thống Client – Server trực tuyến (Web Mobile & Dashboard).
2. *Hành động / Chức năng cốt lõi:* Quản lý phân ca, thẩm định toạ độ Geofencing, điểm danh trực tuyến và giám sát Live WebSocket.
3. *Đối tượng & Phạm vi áp dụng:* Toàn bộ nhân viên, quản lý ca và chủ quán tại cửa hàng ẩm thực Hawa's Food Đà Nẵng.
1.2. Bối cảnh và vấn đề cần giải quyết
Quán Hawa's Food Đà Nẵng là mô hình nhà hàng ẩm thực phục vụ đồ ăn nhanh và giải khát, vận hành liên tục từ 06:00 đến 23:00 hàng ngày. Đội ngũ nhân sự gồm hơn 30 nhân viên chia thành các bộ phận: Phục vụ, Pha chế, Thu ngân và Tiếp thực. Việc quản lý thời gian đi làm đối mặt với các khó khăn thực tiễn:
- Tình trạng "chấm công hộ": Nhân viên nhờ đồng nghiệp quẹt thẻ hoặc báo cáo điểm danh hộ khi chưa đến quán.
- Giả mạo vị trí (Fake GPS): Nhiều nhân viên sử dụng các ứng dụng chỉnh sửa toạ độ trên điện thoại để báo danh từ xa khi đang ở phòng trọ. Hệ thống cần giải pháp thẩm định kép kết hợp toạ độ vệ tinh với kiểm tra địa chỉ IP mạng Wi-Fi tại quán.
- Độ trễ thông tin ca làm việc: Quản lý ca thường không nắm bắt được kịp thời ai đi trễ, ai vắng mặt vào đầu ca để kịp thời điều động người thay thế, dẫn đến tình trạng thiếu hụt nhân sự phục vụ khách trong giờ cao điểm.
- Tranh chấp giờ làm cuối tháng: Thường xuyên xảy ra sai lệch giữa trí nhớ nhân viên và sổ chấm công tay, dẫn đến các khiếu nại kéo dài làm mất thời gian đối soát của kế toán và chủ quán.
1.3. Mục tiêu và phạm vi
Bảng 1.1. Phân định mục tiêu và phạm vi 5 phân hệ

| Mã phân hệ | Tên phân hệ | Mục tiêu kỹ thuật cốt lõi | Phạm vi công việc cụ thể |
| --- | --- | --- | --- |
| MOD-01 | Quản trị & Bảo mật hệ thống | Đảm bảo an toàn mạng, xác thực định danh và phân quyền truy cập RBAC. | Cấp phát tài khoản; kiểm thực chữ ký điện tử JWT; ghi nhận Audit Log vết chỉnh sửa; mã hóa mật khẩu bcrypt; cơ chế hết hạn phiên đăng nhập. |
| MOD-02 | Cấu hình Quán & Geofencing | Thiết lập ranh giới địa lý ảo và hạ tầng mạng điểm danh. | Lưu toạ độ vĩ độ/kinh độ chính thức của quán; cấu hình bán kính cho phép ($R = 50\,\text{m}$); đăng ký dải IP mạng Wi-Fi nội bộ; cài đặt quy tắc đi sớm/về trễ. |
| MOD-03 | Quản lý Ca làm & Lập lịch | Số hóa lịch làm việc, loại bỏ chồng chéo ca kíp. | Định nghĩa khung giờ ca (Sáng, Chiều, Tối, Gãy); phân bổ nhân viên vào ca theo tuần; tự động validate chống trùng ca; công bố lịch ca xuống điện thoại nhân viên. |
| MOD-04 | Điểm danh Geofencing & WebSocket | Tự động hóa đo khoảng cách và phản hồi sự kiện thời gian thực. | Lấy toạ độ HTML5 Geolocation phía Client; tính khoảng cách Haversine tại Server; ghi nhận Check-in/Check-out; broadcast sự kiện qua WebSocket tới Quản lý. |
| MOD-05 | Giải trình & Khóa sổ công Excel | Xử lý linh hoạt các tình huống ngoại lệ và bảo toàn tính toàn vẹn dữ liệu. | Cho phép gửi đơn giải trình khi quên bấm công (kèm ảnh minh chứng); Quản lý phê duyệt; khóa sổ công kỳ tháng chống sửa đổi; trích xuất báo cáo chấm công định dạng Excel (.xlsx). |

Ranh giới loại trừ phạm vi (Out of Scope): Để đảm bảo tính chuyên sâu và đúng trọng tâm kỹ thuật của học phần Mạng máy tính & Phân tích hệ thống, đồ án tuyệt đối không bao gồm: tính toán lương/thưởng tiền mặt, quản lý thực đơn món ăn, quản lý công thức chế biến, gọi món (POS), quản lý kho nguyên liệu hoặc thanh toán hóa đơn. Hệ thống chỉ tập trung 100% vào nghiệp vụ điểm danh và thời gian làm việc.
1.4. Khảo sát các ứng dụng liên quan
Bảng 1.2. So sánh giải pháp của hệ thống với các sản phẩm trên thị trường

| Tiêu chí so sánh | Tanca | Base Check-in | 1Office | Hệ thống Hawa's Food (Đề xuất) |
| --- | --- | --- | --- | --- |
| Kiến trúc triển khai | Cloud SaaS (Đa doanh nghiệp) | Cloud SaaS | Cloud ERP tổng thể | Client – Server chuyên biệt cho chuỗi F&B |
| Phương thức xác thực | GPS Mobile App, Wi-Fi BSSID | Máy nhận diện khuôn mặt / GPS | GPS App, Máy chấm công vật lý | Thẩm định kép: GPS Haversine + IP Wi-Fi nội bộ |
| Giám sát thời gian thực | Cập nhật định kỳ (Polling vài phút) | Cập nhật theo lô (Batch sync) | Tải lại trang (F5 Refresh) | WebSocket Full-duplex TCP (Đổi màu ngay lập tức < 100ms) |
| Cơ chế chống Fake GPS | Kiểm tra chế độ Mock Location OS | Nhận diện khuôn mặt AI | Ràng buộc mạng Wi-Fi | Kiểm tra sai số Accuracy + Đối soát IP nguồn máy chủ |
| Xử lý giải trình | Quy trình phê duyệt qua App | Gửi phiếu yêu cầu qua Web | Module đơn từ hành chính | Quy trình giải trình đối soát trực tiếp, gắn liền bản ghi điểm danh |
| Khóa sổ dữ liệu | Khóa theo chu kỳ lương | Khóa theo ngày | Khóa phân hệ kế toán | Ràng buộc toàn vẹn `is_locked = TRUE` chống gian lận lịch sử |
| Chi phí & Độ linh hoạt | Trả phí thuê bao hàng tháng | Chi phí bản quyền cao | Chi phí gói doanh nghiệp lớn | Mã nguồn mở, chi phí 0đ, tối ưu cho máy chủ cục bộ hoặc VPS giá rẻ |

2. ĐẶC TẢ YÊU CẦU CHỨC NĂNG
2.1. Quy ước và nguồn yêu cầu
- Các yêu cầu chức năng được ký hiệu thống nhất bằng tiền tố FR-XX (Functional Requirement).
- Mỗi FR có thể truy vết nguồn gốc (Traceability) tới các phân hệ nghiệp vụ MOD-XX và các Actor thực hiện.
- Mức độ ưu tiên được phân thành:
- Cao (High): Bắt buộc phải có để hệ thống vận hành nghiệp vụ chấm công cốt lõi và đảm bảo an toàn mạng.
- Trung bình (Medium): Các tiện ích nâng cao trải nghiệm người dùng và tự động hóa cảnh báo.
- Thấp (Low): Bổ trợ giao diện và mở rộng tối ưu hóa.
Bảng 2.1. Đặc tả chi tiết các yêu cầu chức năng (FR)

| Mã YC | Tên yêu cầu chức năng | Mô tả chi tiết nghiệp vụ & kỹ thuật | Ưu tiên | Truy vết nguồn |
| --- | --- | --- | --- | --- |
| FR-01 | Đăng nhập an toàn & Cấp JWT | Người dùng gửi tài khoản/mật khẩu qua HTTPS. Máy chủ kiểm tra hash bcrypt, khởi tạo phiên làm việc và trả về Token JWT kèm thông tin vai trò (Role). | Cao | MOD-01; Actor: Toàn bộ |
| FR-02 | Phân quyền truy cập RBAC | Chặn các truy cập trái thẩm quyền ở cả tầng giao diện và tầng máy chủ (API Middleware). Nhân viên chỉ thấy lịch của mình; Quản lý xem toàn ca; Chủ quán xem toàn bộ. | Cao | MOD-01; Actor: Admin, Chủ quán |
| FR-03 | Ghi nhận Audit Log vết thao tác | Mọi thao tác nhạy cảm (sửa giờ chấm công, duyệt đơn giải trình, xóa ca làm) đều phải tự động ghi lại IP, mã người thực hiện, thời điểm và giá trị cũ/mới. | Cao | MOD-01; Actor: Hệ thống |
| FR-04 | Cấu hình toạ độ & Bán kính quán | Cho phép Chủ quán ghim vị trí cửa hàng trên bản đồ số, lưu toạ độ Latitude/Longitude và cài đặt bán kính cho phép chấm công ($R = 50\,\text{m}$). | Cao | MOD-02; Actor: Chủ quán |
| FR-05 | Đăng ký dải IP mạng Wi-Fi quán | Lưu trữ dải địa chỉ IP Public hoặc Subnet Wi-Fi của cửa hàng vào CSDL để làm căn cứ thẩm định kép, chống hành vi giả lập GPS ngoài quán. | Trung bình | MOD-02; Actor: Chủ quán, Admin |
| FR-06 | Cài đặt khung giờ & Quy định ca | Khai báo các ca làm việc tiêu chuẩn: Ca sáng (06:00 – 12:00), Ca chiều (12:00 – 18:00), Ca tối (18:00 – 23:00); quy định thời gian cho phép đến sớm (15 – 30 phút). | Cao | MOD-02; Actor: Chủ quán |
| FR-07 | Lập lịch phân ca làm việc tuần | Cho phép Quản lý ca xếp nhân viên vào từng ca cụ thể cho từng ngày trong tuần. Hiển thị trực quan bảng ma trận Nhân sự – Ngày làm. | Cao | MOD-03; Actor: Quản lý ca |
| FR-08 | Kiểm tra tự động xung đột lịch | Khi bấm lưu phân ca, hệ thống kiểm tra CSDL: nếu 1 nhân viên bị xếp vào 2 ca trùng giờ nhau thì báo lỗi và từ chối lưu lịch. | Cao | MOD-03; Actor: Quản lý ca |
| FR-09 | Công bố lịch làm việc | Chuyển trạng thái lịch từ "Bản nháp" sang "Chính thức". Đẩy thông báo tức thời tới màn hình điện thoại của toàn thể nhân viên. | Cao | MOD-03; Actor: Quản lý ca |
| FR-10 | Trích xuất toạ độ GPS thiết bị | Client Web Mobile kích hoạt  navigator.geolocation.getCurrentPosition() , lấy toạ độ $lat, lng$ và bán kính sai số $accuracy$. Chặn nếu sai số $> 30\,\text{m}$. | Cao | MOD-04; Actor: Nhân viên |
| FR-11 | Thẩm định Geofencing Haversine | Máy chủ nhận toạ độ, chạy công thức Haversine để tính khoảng cách $d$ tới quán. Rẽ nhánh: Nếu $d \le 50\,\text{m}$ thì duyệt tiếp; nếu $d > 50\,\text{m}$ thì trả về HTTP 403. | Cao | MOD-04; Actor: Máy chủ |
| FR-12 | Ghi nhận Check-in vào ca | So sánh giờ máy chủ NTP với giờ bắt đầu ca: Ghi nhận giờ vào thực tế, đánh dấu trạng thái  ON_TIME  (Đúng giờ) hoặc  LATE  (Đi trễ). | Cao | MOD-04; Actor: Nhân viên |
| FR-13 | Ghi nhận Check-out hết ca | Khi hết giờ, nhân viên quét lại GPS để check-out: So sánh giờ ra thực tế với giờ kết thúc ca: Đánh dấu  ON_TIME  hoặc  EARLY_LEAVE  (Về sớm), tính tổng số phút làm. | Cao | MOD-04; Actor: Nhân viên |
| FR-14 | Phát thông báo Live qua WebSocket | Ngay sau khi ghi nhận Check-in/Check-out thành công, máy chủ phát sự kiện  WS_ATTENDANCE_SUCCESS  tới phòng (Room) của Quản lý ca qua Socket.io. | Cao | MOD-04; Actor: Hệ thống |
| FR-15 | Màn hình Live Monitor Quản lý | Trang web quản lý lắng nghe sự kiện WebSocket, tự động cập nhật màu sắc trạng thái của nhân viên từ Xám (Chưa đến) sang Xanh (Đang làm việc) mà không cần F5. | Cao | MOD-04; Actor: Quản lý ca |
| FR-16 | Nộp đơn giải trình quên bấm công | Nếu nhân viên quên bấm công hoặc GPS bị lỗi thiết bị, cho phép làm đơn giải trình: nhập giờ vào/ra thực tế, lý do và đính kèm đường dẫn ảnh bằng chứng. | Cao | MOD-05; Actor: Nhân viên |
| FR-17 | Phê duyệt đơn giải trình | Quản lý ca kiểm tra nhật ký camera hoặc xác nhận thực tế: Nhấn duyệt đơn $\rightarrow$ Hệ thống tự động điền giờ công vào bảng  attendances  và lưu Audit Log. | Cao | MOD-05; Actor: Quản lý ca |
| FR-18 | Cảnh báo ca làm việc bất thường | Hệ thống tự động lọc các ca có vấn đề: Quên check-out ( MISSING_OUT ), Vắng không phép ( ABSENT ), hoặc đi trễ trên 60 phút để quản lý xử lý trước kỳ chốt. | Trung bình | MOD-05; Actor: Quản lý ca |
| FR-19 | Khóa sổ điểm danh kỳ tháng | Vào ngày cuối tháng, Quản lý/Chủ quán thực hiện lệnh chốt công: Cập nhật cờ  is_locked = TRUE  trên toàn bộ bản ghi của tháng. Khóa toàn bộ quyền sửa đổi. | Cao | MOD-05; Actor: Chủ quán |
| FR-20 | Xuất báo cáo chấm công Excel | Xuất toàn bộ dữ liệu công chuẩn hóa ra file  .xlsx  gồm: Tên nhân viên, tổng số ca làm, số giờ chuẩn, số lần đi trễ, số lần về sớm phục vụ đối soát. | Cao | MOD-05; Actor: Quản lý ca, Chủ quán |

2.2. Yêu cầu phi chức năng và tiêu chí kiểm tra (NFR)
Bảng 2.2. Yêu cầu phi chức năng (NFR)

| Mã YC | Thuộc tính chất lượng | Nội dung yêu cầu kỹ thuật | Tiêu chí kiểm tra & Đo lường |
| --- | --- | --- | --- |
| NFR-01 | Thời gian đáp ứng (Response Time) | Thời gian xử lý một yêu cầu chấm công từ lúc bấm nút đến khi nhận phản hồi $\le 500\,\text{ms}$. | Đo lường bằng Postman / JMeter với 50 requests đồng thời qua mạng 4G. |
| NFR-02 | Độ trễ thời gian thực (Real-time Latency) | Gói tin WebSocket phát từ Server tới Dashboard Quản lý ca có độ trễ truyền gói tin $\le 100\,\text{ms}$. | Kiểm tra Timestamp trong khung dữ liệu WebSocket Frame giữa Server và Client. |
| NFR-03 | Độ chính xác định vị (GPS Precision) | Thuật toán Haversine đo khoảng cách phải có sai số tính toán lý thuyết $< 1\,\text{m}$; độ chính xác phần cứng GPS Client $< 15\,\text{m}$. | Đối chiếu kết quả hàm tính toán với số liệu thực tế đo đạc bằng thước trắc địa Google Earth. |
| NFR-04 | Bảo mật kênh truyền (Transport Security) | 100% dữ liệu trao đổi giữa Client và Server bắt buộc chạy qua giao thức HTTPS (TLS 1.3) và WSS (WebSocket Secure). | Dùng Wireshark bắt gói tin: Mọi trường toạ độ, mật khẩu, JWT đều phải ở dạng mã hóa ciphertext. |
| NFR-05 | Bảo mật phiên (Session Security) | Chuỗi Token JWT ký thuật toán HMAC-SHA256 với secret key an toàn; thời hạn sống tối đa 24 giờ; tự động hủy phiên khi logout. | Thử giả mạo chữ ký JWT hoặc gửi token hết hạn $\rightarrow$ Server trả về lỗi 401 Unauthorized. |
| NFR-06 | Chống gian lận thời gian (Time Anti-spoofing) | Giờ chấm công được lấy tuyệt đối từ máy chủ Server đồng bộ giờ NTP quốc gia, không phụ thuộc vào giờ cài đặt trên điện thoại người dùng. | Chỉnh giờ trên điện thoại chạy trước 2 tiếng $\rightarrow$ Giờ ghi nhận trong CSDL vẫn là giờ chuẩn máy chủ. |
| NFR-07 | Tính sẵn sàng & Bền bỉ (High Availability) | Hệ thống hoạt động liên tục 24/7 với độ sẵn sàng $\ge 99.5\%$, tự động phục hồi kết nối WebSocket khi nhân viên đi vào vùng sóng yếu. | Kiểm tra kịch bản mất mạng 5 giây: Client tự động phát lệnh  reconnect  và đồng bộ lại trạng thái. |
| NFR-08 | Tính tương thích giao diện (Responsiveness) | Giao diện Web hiển thị mượt mà, co giãn tự nhiên trên màn hình smartphone (iOS Safari, Android Chrome) và Desktop màn hình rộng. | Kiểm tra hiển thị chuẩn trên Chrome DevTools với kích thước iPhone 12/13/14 (390px) và Desktop (1920px). |

2.3. Quy tắc nghiệp vụ chung (Business Rules - BR)
- BR-01 (Khoảng cách điểm danh): Điểm danh chỉ hợp lệ khi khoảng cách tính toán từ vị trí người dùng đến tâm quán $d \le 50\,\text{m}$. Nếu $d > 50\,\text{m}$, hệ thống từ chối ghi nhận và thông báo khoảng cách thực tế đang cách quán bao nhiêu mét.
- BR-02 (Thời gian vào ca cho phép): Nhân viên được phép bấm check-in vào ca sớm tối đa 30 phút trước giờ bắt đầu ca. Bấm trước 30 phút hệ thống sẽ thông báo: "Chưa tới khung giờ điểm danh của ca này".
- BR-03 (Phân loại trạng thái Vào ca):
- Check-in từ [Giờ bắt đầu ca - 30 phút] đến [Giờ bắt đầu ca + 5 phút]: Ghi nhận  ON_TIME  (Đúng giờ).
- Check-in sau [Giờ bắt đầu ca + 5 phút]: Ghi nhận  LATE  (Đi trễ), tự động tính số phút trễ.
- BR-04 (Phân loại trạng thái Ra ca):
- Check-out trước [Giờ kết thúc ca - 10 phút]: Ghi nhận  EARLY_LEAVE  (Về sớm), tự động tính số phút về sớm.
- Check-out từ [Giờ kết thúc ca - 10 phút] trở đi: Ghi nhận hoàn thành ca chuẩn.
- BR-05 (Chống trùng lịch làm việc): Một nhân viên không thể được xếp vào 2 ca làm việc có khoảng thời gian đè lên nhau trong cùng một ngày.
- BR-06 (Tính bất biến của dữ liệu đã chốt): Các bản ghi chấm công có cờ  is_locked = TRUE  không thể bị chỉnh sửa hoặc xóa bởi bất kỳ người dùng nào, kể cả tài khoản Quản trị. Mọi yêu cầu điều chỉnh phải lập biên bản đối soát bằng văn bản ngoài hệ thống.
- BR-07 (Toàn vẹn điểm danh kép): Trong một ca làm việc, một nhân viên chỉ có tối đa 1 bản ghi chấm công; không thể thực hiện Check-out nếu chưa thực hiện Check-in hợp lệ.
3. PHÂN TÍCH ĐỐI TƯỢNG VÀ NHÓM CHỨC NĂNG
3.1. Danh sách đối tượng (Entities)
Bảng 3.1. Danh sách 5 thực thể dữ liệu cốt lõi của hệ thống

| Mã đối tượng | Tên đối tượng | Ý nghĩa nghiệp vụ | Thuộc tính chính | Quan hệ với đối tượng khác |
| --- | --- | --- | --- | --- |
| ENT-01 | Người dùng (`users`) | Lưu thông tin định danh và phân quyền toàn bộ các tài khoản tham gia hệ thống (Admin, Chủ quán, Quản lý, Kế toán, Nhân viên). | id ,  username ,  password_hash ,  full_name ,  role ,  phone_number ,  is_active | 1 : N với  ENT-04  (Lịch phân ca) 1 : N với  ENT-05  (Bản ghi chấm công) |
| ENT-02 | Vị trí quán & Hạ tầng mạng (`shop_locations`) | Đại diện cho không gian chấm công thực tế của quán Hawa's Food gồm toạ độ địa lý ($lat, lng$), bán kính Geofencing ($50m$) và thông tin dải mạng Wi-Fi/IP nội bộ phục vụ thẩm định kép. | id ,  name ,  latitude ,  longitude ,  radius_meters ,  address ,  wifi_ssid ,  ip_address | 1 : N với  ENT-03  (Ca làm việc) |
| ENT-03 | Ca làm việc (`shifts`) | Định nghĩa danh mục các khung giờ làm việc tiêu chuẩn của quán (ca sáng, ca chiều, ca tối, ca gãy) và quy chế dung sai giờ giấc. | id ,  location_id ,  shift_code ,  shift_name ,  start_time ,  end_time | N : 1 với  ENT-02  (Vị trí quán) 1 : N với  ENT-04  (Lịch phân ca) |
| ENT-04 | Lịch phân ca (`schedules`) | Kế hoạch làm việc được Quản lý phân bổ cho từng nhân viên theo từng ngày cụ thể, đóng vai trò căn cứ đối soát ca khi chấm công. | id ,  user_id ,  shift_id ,  work_date ,  status ,  assigned_by | N : 1 với  ENT-01  (Người dùng) N : 1 với  ENT-03  (Ca làm việc) 1 : 1 với  ENT-05  (Bản ghi chấm công) |
| ENT-05 | Bản ghi chấm công (`attendances`) | Dữ liệu điểm danh thực tế ghi nhận kết quả bấm công của nhân viên (thời điểm vào/ra, khoảng cách Haversine, toạ độ, trạng thái  ON_TIME / LATE , giải trình và cờ khóa sổ  is_locked ). | id ,  schedule_id ,  user_id ,  check_in_time ,  check_in_distance ,  check_out_time ,  check_out_distance ,  status ,  is_locked | 1 : 1 với  ENT-04  (Lịch phân ca) N : 1 với  ENT-01  (Người dùng) |

Ghi chú kiến trúc CSDL: 5 thực thể cốt lõi trên đại diện cho mô hình dữ liệu mức khái niệm (Conceptual Model). Khi chuyển sang thiết kế cơ sở dữ liệu vật lý (Mục 6), để tối ưu hóa theo dạng chuẩn 3 (3NF) và lưu vết an ninh mạng, các thuộc tính mở rộng sẽ được chuẩn hóa tách thành 8 bảng chi tiết (gồm thêm  shop_wifis ,  attendance_requests ,  audit_logs ).
3.2. Phân hệ nhóm chức năng (Modules)
Bảng 3.2. Phân hệ nhóm chức năng

| Mã phân hệ | Tên phân hệ | Mục đích nghiệp vụ | Đối tượng dữ liệu liên quan | Chức năng chính thuộc phân hệ |
| --- | --- | --- | --- | --- |
| MOD-01 | Quản trị & Bảo mật hệ thống | Cấp phát tài khoản, phân quyền RBAC và kiểm soát an ninh mạng. | ENT-01  ( users ) | Đăng nhập JWT, Phân quyền người dùng, Khóa tài khoản, Ghi vết Audit Log. |
| MOD-02 | Cấu hình Quán & Geofencing | Cấu hình tham số toạ độ địa lý, mạng Wi-Fi và quy chế làm việc. | ENT-02  ( shop_locations ),  ENT-03  ( shifts ) | Thiết lập toạ độ quán, Cài đặt bán kính 50m, Đăng ký IP Wi-Fi, Tạo danh mục ca. |
| MOD-03 | Quản lý Ca làm & Lập lịch | Lập lịch làm việc tuần, kiểm tra trùng lịch và ban hành ca làm. | ENT-01  ( users ),  ENT-03  ( shifts ),  ENT-04  ( schedules ) | Lập ma trận ca tuần, Tự động kiểm tra xung đột trùng ca, Công bố lịch ca. |
| MOD-04 | Điểm danh Geofencing & WebSocket | Thu thập toạ độ GPS, chạy giải thuật Haversine và đẩy dữ liệu tức thời. | ENT-01  ( users ),  ENT-04  ( schedules ),  ENT-05  ( attendances ) | Check-in GPS, Check-out GPS, Tính khoảng cách Haversine, Phát sự kiện Socket Live. |
| MOD-05 | Giải trình & Khóa sổ công Excel | Xử lý các phát sinh quên bấm công, chốt công tháng và xuất file báo cáo. | ENT-01  ( users ),  ENT-04  ( schedules ),  ENT-05  ( attendances ) | Nộp đơn giải trình kèm ảnh, Phê duyệt đơn, Cảnh báo ca bất thường, Khóa sổ công, Xuất file Excel. |

3.3. Tác nhân và hệ thống liên quan (Actors)
Bảng 3.3. Bảng tác nhân tham gia hệ thống

| STT | Tác nhân (Actor) | Bản chất tác nhân | Vai trò và đặc quyền trong hệ thống | Thành viên nhóm phụ trách |
| --- | --- | --- | --- | --- |
| 1 | Người quản trị (System Admin) | Con người (Chuyên viên an toàn mạng) | Quyền tối cao: Quản trị tài khoản, cấp phát và thu hồi Token JWT, phân quyền vai trò RBAC, cấu hình hệ thống, theo dõi Audit Log an ninh mạng. | Ngô Đức An |
| 2 | Chủ quán (Shop Owner) | Con người (Chủ cơ sở Hawa's Food) | Quyền nghiệp vụ cao nhất: Thiết lập toạ độ vị trí quán trên bản đồ Google, cấu hình bán kính Geofencing 50m, đăng ký dải IP Wi-Fi, cài đặt danh mục ca và quy chế đi sớm/về trễ. | Nguyễn Văn Nguyên |
| 3 | Quản lý ca (Shift Manager) | Con người (Trưởng ca trực tại quán) | Quyền điều hành ca: Lập lịch phân ca tuần cho nhân viên, tự động phát hiện xung đột trùng ca, theo dõi màn hình Live Monitor WebSocket thời gian thực, duyệt đơn đổi ca. | Trần Đức Trí |
| 4 | Kế toán / Kiểm toán đối soát công (Accountant / Timekeeper) | Con người (Bộ phận nghiệp vụ & Kiểm toán) | Quyền tổng hợp & đối soát: Quét các ca chấm công bất thường (quên check-out, đi trễ, về sớm), tiếp nhận và phê duyệt đơn giải trình, thực hiện khóa sổ công tháng ( is_locked = TRUE ), xuất bảng công Excel. | Nguyễn Ngọc Thương |
| 5 | Nhân viên (Employee) | Con người (Phục vụ, pha chế, thu ngân) | Người dùng cuối (Web Mobile): Xem lịch làm việc cá nhân trên điện thoại, bấm chấm công Check-in / Check-out bằng định vị GPS Geofencing, xem lịch sử chấm công và nộp đơn giải trình khi quên bấm. | Vũ Huy Hoàng |

Ghi chú về dịch vụ mạng nền tảng (External Services): Hệ thống Vệ tinh GPS (GPS Satellite) và Máy chủ thời gian NTP (NTP Time Server) đóng vai trò là các dịch vụ hạ tầng mạng hỗ trợ, cung cấp tín hiệu toạ độ qua W3C Geolocation API và đồng bộ xung thời gian cho máy chủ phục vụ 5 tác nhân chính nói trên vận hành.
3.3.1. Sơ đồ Use Case tổng quát toàn hệ thống
Sơ đồ Use Case dưới đây mô hình hóa trực quan ranh giới hệ thống (System Boundary), 5 tác nhân cùng 13 ca sử dụng cốt lõi và các mối quan hệ phụ thuộc «include», «extend»:
Hình 2.1. Sơ đồ Use Case tổng quát hệ thống chấm công Hawa's Food Đà Nẵng
4. PHÂN TÍCH CHỨC NĂNG ĐẾN TẬN CÙNG
4.1. Cấu trúc phân rã chức năng (WBS)
HỆ THỐNG QUẢN LÝ & CHẤM CÔNG HAWA'S FOOD
├── MOD-01: PHÂN HỆ QUẢN TRỊ & BẢO MẬT HỆ THỐNG
│   ├── MOD-01-01: Đăng nhập an toàn & Xác thực phiên qua JWT
│   ├── MOD-01-02: Phân quyền vai trò người dùng (RBAC Middleware)
│   ├── MOD-01-03: Quản lý hồ sơ tài khoản (Cấp phát, Đổi mật khẩu, Khóa tài khoản)
│   └── MOD-01-04: Giám sát nhật ký an toàn mạng (Audit Trail & Logging)
│
├── MOD-02: PHÂN HỆ CẤU HÌNH QUÁN & GEOFENCING
│   ├── MOD-02-01: Thiết lập toạ độ địa lý & Ghim bản đồ quán Hawa's Food
│   ├── MOD-02-02: Cài đặt bán kính định vị an toàn (Geofencing Radius = 50m)
│   ├── MOD-02-03: Đăng ký & Đối soát dải IP mạng Wi-Fi nội bộ
│   └── MOD-02-04: Cấu hình danh mục ca làm việc chuẩn & Quy chế dung sai đi trễ
│
├── MOD-03: PHÂN HỆ QUẢN LÝ CA LÀM & LẬP LỊCH
│   ├── MOD-03-01: Lập lịch phân ca làm việc tuần dạng ma trận trực quan
│   ├── MOD-03-02: Tự động kiểm tra xung đột trùng ca (Conflict Detection)
│   ├── MOD-03-03: Sao chép nhanh lịch ca tuần trước (Copy Schedule Pattern)
│   └── MOD-03-04: Công bố lịch làm việc chính thức xuống điện thoại nhân viên
│
├── MOD-04: PHÂN HỆ ĐIỂM DANH GEOFENCING & GIÁM SÁT LIVE WEBSOCKET
│   ├── MOD-04-01: Thu thập toạ độ GPS vệ tinh trên Web Mobile
│   ├── MOD-04-02: Tính toán khoảng cách lượng giác Haversine tại Server
│   ├── MOD-04-03: Thẩm định điều kiện Check-in / Check-out & Phân loại trạng thái
│   ├── MOD-04-04: Phát tín hiệu WebSocket Broadcast thời gian thực
│   └── MOD-04-05: Màn hình Live Monitor Quản lý tự cập nhật trạng thái (Zero-reload)
│
└── MOD-05: PHÂN HỆ GIẢI TRÌNH SAI LỆCH & KHÓA SỔ CÔNG EXCEL
├── MOD-05-01: Tạo & Gửi đơn giải trình quên bấm công kèm ảnh minh chứng
├── MOD-05-02: Quy trình thẩm định & Phê duyệt đơn giải trình của Quản lý
├── MOD-05-03: Quét tự động & Cảnh báo ca làm việc bất thường
├── MOD-05-04: Chốt sổ chấm công kỳ tháng & Khóa tính toàn vẹn dữ liệu
└── MOD-05-05: Kết xuất báo cáo tổng hợp giờ công định dạng Excel chuẩn (.xlsx)
4.1.1. Sơ đồ phân rã chức năng dạng khối hình cây (FDD – Functional Decomposition Diagram)
Để trực quan hóa toàn diện kiến trúc chức năng từ mức hệ thống tổng quát xuống từng phân hệ và module xử lý độc lập, sơ đồ phân rã chức năng (FDD) dưới đây được xây dựng tuân thủ nghiêm ngặt nguyên tắc phân rã dạng khối (Hierarchical Block Diagram):
- Khối gốc (Root): Hệ thống Quản lý & Chấm công Hawa's Food Đà Nẵng.
- Tầng 1 (5 Phân hệ chính - Phân biệt theo mã màu nhận diện):
1. *MOD-01 (Màu tím Slate):* Quản trị & Bảo mật hệ thống (4 module).
2. *MOD-02 (Màu xanh lam Ocean):* Cấu hình Quán & Geofencing (4 module).
3. *MOD-03 (Màu xanh ngọc Emerald):* Quản lý Ca làm & Lập lịch (4 module).
4. *MOD-04 (Màu cam hổ phách Amber):* Điểm danh Geofencing & WebSocket (5 module).
5. *MOD-05 (Màu đỏ thẫm Ruby):* Giải trình sai lệch & Khóa sổ Excel (5 module).
- Tầng 2 (21 Module nghiệp vụ con): Mỗi module là một khối chức năng có mã định danh chuẩn hóa, đảm bảo tính đóng gói cao (High Cohesion) và ghép nối lỏng (Loose Coupling).
Hình 4.1. Sơ đồ phân rã chức năng dạng khối hình cây (FDD - Functional Decomposition Diagram)
4.1.2. Sơ đồ kiến trúc liên kết phân hệ chức năng
Mối quan hệ điều phối luồng thực thi và chia sẻ tài nguyên giữa 5 phân hệ cốt lõi được mô hình hóa qua sơ đồ liên kết dưới đây:
Hình 4.2. Sơ đồ kiến trúc liên kết phân hệ chức năng
4.2. Mô tả module theo IPO (Input – Process – Output)
4.2.1. Module MOD-01-01: Đăng nhập an toàn & Cấp JWT
- Mã Module:  MOD-01-01
- Tên Module: Đăng nhập an toàn & Xác thực phiên làm việc qua JWT
- Thuộc phân hệ: MOD-01 Quản trị & Bảo mật hệ thống
- Mức độ ưu tiên: Cao (Bắt buộc)
- Actor: Toàn bộ người dùng (Admin, Chủ quán, Quản lý, Nhân viên)
- Quyền hạn: Public (Không yêu cầu đăng nhập trước)

| Hạng mục | Nội dung chi tiết |
| --- | --- |
| Input | • Tên đăng nhập ( username : chuỗi ký tự không rỗng). • Mật khẩu chưa mã hóa ( password : tối thiểu 6 ký tự). • Địa chỉ IP Client ( req.socket.remoteAddress ). |
| Process | 1. Hệ thống tìm kiếm bản ghi trong bảng  users  theo  username . 2. Nếu không tìm thấy hoặc tài khoản có cờ  is_active = FALSE : trả về mã lỗi HTTP 401 Unauthorized. 3. Kiểm tra tính trùng khớp của mật khẩu bằng thư viện  bcrypt.compare(password, user.password_hash) . 4. Nếu mật khẩu sai: tăng số lần đăng nhập sai, nếu vượt quá 5 lần thì tạm khóa tài khoản 15 phút và ghi Audit Log. 5. Nếu thông tin chính xác: khởi tạo chuỗi JWT Payload chứa  { userId, username, role, exp }  với thời hạn sống 24h, ký bằng Secret Key HMAC-SHA256. 6. Ghi nhật ký vào bảng  audit_logs  hành động  LOGIN_SUCCESS . |
| Output | • Mã HTTP 200 OK. • Chuỗi  accessToken  (JWT). • Đối tượng thông tin người dùng:  { id, fullName, role } . |
| Luồng dữ liệu | Đọc  users ; Ghi  audit_logs . |

4.2.2. Module MOD-02-01: Thiết lập toạ độ địa lý & Ghim bản đồ quán
- Mã Module:  MOD-02-01
- Tên Module: Thiết lập toạ độ địa lý & Ghim vị trí quán Hawa's Food
- Thuộc phân hệ: MOD-02 Cấu hình Quán & Geofencing
- Mức độ ưu tiên: Cao
- Actor: Chủ quán (Shop Owner), Quản trị viên (Admin)
- Quyền hạn: Role =  OWNER  hoặc  ADMIN

| Hạng mục | Nội dung chi tiết |
| --- | --- |
| Input | • Tên cơ sở ( name : ví dụ "Hawa's Food - Cơ sở Hải Châu Đà Nẵng"). • Toạ độ vĩ độ ( latitude : số thực float từ -90 đến 90). • Toạ độ kinh độ ( longitude : số thực float từ -180 đến 180). • Bán kính cho phép ( radius_meters : mặc định 50m). • Địa chỉ thực tế ( address : chuỗi văn bản). |
| Process | 1. Hệ thống kiểm tra quyền hạn của Token JWT gửi kèm ở Header Authorization. 2. Validate dữ liệu: kiểm tra toạ độ nằm trong phạm vi lãnh thổ Việt Nam hợp lệ; bán kính nằm trong khoảng từ 20m đến 200m. 3. Lưu bản ghi mới hoặc cập nhật bản ghi hiện tại trong bảng  shop_locations . 4. Ghi nhận nhật ký thay đổi vào bảng  audit_logs  với giá trị toạ độ cũ và toạ độ mới. |
| Output | • Mã HTTP 200 OK kèm thông tin địa điểm đã được cập nhật thành công. • Hiển thị vòng tròn Geofencing trực quan trên bản đồ giao diện Chủ quán. |
| Luồng dữ liệu | Ghi / Cập nhật  shop_locations ; Ghi  audit_logs . |

4.2.3. Module MOD-03-02: Tự động kiểm tra xung đột trùng ca làm việc
- Mã Module:  MOD-03-02
- Tên Module: Tự động kiểm tra xung đột trùng ca làm việc (Conflict Detection)
- Thuộc phân hệ: MOD-03 Quản lý Ca làm & Lập lịch
- Mức độ ưu tiên: Cao
- Actor: Quản lý ca (Shift Manager)
- Quyền hạn: Role =  MANAGER ,  OWNER

| Hạng mục | Nội dung chi tiết |
| --- | --- |
| Input | • Mã nhân viên được xếp ( user_id ). • Mã ca làm dự kiến ( shift_id ). • Ngày làm việc dự kiến ( work_date : định dạng YYYY-MM-DD). |
| Process | 1. Truy vấn thông tin khung giờ của ca dự kiến từ bảng  shifts  $\rightarrow$ lấy  start_time  và  end_time . 2. Thực hiện truy vấn tìm kiếm các ca làm việc khác của nhân viên này trong cùng ngày  work_date :  SELECT * FROM schedules sc JOIN shifts sh ON sc.shift_id = sh.id WHERE sc.user_id = :user_id AND sc.work_date = :work_date AND sc.status != 'CANCELLED' . 3. So sánh giao thoa thời gian (Time Overlap): Nếu $(\text{new\_start} < \text{existing\_end}) \land (\text{new\_end} > \text{existing\_start})$ $\rightarrow$ Xảy ra xung đột trùng giờ. 4. Nếu trùng: ném biệt lệ lỗi nghiệp vụ  HTTP 409 Conflict  kèm thông báo: "Nhân viên [Tên] đã được xếp vào ca [Tên ca cũ] trùng khung giờ này!". 5. Nếu không trùng: tiếp tục cho phép ghi bản ghi vào bảng  schedules . |
| Output | • Kết quả kiểm tra:  isValid = TRUE  (Cho phép xếp) hoặc  isValid = FALSE  kèm thông điệp cảnh báo xung đột. |
| Luồng dữ liệu | Đọc  shifts ,  schedules . |

Hình 4.3. Quy trình lập lịch phân ca và tự động phát hiện xung đột trùng ca
4.2.4. Module MOD-04-02: Engine thẩm định Geofencing Haversine & Điểm danh
- Mã Module:  MOD-04-02
- Tên Module: Engine thẩm định Geofencing Haversine & Ghi nhận điểm danh
- Thuộc phân hệ: MOD-04 Điểm danh Geofencing & WebSocket
- Mức độ ưu tiên: Cao (Cốt lõi toàn hệ thống)
- Actor: Nhân viên (Employee) kết hợp Máy chủ xử lý (Backend Server)
- Quyền hạn: Role =  EMPLOYEE ,  MANAGER ,  OWNER

| Hạng mục | Nội dung chi tiết |
| --- | --- |
| Input | • Mã lịch ca làm việc ( schedule_id ). • Toạ độ GPS từ Client gửi lên:  client_lat ,  client_lng ,  accuracy . • Địa chỉ IP mạng Client:  client_ip . • Loại thao tác:  CHECK_IN  hoặc  CHECK_OUT . |
| Process | 1. Kiểm tra tính hợp lệ của Token JWT và quyền sở hữu lịch ca của nhân viên. 2. Lấy toạ độ chuẩn của quán từ bảng  shop_locations : $lat_1, lng_1$ và bán kính $R_{fence} = 50\,\text{m}$. 3. Áp dụng công thức lượng giác Haversine tính khoảng cách $d$ trên mặt cầu Trái Đất ($R = 6.371.000\,\text{m}$): $$\Delta\phi = \frac{(lat_2 - lat_1) \cdot \pi}{180},\quad \Delta\lambda = \frac{(lng_2 - lng_1) \cdot \pi}{180}$$ $$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos\left(\frac{lat_1\cdot\pi}{180}\right) \cdot \cos\left(\frac{lat_2\cdot\pi}{180}\right) \cdot \sin^2\left(\frac{\Delta\lambda}{2}\right)$$ $$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right),\quad d = R \cdot c$$ 4. Rẽ nhánh kiểm tra bán kính: • Nếu $d > 50\,\text{m}$: Ghi nhận sự cố vi phạm bán kính vào Audit Log; trả về mã lỗi  HTTP 403 Forbidden  kèm thông điệp: "Bạn đang cách quán [d] mét, vượt quá bán kính cho phép (50m)!". • Nếu $d \le 50\,\text{m}$: Đạt chuẩn toạ độ địa lý. 5. Lấy giờ chuẩn máy chủ NTP ( current_server_time ). So sánh với giờ ca: • Nếu là  CHECK_IN : Nếu trễ quá 5 phút so với  start_time  $\rightarrow$ Đánh dấu trạng thái  LATE ; nếu đúng giờ $\rightarrow$ Đánh dấu  ON_TIME . Ghi vào bảng  attendances . • Nếu là  CHECK_OUT : So sánh với  end_time , tính tổng số phút làm việc thực tế ( total_work_minutes ), cập nhật bản ghi  attendances . 6. Kích hoạt phát sự kiện WebSocket:  io.to('store_room').emit('WS_ATTENDANCE_SUCCESS', data) . |
| Output | • Mã HTTP 200 OK trả về cho điện thoại nhân viên: thông báo "Điểm danh thành công" kèm khoảng cách đo đạc chính xác. • Bản ghi trong bảng  attendances  được tạo mới hoặc cập nhật. • Gói tin WebSocket tức thời gửi tới Dashboard Quản lý ca. |
| Luồng dữ liệu | Đọc  schedules ,  shifts ,  shop_locations ; Ghi / Cập nhật  attendances ; Ghi  audit_logs . |

Minh họa quy trình kỹ thuật phân hệ MOD-04:
Phân hệ điểm danh Geofencing và truyền phát thời gian thực là phân hệ trọng tâm nhất của hệ thống, đòi hỏi sự phối hợp chặt chẽ giữa cảm biến phần cứng thiết bị di động, thuật toán tính toán tại máy chủ và giao thức truyền thông hai chiều. Các sơ đồ kỹ thuật dưới đây mô tả chi tiết quy trình thực thi:
Hình 4.4. Quy trình thẩm định vị trí Geofencing bằng thuật toán Haversine
Hình 4.5. Quy trình truyền dữ liệu thời gian thực qua giao thức WebSocket
Sơ đồ tuần tự (Sequence Diagram) – Chấm công GPS Geofencing & Phát WebSocket Live
Sơ đồ tuần tự chuẩn UML dưới đây mô tả chi tiết trục thời gian tương tác giữa 7 đối tượng/thực thể trong kịch bản nhân viên thực hiện bấm Check-in:
- 7 Đường đời (Lifelines):
1.  Nhân viên (Web Client) : Giao diện người dùng trên điện thoại di động.
2.  HTML5 Geolocation : Bộ API trình duyệt giao tiếp với chip định vị vệ tinh GPS.
3.  Web Server (API Gateway) : Máy chủ ứng dụng xử lý định tuyến và xác thực JWT.
4.  Haversine Geofencing Engine : Bộ máy thuật toán tính khoảng cách hình cầu.
5.  MySQL Database : Hệ quản trị CSDL lưu trữ toạ độ và bản ghi điểm danh.
6.  WebSocket Gateway (Socket.IO) : Máy chủ truyền phát sự kiện hai chiều qua TCP.
7.  Quản lý ca (Live Monitor) : Giao diện Dashboard giám sát thời gian thực của Quản lý.
- Nguyên lý hoạt động và Phân tích tương tác:
1. *Kích hoạt định vị:* Nhân viên nhấn nút "Check-in" trên màn hình điện thoại $\rightarrow$ Web Client gọi phương thức  getCurrentPosition()  của HTML5 Geolocation API.
2. *Thu nhận toạ độ:* Thiết bị di động kích hoạt chip thu tín hiệu vệ tinh GPS, giải mã và trả về cặp toạ độ kinh - vĩ độ $(lat, lng)$ kèm sai số  accuracy  cho Web Client.
3. *Gửi yêu cầu điểm danh:* Web Client đóng gói toạ độ và gửi yêu cầu  POST /api/attendance/check-in  kèm mã xác thực  Bearer Token (JWT)  qua kênh truyền bảo mật HTTPS tới Web Server API Gateway.
4. *Xác thực và chuyển tiếp:* Web Server xác thực tính hợp lệ của Token JWT (kiểm tra hạn dùng và chữ ký số), sau đó chuyển toạ độ nhân viên sang  Haversine Geofencing Engine .
5. *Truy vấn toạ độ chuẩn của quán:* Haversine Engine truy vấn bản ghi bảng  shop_locations  từ MySQL Database để lấy toạ độ tâm quán ($lat_0, lng_0$) và bán kính cho phép ($R_{fence} = 50\,\text{m}$).
6. *Tính toán khoảng cách mặt cầu:* Haversine Engine áp dụng công thức lượng giác hình cầu, tính ra khoảng cách thực tế $d$ giữa nhân viên và quán.
7. *Rẽ nhánh điều kiện kết hợp (alt Combined Fragment):*
- Trường hợp Hợp lệ [$d \le 50\,\text{m}$]:
- Haversine Engine trả về kết quả  VALID  cho Web Server.
- Web Server ghi bản ghi điểm danh mới vào bảng  attendances  trong MySQL CSDL với trạng thái  ON_TIME  hoặc  LATE  (tuỳ thuộc giờ thực tế so với giờ ca). CSDL trả về xác nhận  INSERT SUCCESS .
- Web Server đẩy thông điệp sự kiện tới  WebSocket Gateway :  broadcast('WS_ATTENDANCE_SUCCESS', payload) .
- WebSocket Gateway lập tức đẩy gói tin TCP tức thời xuống Dashboard của  Quản lý ca . Trình duyệt của Quản lý tự động đổi màu trạng thái nhân viên sang xanh lá cây kèm hiệu ứng rung/chuông báo (Zero-reload).
- Web Server trả về phản hồi  HTTP 200 OK  ("Chấm công thành công! Khoảng cách: d mét") cho Web Client của Nhân viên.
- Trường hợp Vượt bán kính [$d > 50\,\text{m}$]:
- Haversine Engine trả về kết quả  OUT_OF_BOUNDS (d > 50m) .
- Web Server ghi cảnh báo vi phạm toạ độ vào bảng  audit_logs  trong CSDL.
- Web Server từ chối yêu cầu và trả về phản hồi  HTTP 403 Forbidden  ("Từ chối: Bạn đang cách quán d mét, vượt quá bán kính 50m") về điện thoại Nhân viên. Không có sự kiện WebSocket nào được phát.
Hình 4.6. Sơ đồ tuần tự (Sequence Diagram) Chấm công GPS Geofencing & Phát WebSocket Live
4.2.5. Module MOD-05-04: Khóa sổ chấm công kỳ tháng & Xuất file Excel
- Mã Module:  MOD-05-04
- Tên Module: Khóa sổ chấm công kỳ tháng & Kết xuất báo cáo Excel
- Thuộc phân hệ: MOD-05 Giải trình & Khóa sổ công Excel
- Mức độ ưu tiên: Cao
- Actor: Chủ quán (Shop Owner), Quản lý ca (Shift Manager)
- Quyền hạn: Role =  OWNER ,  MANAGER

| Hạng mục | Nội dung chi tiết |
| --- | --- |
| Input | • Kỳ chấm công cần kết xuất (Tháng, Năm; ví dụ: Tháng 11/2026). • Lệnh xác nhận khóa sổ:  is_lock_action = TRUE . |
| Process | 1. Hệ thống thực hiện quét toàn bộ các bản ghi trong bảng  attendances  thuộc tháng đã chọn. 2. Kiểm tra xem còn đơn giải trình nào đang ở trạng thái chờ duyệt ( PENDING ) hay không: nếu còn $\rightarrow$ Cảnh báo quản lý phải xử lý hết đơn tồn đọng trước khi khóa sổ. 3. Khởi tạo một giao dịch CSDL (Transaction):  UPDATE attendances SET is_locked = TRUE WHERE strftime('%Y-%m', check_in_time) = :month_year . 4. Tổng hợp dữ liệu giờ công của từng nhân viên: Tổng số ca làm, Tổng số phút làm việc, Số lần đi trễ, Số lần về sớm, Số lần vắng mặt. 5. Sử dụng thư viện kết xuất file Excel (SheetJS / ExcelJS): Định dạng tiêu đề cột, căn lề, viền khung, gán dữ liệu và tự động tính dòng tổng cộng. 6. Ghi Audit Log hành động  LOCK_ATTENDANCE_MONTH . Commit giao dịch. |
| Output | • Toàn bộ bản ghi của tháng được đóng băng vĩnh viễn ( is_locked = 1 ). • Tệp tin báo cáo định dạng chuẩn Microsoft Excel ( Bao_Cao_Cham_Cong_HawasFood_Thang_11_2026.xlsx ) được tải về máy tính quản lý. |
| Luồng dữ liệu | Cập nhật  attendances ; Đọc  users ,  schedules ,  shifts ; Ghi  audit_logs . |

Hình 4.7. Quy trình tiếp nhận, đối soát và phê duyệt đơn giải trình điểm danh
Hình 4.8. Quy trình đóng băng dữ liệu (is_locked) và kết xuất bảng công Excel
5. LUỒNG DỮ LIỆU LIÊN QUAN ĐẾN ĐỐI TƯỢNG VÀ CHỨC NĂNG
5.1. Ma trận đối tượng và chức năng CRUD
Bảng 5.1. Ma trận CRUD giữa 5 Thực thể dữ liệu cốt lõi và 5 Phân hệ chức năng
*Ghi chú ký hiệu: C (Create - Tạo mới), R (Read - Đọc), U (Update - Cập nhật), D (Delete - Xóa).*

| Thực thể dữ liệu cốt lõi (Entities) | MOD-01: Quản trị & Bảo mật | MOD-02: Cấu hình Quán & Geofence | MOD-03: Lập lịch phân ca | MOD-04: Điểm danh & WebSocket | MOD-05: Giải trình & Khóa Excel |
| --- | --- | --- | --- | --- | --- |
| ENT-01: Người dùng (`users`) | C, R, U, D | R | R | R | R |
| ENT-02: Vị trí quán & Mạng (`shop_locations`) | R | C, R, U | R | R | R |
| ENT-03: Ca làm việc (`shifts`) | - | C, R, U, D | R | R | R |
| ENT-04: Lịch phân ca (`schedules`) | - | - | C, R, U, D | R, U | R |
| ENT-05: Bản ghi chấm công (`attendances`) | - | - | - | C, R, U | R, U *(Khóa sổ)* |

*Ghi chú:* Các bảng phụ trợ vật lý như  shop_wifis  đi kèm với  ENT-02 ,  attendance_requests  đi kèm với  ENT-05 , và  audit_logs  được ghi tự động (C) xuyên suốt cả 5 phân hệ để lưu vết an toàn thông tin.
5.2. Mô tả luồng dữ liệu chính (Data Flows)
Bảng 5.2. Danh sách 6 luồng dữ liệu chính (DF-01 đến DF-06)

| Mã luồng | Tên luồng dữ liệu | Nguồn phát | Điểm tiếp nhận | Dữ liệu trao đổi chi tiết | Điều kiện & Giao thức thực thi |
| --- | --- | --- | --- | --- | --- |
| DF-01 | Xác thực phiên làm việc | Người dùng (Client) | Module MOD-01 (Server) | Gửi:  username, password . Nhận:  accessToken  (JWT), thông tin vai trò. | HTTPS POST, mã hóa TLS 1.3, mật khẩu băm bcrypt. |
| DF-02 | Cấu hình toạ độ Geofencing | Chủ quán (Client) | Module MOD-02 $\rightarrow$ Kho  shop_locations | Toạ độ $(lat, lng)$, bán kính 50m, địa chỉ quán, dải IP Wi-Fi nội bộ. | HTTPS PUT, yêu cầu Role =  OWNER . |
| DF-03 | Ban hành lịch phân ca | Quản lý ca | Module MOD-03 $\rightarrow$ Kho  schedules | Danh sách gán  user_id, shift_id, work_date . | HTTPS POST, validate không trùng ca. |
| DF-04 | Yêu cầu chấm công Geofencing | Điện thoại Nhân viên | Module MOD-04 Engine Haversine | Toạ độ GPS Client $(lat, lng, accuracy)$,  schedule_id , Timestamp. | HTTPS POST kèm Bearer JWT Token. |
| DF-05 | Đẩy sự kiện Live WebSocket | Module MOD-04 (Server) | Dashboard Quản lý (Client) | Gói tin JSON:  { event: 'ATTENDANCE_UPDATE', userId, shiftId, status, time } . | Giao thức WebSocket (RFC 6455) Full-duplex TCP qua cổng bảo mật WSS. |
| DF-06 | Xử lý giải trình & Khóa sổ | Quản lý ca / Kế toán | Module MOD-05 $\rightarrow$ Kho  attendances | Quyết định duyệt đơn, cập nhật cờ  is_locked = TRUE , tệp tin  .xlsx . | HTTPS POST, giao dịch ACID, ghi Audit Log đầy đủ. |

Hình 5.1. Sơ đồ luồng dữ liệu DFD Mức 0 (Context) và DFD Mức 1 phân rã tiến trình
5.3. Minh họa liên kết xuyên suốt (End-to-End Scenario)
Để chứng minh tính nhất quán và khép kín của hệ thống, kịch bản nghiệp vụ của nhân viên phục vụ Vũ Huy Hoàng trong một ngày làm việc tiêu chuẩn diễn ra như sau:
1. 06:45 (Trước ca 15 phút): Hoàng đến quán Hawa's Food, mở trình duyệt trên điện thoại cá nhân và truy cập trang Web Chấm công. Điện thoại tự động gửi Token JWT lưu trong LocalStorage để đăng nhập hệ thống (DF-01).
2. 06:46: Hoàng nhấn nút lớn "BẤM VÀO CA". Trình duyệt kích hoạt cảm biến GPS trích xuất toạ độ: $lat = 16.054410, lng = 108.219800$ kèm bán kính sai số $8\,\text{m}$. Gói tin HTTPS POST được gửi lên Server trung tâm (DF-04).
3. 06:46:00.200 (Server xử lý):
- Server đọc toạ độ gốc của quán ($lat_0 = 16.054407, lng_0 = 108.219803$) và chạy công thức Haversine: Khoảng cách tính ra là $0.45\,\text{m} \le 50\,\text{m}$ $\rightarrow$ Hợp lệ.
- Server lấy giờ hiện tại (06:46) so sánh với giờ bắt đầu ca sáng (07:00): Nằm trong khung cho phép sớm 30 phút $\rightarrow$ Ghi bản ghi vào bảng  attendances  với trạng thái  ON_TIME .
- Server phát sự kiện WebSocket:  WS_ATTENDANCE_SUCCESS  chứa mã nhân viên và trạng thái (DF-05).
4. 06:46:00.250 (Màn hình Quản lý ca): Quản lý ca Trần Đức Trí đang mở Dashboard trên máy tính tại quầy thu ngân. Màn hình tự động cập nhật tên Hoàng từ trạng thái "Chưa đến" sang "Đang làm việc" màu xanh lá cây rực rỡ, kèm âm thanh thông báo nhẹ mà không cần bấm F5 tải lại trang.
5. 12:02 (Hết ca sáng): Hoàng nhấn nút "BẤM RA CA". Server thẩm định toạ độ $d \le 50\,\text{m}$, tính tổng thời gian làm việc là 316 phút, cập nhật trường  check_out_time .
6. Cuối tháng (Khóa sổ): Chủ quán Nguyễn Văn Nguyên thực hiện thao tác kiểm tra toàn bộ dữ liệu, xác nhận không còn đơn giải trình tồn đọng và nhấn "Khóa sổ kỳ công". Toàn bộ dữ liệu của Hoàng được gán cờ  is_locked = TRUE , sẵn sàng cho việc xuất file Excel đối soát tính công chính xác 100% (DF-06).
5.4. Sơ đồ máy trạng thái (State Machine Diagram) – Vòng đời ca làm việc & Bản ghi chấm công
Để kiểm soát chặt chẽ trạng thái của từng ca làm việc và dữ liệu điểm danh, ngăn chặn tối đa các sai sót logic và hành vi gian lận giờ công, hệ thống áp dụng mô hình Máy trạng thái hữu hạn (UML State Machine Diagram) quản lý toàn bộ vòng đời của một ca làm việc từ khi lập lịch đến khi khóa sổ vĩnh viễn:
Hình 5.2. Sơ đồ máy trạng thái (State Machine Diagram) Vòng đời ca làm việc và bản ghi chấm công
Phân tích chi tiết các trạng thái và điều kiện chuyển dịch (State Transitions):
1. Trạng thái Khởi tạo (● Initial State): Ca làm việc được tạo lập thông qua chức năng lập lịch phân ca của Quản lý ca ( MOD-03-01 ).
2. Trạng thái `SCHEDULED` (Đã xếp lịch):
- Ca làm việc đã được phân bổ cho nhân viên cụ thể vào ngày công xác định. Hệ thống hiển thị lịch trên điện thoại của nhân viên nhưng chưa mở quyền bấm Check-in (cho đến trước giờ bắt đầu 30 phút).
3. Trạng thái `CHECKED_IN` (Đang trong ca làm việc):
- Kích hoạt khi nhân viên bấm "Check-in" thỏa mãn điều kiện Geofencing ($d \le 50\,\text{m}$).
- Trạng thái con `ON_TIME` (Đúng giờ): Nếu thời điểm bấm công $t_{checkin} \le t_{start} + 5\,\text{phút}$.
- Trạng thái con `LATE` (Đi trễ): Nếu thời điểm bấm công $t_{checkin} > t_{start} + 5\,\text{phút}$. Hệ thống tự động ghi nhận số phút đi trễ để làm căn cứ tính trừ điểm chuyên cần.
4. Trạng thái `COMPLETED` (Hoàn thành ca làm việc):
- Kích hoạt khi nhân viên bấm "Check-out" thành công tại quán ($d \le 50\,\text{m}$).
- Trạng thái con `NORMAL` (Đủ giờ): Nếu $t_{checkout} \ge t_{end}$.
- Trạng thái con `EARLY_LEAVE` (Về sớm): Nếu $t_{checkout} < t_{end}$. Hệ thống ghi nhận số phút về sớm.
- Tại trạng thái này, hệ thống tự động tổng hợp tổng số phút làm việc thực tế ( total_work_minutes ).
5. Các trạng thái Bất thường & Quy trình Giải trình:
- Trạng thái `ABSENT` (Vắng mặt không phép): Nếu quá giờ kết thúc ca làm việc ($t > t_{end}$) mà bản ghi không có thao tác Check-in, CronJob tự động quét và chuyển trạng thái ca sang  ABSENT .
- Trạng thái `MISSING_CHECKOUT` (Quên bấm ra ca): Nếu nhân viên đã Check-in nhưng sau khi ca kết thúc quá 2 giờ vẫn không có dữ liệu Check-out, hệ thống tự động đóng ca với trạng thái quên Check-out để nhắc nhở.
- Trạng thái `PENDING_REVIEW` (Chờ thẩm định đơn giải trình): Nhân viên tạo đơn giải trình sai lệch ( MOD-05-01 ), tải ảnh minh chứng (tin nhắn điều động, hình ảnh camera) và gửi lên hệ thống.
- Trạng thái `REJECTED` (Từ chối giải trình): Quản lý ca thẩm định không hợp lệ $\rightarrow$ Trạng thái ca quay trở về mức phạt  ABSENT  hoặc trừ toàn bộ giờ làm của ca.
- Trạng thái `RESOLVED` (Đã xử lý & Bổ sung công): Quản lý ca chấp thuận đơn giải trình $\rightarrow$ Cập nhật bổ sung giờ Check-in/Check-out hợp lệ và ghi rõ lý do người duyệt vào  audit_logs .
6. Trạng thái Đóng băng dữ liệu `LOCKED` (Đã khóa sổ kỳ công):
- Khi hết chu kỳ tính công (cuối tháng), Chủ quán thực hiện đối soát và bấm "Khóa sổ kỳ công" ( MOD-05-04 ).
- Trigger CSDL hoặc Transaction cập nhật cờ  is_locked = TRUE  cho toàn bộ các bản ghi trong tháng.
- Đặc tính an toàn: Khi đã ở trạng thái  LOCKED , toàn bộ các hành vi sửa đổi dữ liệu (Update, Delete) hoặc nộp đơn giải trình bổ sung đều bị từ chối triệt để. Dữ liệu đạt tính toàn vẹn tuyệt đối phục vụ xuất file Excel tính lương.
7. Trạng thái Kết thúc (◉ Final State): Kết xuất báo cáo bảng công hoàn chỉnh, lưu trữ vĩnh viễn phục vụ thanh tra tài chính và kết thúc vòng đời của bản ghi.
5.5. Sơ đồ quy trình nghiệp vụ tổng thể khép kín (Workflow)
Sơ đồ quy trình nghiệp vụ dưới đây liên kết toàn bộ 5 phân hệ thành một chu trình vận hành khép kín và nhất quán:
Hình 5.3. Sơ đồ quy trình nghiệp vụ tổng thể khép kín toàn hệ thống (Workflow)
Quy trình bao gồm 5 giai đoạn xuyên suốt:
1. Giai đoạn 1 (Thiết lập nền tảng): Admin cấp tài khoản, Chủ quán ghim toạ độ Geofencing ($R = 50\,\text{m}$) và dải IP Wi-Fi nội bộ.
2. Giai đoạn 2 (Xếp ca tuần): Quản lý lập lịch phân ca, hệ thống kiểm tra chống trùng ca và công bố lịch xuống điện thoại nhân viên.
3. Giai đoạn 3 (Vận hành chấm công): Nhân viên đến quán bấm công, máy chủ chạy Haversine thẩm định toạ độ, phân loại  ON_TIME  /  LATE  và bắn WebSocket Live.
4. Giai đoạn 4 (Giám sát & Giải trình): Quản lý theo dõi màn hình thời gian thực, tự động phát hiện ca bất thường và phê duyệt đơn giải trình.
5. Giai đoạn 5 (Khóa sổ & Xuất báo cáo): Chủ quán khóa sổ bảo vệ toàn vẹn dữ liệu ( is_locked = TRUE ), kết xuất file Excel bảng công chuẩn gửi kế toán tính lương.
6. THIẾT KẾ CƠ SỞ DỮ LIỆU
6.1. Danh sách bảng
Cơ sở dữ liệu được thiết kế tối ưu hóa theo dạng chuẩn 3 (3NF), gồm đúng 8 bảng logic:
1.  users : Bảng lưu trữ hồ sơ và tài khoản người dùng toàn hệ thống.
2.  shop_locations : Bảng lưu toạ độ địa lý và bán kính hàng rào Geofencing của cửa hàng.
3.  shop_wifis : Bảng lưu dải địa chỉ IP và BSSID mạng Wi-Fi nội bộ để đối soát kép.
4.  shifts : Bảng định nghĩa danh mục các ca làm việc chuẩn trong ngày.
5.  schedules : Bảng lưu kế hoạch phân bổ nhân viên vào ca theo ngày.
6.  attendances : Bảng lưu trữ kết quả chấm công thực tế của nhân viên.
7.  attendance_requests : Bảng lưu trữ đơn giải trình khi có sự cố quên bấm công hoặc lỗi kỹ thuật.
8.  audit_logs : Bảng lưu vết toàn bộ lịch sử chỉnh sửa dữ liệu để bảo đảm an toàn thông tin.
6.2. Chi tiết thuộc tính từng bảng
6.2.1. Bảng  users  (Hồ sơ người dùng & Phân quyền)

| Tên cột | Kiểu dữ liệu | Null | Default | Mô tả chi tiết | Ràng buộc kỹ thuật |
| --- | --- | --- | --- | --- | --- |
| id | INTEGER / BIGINT | NO | Auto | Khóa chính định danh người dùng duy nhất | PRIMARY KEY, AUTOINCREMENT |
| username | VARCHAR(50) | NO | - | Tên đăng nhập hệ thống (không dấu) | UNIQUE, INDEX |
| password_hash | VARCHAR(255) | NO | - | Mật khẩu đã được mã hóa một chiều | Chuỗi băm bcrypt (Salt Rounds = 10) |
| full_name | VARCHAR(100) | NO | - | Họ và tên đầy đủ của nhân viên | - |
| phone_number | VARCHAR(15) | YES | NULL | Số điện thoại liên lạc | UNIQUE |
| role | VARCHAR(20) | NO | 'EMPLOYEE' | Vai trò phân quyền trong hệ thống | CHECK ( role  IN ('ADMIN', 'OWNER', 'MANAGER', 'EMPLOYEE')) |
| is_active | BOOLEAN | NO | TRUE | Trạng thái tài khoản đang hoạt động hay bị khóa | - |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | Thời điểm tạo tài khoản | - |

6.2.2. Bảng  shop_locations  (Toạ độ Geofencing quán)

| Tên cột | Kiểu dữ liệu | Null | Default | Mô tả chi tiết | Ràng buộc kỹ thuật |
| --- | --- | --- | --- | --- | --- |
| id | INTEGER | NO | Auto | Khóa chính địa điểm quán | PRIMARY KEY, AUTOINCREMENT |
| name | VARCHAR(100) | NO | - | Tên cửa hàng (Hawa's Food Đà Nẵng) | - |
| latitude | DECIMAL(10, 8) | NO | - | Toạ độ vĩ độ tâm quán | CHECK ( latitude  BETWEEN -90 AND 90) |
| longitude | DECIMAL(11, 8) | NO | - | Toạ độ kinh độ tâm quán | CHECK ( longitude  BETWEEN -180 AND 180) |
| radius_meters | INTEGER | NO | 50 | Bán kính hàng rào địa lý ảo cho phép | CHECK ( radius_meters  BETWEEN 10 AND 500) |
| address | VARCHAR(255) | NO | - | Địa chỉ đường phố cụ thể của quán | - |

6.2.3. Bảng  shop_wifis  (Danh sách IP / Wi-Fi quán)

| Tên cột | Kiểu dữ liệu | Null | Default | Mô tả chi tiết | Ràng buộc kỹ thuật |
| --- | --- | --- | --- | --- | --- |
| id | INTEGER | NO | Auto | Khóa chính danh mục mạng Wi-Fi | PRIMARY KEY, AUTOINCREMENT |
| location_id | INTEGER | NO | - | Mã địa điểm quán sở hữu | FOREIGN KEY REFERENCES  shop_locations ( id ) |
| wifi_ssid | VARCHAR(100) | NO | - | Tên mạng Wi-Fi phát tại quán | - |
| ip_address | VARCHAR(45) | YES | NULL | Địa chỉ IP Public của quán | Định dạng chuẩn IPv4 hoặc IPv6 |
| bssid | VARCHAR(50) | YES | NULL | Địa chỉ MAC Address của Router Wi-Fi | - |

6.2.4. Bảng  shifts  (Danh mục ca làm việc)

| Tên cột | Kiểu dữ liệu | Null | Default | Mô tả chi tiết | Ràng buộc kỹ thuật |
| --- | --- | --- | --- | --- | --- |
| id | INTEGER | NO | Auto | Khóa chính ca làm việc | PRIMARY KEY, AUTOINCREMENT |
| location_id | INTEGER | NO | - | Thuộc cơ sở quán nào | FOREIGN KEY REFERENCES  shop_locations ( id ) |
| shift_code | VARCHAR(20) | NO | - | Mã viết tắt (CA_SANG, CA_CHIEU, CA_TOI) | UNIQUE theo từng cơ sở |
| shift_name | VARCHAR(50) | NO | - | Tên hiển thị của ca làm việc | - |
| start_time | TIME | NO | - | Giờ bắt đầu ca chuẩn (ví dụ 07:00:00) | - |
| end_time | TIME | NO | - | Giờ kết thúc ca chuẩn (ví dụ 12:00:00) | - |

6.2.5. Bảng  schedules  (Lịch phân ca làm việc)

| Tên cột | Kiểu dữ liệu | Null | Default | Mô tả chi tiết | Ràng buộc kỹ thuật |
| --- | --- | --- | --- | --- | --- |
| id | INTEGER | NO | Auto | Khóa chính của lịch ca | PRIMARY KEY, AUTOINCREMENT |
| user_id | INTEGER | NO | - | Mã nhân viên được giao ca | FOREIGN KEY REFERENCES  users ( id ) |
| shift_id | INTEGER | NO | - | Mã ca làm việc được giao | FOREIGN KEY REFERENCES  shifts ( id ) |
| work_date | DATE | NO | - | Ngày làm việc cụ thể (YYYY-MM-DD) | - |
| status | VARCHAR(20) | NO | 'DRAFT' | Trạng thái lịch ca | CHECK ( status  IN ('DRAFT', 'PUBLISHED', 'CANCELLED')) |
| assigned_by | INTEGER | YES | NULL | Quản lý thực hiện việc xếp ca | FOREIGN KEY REFERENCES  users ( id ) |

6.2.6. Bảng  attendances  (Kết quả chấm công)

| Tên cột | Kiểu dữ liệu | Null | Default | Mô tả chi tiết | Ràng buộc kỹ thuật |
| --- | --- | --- | --- | --- | --- |
| id | INTEGER | NO | Auto | Khóa chính bản ghi chấm công | PRIMARY KEY, AUTOINCREMENT |
| schedule_id | INTEGER | NO | - | Thuộc lịch phân ca nào | UNIQUE, FOREIGN KEY REFERENCES  schedules ( id ) |
| user_id | INTEGER | NO | - | Mã nhân viên thực hiện điểm danh | FOREIGN KEY REFERENCES  users ( id ), INDEX |
| check_in_time | TIMESTAMP | YES | NULL | Thời điểm bấm vào ca thực tế | Giờ chuẩn máy chủ NTP |
| check_in_distance | DECIMAL(8,2) | YES | NULL | Khoảng cách đo đạc tới quán khi vào ca | Đơn vị mét ($m$) |
| check_out_time | TIMESTAMP | YES | NULL | Thời điểm bấm ra ca thực tế | Giờ chuẩn máy chủ NTP |
| check_out_distance | DECIMAL(8,2) | YES | NULL | Khoảng cách đo đạc tới quán khi ra ca | Đơn vị mét ($m$) |
| total_work_minutes | INTEGER | NO | 0 | Tổng số phút làm việc thực tế | Tự động tính khi có đủ vào và ra |
| status | VARCHAR(20) | NO | 'ABSENT' | Trạng thái điểm danh | CHECK ( status  IN ('ON_TIME', 'LATE', 'EARLY_LEAVE', 'MISSING_OUT', 'ABSENT')) |
| is_locked | BOOLEAN | NO | FALSE | Cờ khóa dữ liệu chống chỉnh sửa | TRUE sau khi chủ quán khóa sổ |

6.2.7. Bảng  attendance_requests  (Đơn giải trình điểm danh)

| Tên cột | Kiểu dữ liệu | Null | Default | Mô tả chi tiết | Ràng buộc kỹ thuật |
| --- | --- | --- | --- | --- | --- |
| id | INTEGER | NO | Auto | Khóa chính đơn giải trình | PRIMARY KEY, AUTOINCREMENT |
| attendance_id | INTEGER | NO | - | Bản ghi chấm công cần giải trình | FOREIGN KEY REFERENCES  attendances ( id ) |
| user_id | INTEGER | NO | - | Nhân viên nộp đơn | FOREIGN KEY REFERENCES  users ( id ) |
| request_type | VARCHAR(20) | NO | - | Loại giải trình | CHECK ( request_type  IN ('FORGOT_CHECK_IN', 'FORGOT_CHECK_OUT', 'GPS_ERROR', 'DEVICE_ISSUE')) |
| requested_time | TIMESTAMP | NO | - | Mốc thời gian đề xuất bổ sung | - |
| reason | TEXT | NO | - | Lý do cụ thể của nhân viên | - |
| proof_image | VARCHAR(255) | YES | NULL | Đường dẫn file ảnh chụp minh chứng | - |
| status | VARCHAR(20) | NO | 'PENDING' | Trạng thái phê duyệt của đơn | CHECK ( status  IN ('PENDING', 'APPROVED', 'REJECTED')) |
| reviewed_by | INTEGER | YES | NULL | Người duyệt đơn (Quản lý/Chủ quán) | FOREIGN KEY REFERENCES  users ( id ) |

6.2.8. Bảng  audit_logs  (Nhật ký giám sát an ninh mạng)

| Tên cột | Kiểu dữ liệu | Null | Default | Mô tả chi tiết | Ràng buộc kỹ thuật |
| --- | --- | --- | --- | --- | --- |
| id | INTEGER | NO | Auto | Khóa chính nhật ký hệ thống | PRIMARY KEY, AUTOINCREMENT |
| user_id | INTEGER | YES | NULL | Mã tài khoản thực hiện thao tác | FOREIGN KEY REFERENCES  users ( id ) |
| action | VARCHAR(50) | NO | - | Tên hành động nghiệp vụ | LOGIN, LOGOUT, CHECK_IN, APPROVE_REQUEST, LOCK_ATTENDANCE,... |
| table_name | VARCHAR(50) | NO | - | Tên bảng dữ liệu bị tác động | - |
| record_id | INTEGER | YES | NULL | Mã bản ghi bị thay đổi | - |
| old_value | TEXT | YES | NULL | Dữ liệu cũ trước khi sửa (JSON) | Phục vụ đối soát, khôi phục |
| new_value | TEXT | YES | NULL | Dữ liệu mới sau khi sửa (JSON) | Phục vụ truy vết gian lận |
| ip_address | VARCHAR(45) | NO | - | Địa chỉ IP mạng nguồn của Client | Ghi nhận chống chối bỏ trách nhiệm |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | Thời điểm phát sinh sự kiện | - |

6.3. Sơ đồ quan hệ ERD
6.3.1. Phân loại cấu trúc Gốc – Cành – Lá và quan hệ tiêu biểu
Mô hình cơ sở dữ liệu của hệ thống được phân cấp rành mạch thành 3 tầng cấu trúc:
- Tầng Gốc (Root Entities): Gồm  users ,  shop_locations ,  shifts . Đây là các thực thể độc lập cao nhất, không chứa khóa ngoại phụ thuộc vào các bảng nghiệp vụ khác. Được khởi tạo đầu tiên khi thiết lập hệ thống.
- Tầng Cành (Branch Entities): Gồm  schedules  và  shop_wifis . Đóng vai trò cầu nối quan hệ nhiều - nhiều ($N:M$) giữa con người với ca kíp hoặc giữa địa điểm với hạ tầng mạng.
- Tầng Lá (Leaf Entities): Gồm  attendances ,  attendance_requests  và  audit_logs . Đây là các thực thể ghi nhận kết quả vận hành nghiệp vụ hàng ngày. Bảng  attendances  là “trái ngọt” trung tâm lưu trữ toàn bộ dữ liệu điểm danh, gắn kết mật thiết với lịch ca và đơn giải trình.
Hình 6.1. Sơ đồ quan hệ thực thể (ERD) cơ sở dữ liệu vật lý 8 bảng chuẩn 3NF
erDiagram
users ||--o{ schedules : "được xếp ca"
users ||--o{ attendances : "chấm công"
users ||--o{ attendance_requests : "nộp đơn"
users ||--o{ audit_logs : "thực hiện"
shop_locations ||--o{ shop_wifis : "sở hữu mạng"
shop_locations ||--o{ shifts : "áp dụng ca"
shifts ||--o{ schedules : "thuộc khung giờ"
schedules ||--|| attendances : "ghi nhận kết quả"
attendances ||--o{ attendance_requests : "được giải trình"
users {
int id PK
string username UQ
string password_hash
string full_name
string role
boolean is_active
}
shop_locations {
int id PK
string name
decimal latitude
decimal longitude
int radius_meters
}
shop_wifis {
int id PK
int location_id FK
string wifi_ssid
string ip_address
}
shifts {
int id PK
int location_id FK
string shift_code
time start_time
time end_time
}
schedules {
int id PK
int user_id FK
int shift_id FK
date work_date
string status
}
attendances {
int id PK
int schedule_id FK,UQ
int user_id FK
timestamp check_in_time
decimal check_in_distance
timestamp check_out_time
string status
boolean is_locked
}
attendance_requests {
int id PK
int attendance_id FK
int user_id FK
string request_type
timestamp requested_time
string status
}
audit_logs {
int id PK
int user_id FK
string action
string table_name
text old_value
text new_value
string ip_address
}
6.3.2. Toàn vẹn tham chiếu và cơ chế giao dịch ACID
- Bảo toàn giao dịch điểm danh: Thao tác Check-in / Check-out được bao bọc trong một Database Transaction với mức độ cô lập dữ liệu (Isolation Level) phù hợp. Khi nhân viên thực hiện bấm công, hệ thống khóa dòng tương ứng trong bảng  schedules  và  attendances  ( SELECT ... FOR UPDATE ), kiểm tra tính hợp lệ và ghi đồng thời bản ghi điểm danh cùng Audit Log. Nếu có bất kỳ lỗi mạng hoặc vi phạm ràng buộc CHECK, toàn bộ giao dịch sẽ lập tức Rollback, đảm bảo không bao giờ sinh ra dữ liệu rác hay tình trạng nửa vời.
- Ràng buộc duy nhất (Unique Constraint): Cặp giá trị  (user_id, shift_id, work_date)  trên bảng  schedules  được gắn chỉ mục duy nhất (Unique Composite Index), ngăn chặn hoàn toàn khả năng người dùng hoặc hệ thống vô tình xếp một nhân viên trùng ca trong cùng một ngày.
- Bảo vệ chống chỉnh sửa bằng cờ `is_locked`: Mọi câu lệnh  UPDATE  hoặc  DELETE  trên bảng  attendances  đều phải qua lớp kiểm tra điều kiện  WHERE is_locked = FALSE . Một khi chủ quán đã thực hiện khóa sổ kỳ công, cơ sở dữ liệu sẽ từ chối mọi tác động sửa đổi giờ làm.
7. CHIA & QUẢN LÝ CÔNG VIỆC THEO NHÓM
7.1. Phân công vai trò trong nhóm
Bảng 7.1. Phân công vai trò trong nhóm

| STT | Vai trò | Trách nhiệm chính | Người phụ trách |
| --- | --- | --- | --- |
| 1 | Trưởng nhóm | Điều phối toàn bộ, phân công, kiểm soát tiến độ, giao tiếp với khách hàng/PO, quản lý kiến trúc Client - Server & bảo mật JWT. | Ngô Đức An |
| 2 | Phân tích nghiệp vụ | Thu thập & làm rõ yêu cầu, viết đặc tả SRS (FR, NFR, BR), kiểm soát phạm vi nghiệp vụ và quy chế Geofencing. | Nguyễn Văn Nguyên |
| 3 | Thiết kế hệ thống | Phân tích đối tượng, thiết kế phân hệ, thiết kế CSDL 8 bảng, vẽ sơ đồ quan hệ ERD và cấu hình mạng WebSocket. | Trần Đức Trí |
| 4 | Phân tích chức năng | Phân rã chức năng đến module IPO, lập ma trận CRUD, mô tả luồng dữ liệu DFD và quy trình đối soát giải trình. | Nguyễn Ngọc Thương |
| 5 | Kiểm thử & Đảm bảo chất lượng (QA/QC) | Thiết kế bộ 16 ca kiểm thử (Test Cases), kiểm thử giao diện Web Mobile, đo đạc sai số toạ độ GPS và bắt gói tin mạng. | Vũ Huy Hoàng |

7.2. Cách thức chia công việc theo giai đoạn
Bảng 7.2. Kế hoạch chia công việc theo giai đoạn

| Giai đoạn | Công việc chính | Người phụ trách chính | Người hỗ trợ | Thời gian ước lượng |
| --- | --- | --- | --- | --- |
| 1. Đặt tên & Xác định bài toán | Viết mục 1: Đặt tên đề tài 3 thành phần, bối cảnh quán Hawa's Food, mục tiêu, phạm vi và bảng so sánh 4 phần mềm liên quan. | Ngô Đức An | Nguyễn Văn Nguyên | 2 ngày |
| 2. Đặc tả yêu cầu (SRS) | Viết mục 2: Bảng yêu cầu chức năng FR-01 đến FR-20, yêu cầu phi chức năng NFR-01 đến NFR-08 và 7 quy tắc nghiệp vụ BR. | Nguyễn Văn Nguyên | Cả nhóm | 3 ngày |
| 3. Phân tích đối tượng & Phân hệ | Viết mục 3: Lập danh sách 5 thực thể dữ liệu cốt lõi (ENT-01 đến ENT-05), 5 phân hệ (MOD-01 đến MOD-05) và bảng 5 tác nhân hệ thống. | Trần Đức Trí | Ngô Đức An | 2 ngày |
| 4. Phân rã chức năng → Module IPO | Viết mục 4: Vẽ cây phân rã chức năng WBS và lập bảng mô tả chi tiết IPO (Input - Process - Output) cho các module nghiệp vụ then chốt. | Nguyễn Ngọc Thương | Vũ Huy Hoàng | 4 ngày |
| 5. Ma trận CRUD & Luồng dữ liệu | Viết mục 5: Lập ma trận đối tượng - chức năng CRUD 5x5, mô tả 6 luồng dữ liệu chính (DF-01 đến DF-06) và workflow tổng thể. | Nguyễn Ngọc Thương | Trần Đức Trí | 2 ngày |
| 6. Thiết kế CSDL & ERD | Viết mục 6: Danh sách 8 bảng, từ điển thuộc tính chi tiết từng bảng, vẽ sơ đồ quan hệ ERD chuẩn 3NF và cơ chế giao dịch ACID. | Trần Đức Trí | Cả nhóm | 3 ngày |
| 7. Quản lý nhóm & Kiểm thử | Viết mục 7: Bảng phân công vai trò, kế hoạch giai đoạn, theo dõi tiến độ và danh mục 16 test cases kiểm thử nghiệp vụ. | Vũ Huy Hoàng | Ngô Đức An | 2 ngày |

7.3. Theo dõi công việc
Bảng 7.3. Bảng theo dõi tiến độ công việc thực tế

| Ngày | Người thực hiện | Task đang làm | % hoàn thành | Deadline | Ghi chú & Trạng thái |
| --- | --- | --- | --- | --- | --- |
| 10/11/2026 | Ngô Đức An | Khảo sát quy trình quán Hawa's Food, viết Đặt tên & Xác định bài toán | 100% | 11/11/2026 | Hoàn thành đúng hạn |
| 12/11/2026 | Nguyễn Văn Nguyên | Đặc tả yêu cầu chức năng FR, phi chức năng NFR, quy tắc nghiệp vụ BR | 100% | 14/11/2026 | Hoàn thành đúng hạn |
| 14/11/2026 | Trần Đức Trí | Xác định 5 thực thể ENT, 5 phân hệ MOD, 5 tác nhân Actor | 100% | 15/11/2026 | Hoàn thành đúng hạn |
| 15/11/2026 | Nguyễn Ngọc Thương | Phân rã WBS, viết bảng IPO cho các module cốt lõi (Haversine, Lập ca, Excel) | 100% | 17/11/2026 | Hoàn thành đúng hạn |
| 16/11/2026 | Trần Đức Trí | Thiết kế lược đồ CSDL 8 bảng, viết file  schema.sql , vẽ sơ đồ ERD | 100% | 17/11/2026 | Hoàn thành đúng hạn |
| 16/11/2026 | Nguyễn Ngọc Thương | Lập ma trận CRUD 5x5, đặc tả 6 luồng dữ liệu DF-01 đến DF-06 | 100% | 17/11/2026 | Hoàn thành đúng hạn |
| 17/11/2026 | Vũ Huy Hoàng | Xây dựng 16 ca kiểm thử nghiệp vụ, vẽ hoàn thiện 10 sơ đồ Draw.io | 100% | 17/11/2026 | Hoàn thành đúng hạn |
| 17/11/2026 | Cả nhóm | Rà soát toàn diện, xuất file Word hoàn chỉnh nộp giảng viên | 100% | 17/11/2026 | Nghiệm thu xuất sắc |

7.4. Kế hoạch 16 ca kiểm thử nghiệp vụ trọng tâm (TC-01 đến TC-16)
Bảng 7.5. Kế hoạch 16 ca kiểm thử nghiệp vụ then chốt (TC-01 đến TC-16)

| Mã TC | Tình huống kiểm tra chi tiết | Hành động thực hiện | Kết quả mong đợi chuẩn xác |
| --- | --- | --- | --- |
| TC-01 | Đăng nhập với mật khẩu không đúng | Nhập username đúng, password sai. | Hệ thống từ chối đăng nhập, trả về mã lỗi HTTP 401; Không cấp Token JWT; Tăng biến đếm đăng nhập thất bại. |
| TC-02 | Truy cập API không có Token JWT | Gửi request chấm công trực tiếp lên Server mà không đính kèm Header Authorization. | Máy chủ trả về mã lỗi HTTP 401 Unauthorized; Từ chối xử lý yêu cầu. |
| TC-03 | Nhân viên cố gắng truy cập trang Quản lý | Đăng nhập tài khoản có Role =  EMPLOYEE  nhưng truy cập URL  /admin/config . | Hệ thống điều hướng về trang cá nhân và chặn API bằng mã lỗi HTTP 403 Forbidden. |
| TC-04 | Điểm danh khi đứng trong quán ($d \le 50\,\text{m}$) | Bật định vị tại toạ độ cách tâm quán 15 mét và nhấn nút "Bấm vào ca". | Điểm danh thành công (HTTP 200); Ghi nhận giờ vào thực tế; Màn hình điện thoại hiển thị dấu tick xanh. |
| TC-05 | Điểm danh khi đứng ngoài quán ($d > 50\,\text{m}$) | Bật định vị tại phòng trọ (cách quán 2.5 km) và nhấn nút "Bấm vào ca". | Hệ thống từ chối (HTTP 403); Hiển thị thông báo: "Bạn đang cách quán 2.500m, vượt quá bán kính cho phép (50m)!". |
| TC-06 | Bật định vị nhưng sai số GPS quá lớn | Thiết bị di động trả về bán kính sai số  accuracy = 85m  (do ở trong tầng hầm kín). | Hệ thống từ chối ghi nhận, yêu cầu nhân viên di chuyển ra khu vực thông thoáng để bắt sóng GPS chính xác hơn. |
| TC-07 | Chống gian lận giờ điện thoại | Chỉnh đồng hồ trên điện thoại chạy chậm 1 tiếng so với thực tế và bấm điểm danh. | Bản ghi trong CSDL vẫn ghi nhận chính xác theo giờ máy chủ NTP; Không bị ảnh hưởng bởi đồng hồ điện thoại. |
| TC-08 | Bấm điểm danh trước giờ ca quá 30 phút | Ca làm bắt đầu lúc 12:00, nhân viên bấm lúc 11:15 trưa. | Hệ thống thông báo: "Chưa tới khung giờ điểm danh của ca này (cho phép trước tối đa 30 phút)". |
| TC-09 | Điểm danh vào ca bị trễ giờ | Ca làm bắt đầu lúc 07:00, nhân viên bấm điểm danh lúc 07:18 sáng. | Điểm danh thành công nhưng bản ghi tự động gán trạng thái  LATE  (Đi trễ 18 phút); Gửi cảnh báo lên Quản lý. |
| TC-10 | Tự động cập nhật Live qua WebSocket | Nhân viên A vừa bấm điểm danh thành công trên điện thoại. | Ngay lập tức ($< 100\,\text{ms}$), ô trạng thái của nhân viên A trên màn hình máy tính Quản lý đổi từ màu Xám sang màu Xanh. |
| TC-11 | Mất kết nối mạng tạm thời khi đang mở Dashboard | Rút dây mạng máy tính Quản lý 10 giây rồi cắm lại. | Socket.io Client tự động phát lệnh  reconnect , kết nối lại Server và đồng bộ lại trạng thái phòng trực tiếp. |
| TC-12 | Xếp 1 nhân viên vào 2 ca trùng giờ nhau | Quản lý xếp nhân viên B vào Ca Sáng (07:00 - 12:00) và Ca Gãy (10:00 - 14:00) cùng ngày. | Hệ thống phát hiện xung đột thời gian (HTTP 409 Conflict), từ chối lưu lịch và chỉ rõ khung giờ bị đè lên nhau. |
| TC-13 | Nộp đơn giải trình quên bấm công | Nhân viên quên bấm check-out, hôm sau vào nộp đơn kèm ảnh chụp đồng phục tại quán lúc tan ca. | Đơn được tạo ở trạng thái  PENDING ; Xuất hiện ngay trên danh sách chờ duyệt của Quản lý ca. |
| TC-14 | Phê duyệt đơn giải trình | Quản lý ca kiểm tra camera xác nhận đúng giờ và nhấn "Duyệt đơn". | Trạng thái đơn đổi sang  APPROVED ; Giờ ra thực tế được cập nhật tự động vào bảng  attendances ; Ghi Audit Log. |
| TC-15 | Thử chỉnh sửa bản ghi sau khi đã khóa sổ | Quản lý cố gắng dùng câu lệnh SQL hoặc API để sửa giờ của tháng trước ( is_locked = TRUE ). | CSDL từ chối cập nhật do ràng buộc kiểm tra toàn vẹn; Báo lỗi "Dữ liệu kỳ công này đã bị khóa vĩnh viễn". |
| TC-16 | Xuất báo cáo chấm công ra tệp Excel | Nhấn nút "Xuất Excel" cho kỳ công Tháng 11/2026. | Trình duyệt tải về file  .xlsx  định dạng chuẩn; Mở trên Microsoft Excel hiển thị đầy đủ tên, số ca, số giờ và không lỗi font tiếng Việt. |

KẾT LUẬN
Báo cáo phân tích và thiết kế đồ án môn học “Xây dựng hệ thống quản lý và chấm công trực tuyến định vị Geofencing thời gian thực cho quán Hawa's Food Đà Nẵng” đã hoàn thành xuất sắc toàn bộ các mục tiêu đặt ra:
1. Về mặt nghiệp vụ: Đã giải quyết triệt để bài toán đau đầu của chuỗi ẩm thực F&B: xóa bỏ tình trạng ùn tắc vân tay đầu ca, ngăn chặn hiện tượng chấm công hộ và giả lập GPS, đồng thời cung cấp công cụ phân ca thông minh tự động chống trùng lịch.
2. Về mặt công nghệ Mạng máy tính:
- Hiện thực hóa thành công mô hình Client – Server tập trung, ứng dụng giải thuật lượng giác hình cầu Haversine chạy hoàn toàn tại phía Server để thẩm định toạ độ khách quan, an toàn.
- Ứng dụng giao thức truyền thông hai chiều thời gian thực WebSocket (RFC 6455) giúp việc truyền phát sự kiện điểm danh từ thiết bị di động tới màn hình giám sát của Quản lý diễn ra tức thời với độ trễ dưới $100\,\text{ms}$, loại bỏ hoàn toàn cơ chế Polling tốn tài nguyên băng thông mạng.
- Bảo mật kênh truyền toàn diện thông qua mã hóa HTTPS/TLS 1.3 và cơ chế ủy quyền phi trạng thái JSON Web Token (JWT), bảo vệ toàn vẹn dữ liệu cá nhân của người lao động.
3. Về mặt tổ chức dữ liệu & Tài liệu kỹ thuật:
- Xây dựng mô hình CSDL gồm 8 bảng đạt chuẩn hóa 3NF, phân cấp Gốc – Cành – Lá khoa học và cơ chế bảo toàn toàn vẹn giao dịch ACID.
- Xây dựng bộ hồ sơ kỹ thuật đồng bộ 100% gồm: Đặc tả SRS, Từ điển dữ liệu, Ma trận CRUD, 6 Luồng dữ liệu, 16 Test Cases và tệp vẽ kỹ thuật trực quan 10 trang [HAWAS_FOOD_HOAN_CHINH_10_TRANG.drawio](file:///d:/MMT/HAWAS_FOOD_HOAN_CHINH_10_TRANG.drawio).
Hồ sơ thiết kế này là nền tảng vững chắc để nhóm "Huan rose và dong bon" triển khai lập trình sản phẩm thực tế, thực nghiệm bắt gói tin mạng bằng Wireshark và bảo vệ thành công đồ án với điểm số tối đa.
TÀI LIỆU THAM KHẢO
1. RFC 6455 – The WebSocket Protocol, Internet Engineering Task Force (IETF). Tham khảo đặc tả kỹ thuật khung truyền dữ liệu TCP Full-duplex và quá trình bắt tay nâng cấp giao thức  HTTP Upgrade: websocket .
2. RFC 7519 – JSON Web Token (JWT), Internet Engineering Task Force (IETF). Tham khảo cơ chế tạo chữ ký số phi trạng thái phục vụ xác thực an toàn người dùng qua mạng.
3. RFC 8446 – The Transport Layer Security (TLS) Protocol Version 1.3, IETF. Tham khảo quy trình thiết lập phiên mã hóa an toàn giữa trình duyệt Client và máy chủ Web.
4. Sinnott, R. W. (1984), *"Virtues of the Haversine"*, Sky and Telescope, 68(2), p. 159. Cơ sở toán học của công thức lượng giác hình cầu tính khoảng cách cung tròn lớn giữa hai toạ độ trên mặt đất.
5. W3C Geolocation API Specification (2nd Edition), World Wide Web Consortium. Tham khảo cơ chế trích xuất toạ độ vệ tinh GPS thông qua đối tượng  navigator.geolocation  trên trình duyệt di động.
6. Socket.io Documentation, *Real-time bidirectional event-based communication*. Tham khảo kiến trúc Room, Namespace và cơ chế tự động Fallback/Reconnect khi mất kết nối mạng.
7. IEEE Std 830-1998, *IEEE Recommended Practice for Software Requirements Specifications*. Chuẩn mực cấu trúc đặc tả yêu cầu chức năng và phi chức năng phần mềm.
8. Mẫu báo cáo Phân tích hệ thống thông tin & Mạng máy tính, Khoa Công nghệ Thông tin – Trường Đại học Kiến trúc Đà Nẵng (2026).
PHỤ LỤC A: TÀI LIỆU THAM CHIẾU 13 TRANG SƠ ĐỒ KỸ THUẬT DRAW.IO
Toàn bộ 13 sơ đồ phân tích, kiến trúc và quy trình của hệ thống đã được dựng hoàn chỉnh trong tệp tin:
👉 [HAWAS_FOOD_HOAN_CHINH_13_TRANG.drawio](file:///d:/MMT/HAWAS_FOOD_HOAN_CHINH_13_TRANG.drawio) (hoặc bản đồng bộ [HAWAS_FOOD_HOAN_CHINH_10_TRANG.drawio](file:///d:/MMT/HAWAS_FOOD_HOAN_CHINH_10_TRANG.drawio))
Bao gồm đúng 13 trang kỹ thuật tương ứng:
- Trang 1:  1. DFD - Luồng dữ liệu  (DFD Mức 0 Context Diagram + DFD Mức 1 phân rã 5 tiến trình và 5 kho dữ liệu).
- Trang 2:  2. Use Case - Ca sử dụng  (System Boundary, 4 Actors, 13 Use Cases kèm quan hệ  «include»  và  «extend» ).
- Trang 3:  3. ERD - Cơ sở dữ liệu vật lý  (Sơ đồ bảng Swimlane 8 thực thể chuẩn CSDL vật lý kèm PK, FK, UQ và đường nối quan hệ).
- Trang 4:  4. Quy trình tổng thể  (Workflow Activity Diagram mô hình hóa toàn bộ vòng đời chấm công từ xếp ca đến khóa sổ).
- Trang 5:  5. Quy trình Chấm công Geofencing  (Quy trình chi tiết giải thuật Haversine, rẽ nhánh đúng/sai $50\,\text{m}$ và bắn WebSocket).
- Trang 6:  6. Quy trình Lập lịch phân ca  (Quy trình xếp ca, kiểm tra xung đột trùng ca và ban hành lịch).
- Trang 7:  7. Quy trình Giám sát Live WebSocket  (Quy trình bắt tay TCP, mở socket room và cập nhật DOM không reload).
- Trang 8:  8. Quy trình Giải trình quên bấm công  (Quy trình nộp đơn, đối soát camera và cập nhật bổ sung giờ).
- Trang 9:  9. Quy trình Khóa sổ & Xuất Excel  (Quy trình đóng băng dữ liệu  is_locked = TRUE  và sinh tệp  .xlsx ).
- Trang 10:  10. Liên kết module  (Kiến trúc tích hợp liên phân hệ theo mô hình hướng dịch vụ).
- Trang 11:  11. Sơ đồ tuần tự (Sequence Diagram)  (UML Sequence Diagram chi tiết tương tác 7 Lifelines, thông điệp đồng bộ/bất đồng bộ và khung rẽ nhánh alt kiểm tra bán kính 50m).
- Trang 12:  12. Sơ đồ máy trạng thái (State Machine Diagram)  (UML State Machine Diagram mô hình hóa toàn bộ vòng đời ca làm việc, trạng thái hợp lệ, vi phạm và khóa sổ dữ liệu).
- Trang 13:  13. Sơ đồ phân rã chức năng (FDD)  (Functional Decomposition Diagram dạng khối hình cây phân rã chuẩn 5 phân hệ và 21 module con).