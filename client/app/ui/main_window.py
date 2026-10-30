import json
from datetime import UTC, datetime

from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView
from PySide6.QtCore import QDate, QEasingCurve, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.network.api import ApiError
from app.network.realtime import RealtimeThread
from app.ui.dialogs import Field, FormDialog
from app.ui.style import ADMIN_DARK, ADMIN_LIGHT, DARK, LIGHT

EMPLOYEE_PAGES = [
    "Tổng quan",
    "Chấm công",
    "Lịch sử",
    "Lịch làm việc",
    "Nghỉ phép",
    "Thông báo",
    "Hồ sơ cá nhân",
]
ADMIN_PAGES = [
    "Trung tâm điều hành",
    "Quản lý nhân viên",
    "Phòng ban",
    "Chức vụ",
    "Ca làm",
    "Phân ca",
    "Quản lý chấm công",
    "Duyệt điều chỉnh",
    "Duyệt nghỉ phép",
    "Loại nghỉ phép",
    "Quỹ phép",
    "Cảnh báo",
    "Xác minh ngẫu nhiên",
    "Thiết bị",
    "Client kết nối",
    "Tài khoản",
    "Báo cáo",
    "Cấu hình hệ thống",
    "Nhật ký",
]
MANAGER_PAGES = [
    "Trung tâm điều hành",
    "Quản lý nhân viên",
    "Phân ca",
    "Quản lý chấm công",
    "Duyệt điều chỉnh",
    "Duyệt nghỉ phép",
    "Quỹ phép",
    "Cảnh báo",
    "Xác minh ngẫu nhiên",
    "Thiết bị",
    "Báo cáo",
]

PAGE_ICONS = {
    "Tổng quan": "⌂",
    "Chấm công": "◷",
    "Lịch sử": "≡",
    "Lịch làm việc": "▦",
    "Nghỉ phép": "◇",
    "Thông báo": "●",
    "Hồ sơ cá nhân": "○",
    "Trung tâm điều hành": "◆",
    "Quản lý nhân viên": "♙",
    "Phòng ban": "▤",
    "Chức vụ": "▣",
    "Ca làm": "◴",
    "Phân ca": "▦",
    "Quản lý chấm công": "✓",
    "Duyệt điều chỉnh": "↻",
    "Duyệt nghỉ phép": "◇",
    "Loại nghỉ phép": "◈",
    "Quỹ phép": "⊕",
    "Cảnh báo": "!",
    "Xác minh ngẫu nhiên": "◎",
    "Thiết bị": "▱",
    "Client kết nối": "⌁",
    "Tài khoản": "♙",
    "Báo cáo": "▥",
    "Cấu hình hệ thống": "⚙",
    "Nhật ký": "≣",
}

PAGE_DESCRIPTIONS = {
    "Tổng quan": "Tóm tắt tình trạng chấm công và yêu cầu của bạn trong ngày.",
    "Chấm công": "Check-in và check-out bằng thời gian chính thức từ Server.",
    "Lịch sử": "Tra cứu lịch sử và gửi yêu cầu điều chỉnh chấm công.",
    "Lịch làm việc": "Theo dõi ca làm đã được phân công theo ngày.",
    "Nghỉ phép": "Tạo và theo dõi trạng thái các đơn nghỉ phép.",
    "Thông báo": "Thông báo nghiệp vụ và kết quả phê duyệt từ Server.",
    "Hồ sơ cá nhân": "Thông tin tài khoản và hồ sơ nhân viên hiện tại.",
    "Trung tâm điều hành": "Theo dõi toàn hệ thống và truy cập nhanh các tác vụ quản trị.",
    "Quản lý nhân viên": "Thêm, cập nhật, tìm kiếm và quản lý trạng thái nhân viên.",
    "Phòng ban": "Thiết lập cơ cấu phòng ban và người quản lý.",
    "Chức vụ": "Quản lý danh mục chức vụ trong doanh nghiệp.",
    "Ca làm": "Thiết lập giờ làm, giờ nghỉ và quy tắc đi muộn/về sớm.",
    "Phân ca": "Phân ca theo khoảng ngày và ngày làm việc trong tuần.",
    "Quản lý chấm công": "Theo dõi bản ghi chấm công theo thời gian và nhân viên.",
    "Duyệt điều chỉnh": "Duyệt hoặc từ chối các yêu cầu điều chỉnh công.",
    "Duyệt nghỉ phép": "Xử lý các đơn nghỉ phép đang chờ duyệt.",
    "Loại nghỉ phép": "Thiết lập loại phép, hưởng lương và quy tắc trừ quỹ.",
    "Quỹ phép": "Cấp và cập nhật số ngày phép theo nhân viên, năm và loại phép.",
    "Cảnh báo": "Kiểm tra và xử lý thủ công các dấu hiệu bất thường.",
    "Xác minh ngẫu nhiên": "Theo dõi kết quả các yêu cầu xác minh hiện diện.",
    "Thiết bị": "Phê duyệt hoặc thu hồi thiết bị được phép chấm công.",
    "Client kết nối": "Danh sách tài khoản đang kết nối thời gian thực tới Server.",
    "Tài khoản": "Quản lý vai trò và mở khóa tài khoản.",
    "Báo cáo": "Lọc, xem và xuất báo cáo Excel/PDF theo thời gian và nhân sự.",
    "Cấu hình hệ thống": "Cập nhật cấu hình vận hành, sao lưu và khôi phục dữ liệu.",
    "Nhật ký": "Theo dõi đăng nhập và các thay đổi quan trọng trong hệ thống.",
}

TABLE_COLUMNS = {
    "Lịch sử": [
        "id",
        "work_date",
        "check_in_at",
        "check_out_at",
        "status",
        "worked_minutes",
        "late_minutes",
        "early_leave_minutes",
    ],
    "Lịch làm việc": ["id", "work_date", "shift_name", "employee_id"],
    "Nghỉ phép": [
        "id",
        "leave_type_name",
        "start_date",
        "end_date",
        "days",
        "reason",
        "status",
        "review_note",
    ],
    "Thông báo": ["id", "title", "message", "category", "read_at", "created_at"],
    "Hồ sơ cá nhân": ["id", "username", "role", "employee"],
    "Quản lý nhân viên": [
        "id",
        "employee_code",
        "full_name",
        "email",
        "phone",
        "department_name",
        "position_name",
        "hire_date",
        "active",
    ],
    "Phòng ban": ["id", "code", "name", "manager_name", "active"],
    "Chức vụ": ["id", "code", "name", "active"],
    "Ca làm": [
        "id",
        "code",
        "name",
        "start_time",
        "end_time",
        "break_minutes",
        "late_grace_minutes",
        "early_grace_minutes",
        "active",
    ],
    "Phân ca": ["id", "work_date", "employee_code", "full_name", "shift_name"],
    "Quản lý chấm công": [
        "id",
        "employee_code",
        "full_name",
        "work_date",
        "check_in_at",
        "check_out_at",
        "status",
        "worked_minutes",
        "late_minutes",
        "early_leave_minutes",
    ],
    "Duyệt điều chỉnh": [
        "id",
        "attendance_id",
        "employee_code",
        "full_name",
        "work_date",
        "proposed_check_in",
        "proposed_check_out",
        "reason",
        "status",
        "review_note",
    ],
    "Duyệt nghỉ phép": [
        "id",
        "employee_code",
        "full_name",
        "leave_type_name",
        "start_date",
        "end_date",
        "days",
        "reason",
        "status",
    ],
    "Loại nghỉ phép": ["id", "code", "name", "paid", "deduct_balance", "active"],
    "Quỹ phép": [
        "id",
        "employee_code",
        "full_name",
        "leave_type_name",
        "year",
        "allocated_days",
        "used_days",
        "remaining_days",
    ],
    "Cảnh báo": [
        "id",
        "employee_code",
        "full_name",
        "type",
        "severity",
        "description",
        "status",
        "created_at",
    ],
    "Xác minh ngẫu nhiên": [
        "id",
        "employee_code",
        "full_name",
        "sent_at",
        "expires_at",
        "responded_at",
        "result",
        "response_ip",
    ],
    "Thiết bị": [
        "id",
        "employee_code",
        "full_name",
        "device_name",
        "approved",
        "active",
        "last_ip",
        "last_seen_at",
    ],
    "Client kết nối": ["user_id", "username", "role", "employee_id", "connections"],
    "Tài khoản": ["id", "username", "role", "employee_id", "active", "locked_until"],
    "Báo cáo": [
        "employee_id",
        "employee_code",
        "full_name",
        "department",
        "work_days",
        "hours",
        "late_count",
        "early_count",
        "leave_days",
    ],
    "Cấu hình hệ thống": ["key", "value", "description"],
    "Nhật ký": ["id", "created_at", "user_id", "action", "entity_type", "entity_id", "client_ip"],
}

COLUMN_LABELS = {
    "id": "ID",
    "user_id": "Người dùng",
    "employee_id": "Nhân viên",
    "employee_code": "Mã NV",
    "full_name": "Họ tên",
    "username": "Tài khoản",
    "role": "Vai trò",
    "email": "Email",
    "phone": "Điện thoại",
    "department": "Phòng ban",
    "department_id": "Phòng ban",
    "department_name": "Phòng ban",
    "position_id": "Chức vụ",
    "position_name": "Chức vụ",
    "hire_date": "Ngày vào làm",
    "active": "Hoạt động",
    "code": "Mã",
    "name": "Tên",
    "manager_employee_id": "Quản lý",
    "manager_name": "Người quản lý",
    "start_time": "Bắt đầu",
    "end_time": "Kết thúc",
    "break_minutes": "Nghỉ (phút)",
    "late_grace_minutes": "Ân hạn muộn",
    "early_grace_minutes": "Ân hạn sớm",
    "work_date": "Ngày làm",
    "shift_id": "Ca",
    "shift_name": "Tên ca",
    "check_in_at": "Check-in",
    "check_out_at": "Check-out",
    "status": "Trạng thái",
    "worked_minutes": "Phút làm",
    "late_minutes": "Phút muộn",
    "early_leave_minutes": "Phút sớm",
    "leave_type_id": "Loại phép",
    "leave_type_name": "Loại phép",
    "start_date": "Từ ngày",
    "end_date": "Đến ngày",
    "days": "Số ngày",
    "reason": "Lý do",
    "review_note": "Ghi chú duyệt",
    "title": "Tiêu đề",
    "message": "Nội dung",
    "category": "Loại",
    "read_at": "Đã đọc lúc",
    "created_at": "Thời gian",
    "employee": "Hồ sơ",
    "attendance_id": "Bản ghi công",
    "requested_by": "Người yêu cầu",
    "proposed_check_in": "Check-in đề xuất",
    "proposed_check_out": "Check-out đề xuất",
    "paid": "Có lương",
    "deduct_balance": "Trừ quỹ",
    "year": "Năm",
    "allocated_days": "Được cấp",
    "used_days": "Đã dùng",
    "remaining_days": "Còn lại",
    "type": "Loại",
    "severity": "Mức độ",
    "description": "Mô tả",
    "sent_at": "Gửi lúc",
    "expires_at": "Hết hạn",
    "responded_at": "Phản hồi lúc",
    "result": "Kết quả",
    "response_ip": "IP phản hồi",
    "device_name": "Thiết bị",
    "approved": "Đã duyệt",
    "last_ip": "IP gần nhất",
    "last_seen_at": "Hoạt động cuối",
    "connections": "Số kết nối",
    "locked_until": "Khóa đến",
    "work_days": "Ngày công",
    "hours": "Giờ làm",
    "late_count": "Lần muộn",
    "early_count": "Lần về sớm",
    "leave_days": "Ngày phép",
    "key": "Khóa cấu hình",
    "value": "Giá trị",
    "action": "Hành động",
    "entity_type": "Đối tượng",
    "entity_id": "ID đối tượng",
    "client_ip": "IP Client",
}

STATUS_TEXT = {
    "PENDING": "Chờ duyệt",
    "APPROVED": "Đã duyệt",
    "REJECTED": "Từ chối",
    "CANCELLED": "Đã hủy",
    "ON_TIME": "Đúng giờ",
    "LATE": "Đi muộn",
    "EARLY_LEAVE": "Về sớm",
    "LATE_AND_EARLY": "Muộn & về sớm",
    "OPEN": "Đang mở",
    "CONFIRMED": "Đã xác nhận",
    "DISMISSED": "Đã bỏ qua",
    "VERIFIED": "Đã xác minh",
    "MISSED": "Không phản hồi",
    "ADMIN": "Quản trị",
    "MANAGER": "Quản lý",
    "EMPLOYEE": "Nhân viên",
}


class MainWindow(QMainWindow):
    session_ended = Signal(bool)

    def __init__(self, api, admin_only=False):
        super().__init__()
        self.api = api
        self.admin_only = admin_only
        self.dark = False
        self.table_rows = {}
        self.table_filters = {}
        self.empty_states = {}
        self.loading_bars = {}
        self.table_pagination = {}
        self.nav_buttons = []
        self._logout_requested = False
        self._session_end_emitted = False
        self.setWindowTitle(
            "LAN Attendance — Trung tâm quản trị"
            if admin_only
            else "LAN Attendance — Cổng nhân viên"
        )
        self.resize(1360, 820)
        shell = QWidget()
        sidebar = QFrame(objectName="adminSidebar" if admin_only else "sidebar")
        root, nav = QHBoxLayout(shell), QVBoxLayout(sidebar)
        root.setContentsMargins(14, 14, 14, 14)
        sidebar.setFixedWidth(260 if admin_only else 230)
        nav.setContentsMargins(16, 22, 16, 22)
        brand = QLabel("ADMIN\nCONTROL CENTER" if admin_only else "LAN\nATTENDANCE")
        brand.setStyleSheet("font-size: 17pt; font-weight: 800; letter-spacing: 1px;")
        nav.addWidget(brand)
        role = QLabel("QUẢN TRỊ HỆ THỐNG" if api.role == "ADMIN" else "QUẢN LÝ PHÒNG BAN")
        role.setObjectName("roleBadge")
        role.setAlignment(Qt.AlignCenter)
        nav.addWidget(role)
        nav.addSpacing(8)
        self.stack = QStackedWidget()
        management_pages = ADMIN_PAGES if api.role == "ADMIN" else MANAGER_PAGES
        self.page_names = (
            management_pages
            if admin_only
            else EMPLOYEE_PAGES + (management_pages if api.role in ("ADMIN", "MANAGER") else [])
        )
        for name in self.page_names:
            label = f"{PAGE_ICONS.get(name, '•')}   {name}"
            button, index = QPushButton(label), self.stack.count()
            button.setProperty("nav", True)
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, i=index: self.show_page(i))
            nav.addWidget(button)
            self.nav_buttons.append(button)
            self.stack.addWidget(self.make_page(name))
        nav.addStretch()
        theme = QPushButton("Sáng / Tối")
        theme.setProperty("secondary", True)
        theme.clicked.connect(self.toggle_theme)
        nav.addWidget(theme)
        logout = QPushButton("Đăng xuất")
        logout.setProperty("danger", True)
        logout.clicked.connect(self.logout)
        nav.addWidget(logout)
        self.connection = QLabel("● Đang kết nối")
        nav.addWidget(self.connection)
        root.addWidget(sidebar)
        root.addWidget(self.stack, 1)
        self.setCentralWidget(shell)
        self.setStyleSheet(ADMIN_LIGHT if admin_only else LIGHT)
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)
        self.realtime = RealtimeThread(lambda: self.api.websocket_url, self)
        self.realtime.connection_changed.connect(self.connection_state)
        self.realtime.message.connect(self.realtime_message)
        self.realtime.start()
        QTimer.singleShot(50, self.refresh_dashboard)
        if api.device_registration_pending:
            QTimer.singleShot(
                200,
                lambda: QMessageBox.information(
                    self, "Thiết bị mới", "Thiết bị đang chờ Admin phê duyệt trước khi chấm công."
                ),
            )

    def make_page(self, name):
        page, layout = QWidget(), QVBoxLayout()
        page.setLayout(layout)
        layout.setContentsMargins(26, 18, 26, 18)
        header, header_box = QFrame(objectName="pageHeader"), QVBoxLayout()
        header.setLayout(header_box)
        header_box.setContentsMargins(0, 0, 0, 5)
        header_box.addWidget(QLabel(name, objectName="title"))
        header_box.addWidget(QLabel(PAGE_DESCRIPTIONS.get(name, ""), objectName="subtitle"))
        layout.addWidget(header)
        if name == "Trung tâm điều hành":
            self.build_admin_dashboard(layout)
            return page
        if name == "Tổng quan":
            self.metrics, grid = {}, QGridLayout()
            metric_definitions = [
                ("present", "Đang có mặt"),
                ("late", "Đi muộn"),
                ("pending_leave", "Đơn chờ duyệt"),
                ("open_alerts", "Cảnh báo"),
            ]
            for i, (key, label) in enumerate(metric_definitions):
                card, box = QFrame(objectName="card"), QVBoxLayout()
                card.setLayout(box)
                box.addWidget(QLabel(label))
                value = QLabel("—", objectName="metric")
                box.addWidget(value)
                self.metrics[key] = value
                grid.addWidget(card, i // 2, i % 2)
            layout.addLayout(grid)
            self.chart_values = QBarSet("Số lượng")
            self.chart_values.append([0] * len(metric_definitions))
            series = QBarSeries()
            series.append(self.chart_values)
            chart = QChart()
            chart.addSeries(series)
            chart.createDefaultAxes()
            chart.setTitle("Tình hình trong ngày")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            categories = QBarCategoryAxis()
            categories.append([label for _, label in metric_definitions])
            for axis in chart.axes(Qt.Horizontal):
                chart.removeAxis(axis)
            chart.addAxis(categories, Qt.AlignBottom)
            series.attachAxis(categories)
            chart.legend().setVisible(False)
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(300)
            layout.addWidget(chart_view)
            return page
        if name == "Chấm công":
            clock, buttons = QLabel(objectName="metric"), QHBoxLayout()
            clock.setAlignment(Qt.AlignCenter)
            timer = QTimer(page)
            timer.timeout.connect(
                lambda: clock.setText(datetime.now().strftime("%d/%m/%Y  %H:%M:%S"))
            )
            timer.start(1000)
            for label, action in (("CHECK-IN", "check-in"), ("CHECK-OUT", "check-out")):
                button = QPushButton(label)
                button.clicked.connect(lambda _=False, a=action: self.do_attendance(a))
                buttons.addWidget(button)
            layout.addWidget(clock)
            layout.addLayout(buttons)
            return page
        toolbar, controls = QFrame(objectName="toolbar"), QHBoxLayout()
        toolbar.setLayout(controls)
        controls.setContentsMargins(0, 0, 0, 0)
        table = QTableWidget()
        table.setProperty("page_name", name)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setVisible(False)
        endpoint = self.endpoint_for(name)
        self.add_page_filters(name, table, controls)
        refresh = QPushButton("↻ Tải lại")
        refresh.setProperty("secondary", True)
        refresh.clicked.connect(lambda _=False, t=table, e=endpoint: self.load_table(t, e))
        controls.addWidget(refresh)
        for label, handler in self.actions_for(name, table):
            button = QPushButton(label)
            button.clicked.connect(handler)
            controls.addWidget(button)
        controls.addStretch()
        layout.addWidget(toolbar)
        loading = QProgressBar()
        loading.setRange(0, 0)
        loading.setTextVisible(False)
        loading.setFixedHeight(4)
        loading.hide()
        self.loading_bars[table] = loading
        layout.addWidget(loading)
        empty = QFrame(objectName="emptyCard")
        empty_box = QVBoxLayout(empty)
        empty_box.setContentsMargins(22, 18, 22, 18)
        empty_box.addWidget(QLabel("Chưa có dữ liệu", objectName="emptyTitle"))
        empty_text = QLabel(self.empty_message(name), objectName="emptyText")
        empty_text.setWordWrap(True)
        empty_box.addWidget(empty_text)
        empty.hide()
        self.empty_states[table] = empty
        layout.addWidget(empty)
        layout.addWidget(table)
        pagination_bar = QHBoxLayout()
        previous_page = QPushButton("‹ Trang trước")
        previous_page.setProperty("secondary", True)
        page_label = QLabel("Trang 1/1 — 0 bản ghi")
        next_page = QPushButton("Trang sau ›")
        next_page.setProperty("secondary", True)
        previous_page.setEnabled(False)
        next_page.setEnabled(False)
        pagination_bar.addStretch()
        pagination_bar.addWidget(previous_page)
        pagination_bar.addWidget(page_label)
        pagination_bar.addWidget(next_page)
        self.table_pagination[table] = {
            "page": 1,
            "page_size": 50,
            "pages": 1,
            "total": 0,
            "label": page_label,
            "previous": previous_page,
            "next": next_page,
        }
        previous_page.clicked.connect(
            lambda _=False, t=table, e=endpoint: self.change_table_page(t, e, -1)
        )
        next_page.clicked.connect(
            lambda _=False, t=table, e=endpoint: self.change_table_page(t, e, 1)
        )
        layout.addLayout(pagination_bar)
        QTimer.singleShot(100, lambda t=table, e=endpoint: self.load_table(t, e))
        return page

    def build_admin_dashboard(self, layout):
        self.admin_metrics = {}
        grid = QGridLayout()
        definitions = [
            ("total_employees", "Nhân viên hoạt động"),
            ("present", "Đang có mặt"),
            ("late", "Đi muộn hôm nay"),
            ("pending_leave", "Đơn phép chờ duyệt"),
            ("open_alerts", "Cảnh báo đang mở"),
            ("connected_clients", "Client trực tuyến"),
        ]
        for index, (key, title) in enumerate(definitions):
            card = QFrame(objectName="adminCard")
            box = QVBoxLayout(card)
            box.addWidget(QLabel(title))
            value = QLabel("—", objectName="adminMetric")
            box.addWidget(value)
            self.admin_metrics[key] = value
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)

        quick_card = QFrame(objectName="card")
        quick = QVBoxLayout(quick_card)
        quick.addWidget(QLabel("Tác vụ quản trị nhanh", objectName="emptyTitle"))
        quick.addWidget(
            QLabel(
                "Thiết lập danh mục theo thứ tự: Phòng ban → Chức vụ → Ca làm → Nhân viên → Phân ca.",
                objectName="subtitle",
            )
        )
        buttons = QHBoxLayout()
        for label, target in (
            ("Thêm nhân viên", "Quản lý nhân viên"),
            ("Phân ca", "Phân ca"),
            ("Duyệt nghỉ phép", "Duyệt nghỉ phép"),
            ("Xử lý cảnh báo", "Cảnh báo"),
            ("Xem báo cáo", "Báo cáo"),
        ):
            button = QPushButton(label)
            button.clicked.connect(lambda _=False, page_name=target: self.go_to_page(page_name))
            buttons.addWidget(button)
        quick.addLayout(buttons)
        layout.addWidget(quick_card)
        layout.addStretch()

    def add_page_filters(self, name, table, controls):
        filters = {}
        endpoint = self.endpoint_for(name)
        if name == "Quản lý nhân viên":
            search = QLineEdit()
            search.setPlaceholderText("Tìm mã, tên hoặc email...")
            search.setClearButtonEnabled(True)
            search.returnPressed.connect(lambda t=table, e=endpoint: self.load_table(t, e))
            controls.addWidget(search)
            filters["search"] = search
            active = QComboBox()
            active.addItem("Tất cả trạng thái", None)
            active.addItem("Đang hoạt động", True)
            active.addItem("Đã ngừng", False)
            controls.addWidget(active)
            filters["active"] = active
            departments = QComboBox()
            departments.addItem("Tất cả phòng ban", None)
            for item in self.safe_get("/api/v1/departments"):
                departments.addItem(item["name"], item["id"])
            controls.addWidget(departments)
            filters["department_id"] = departments
        if name in (
            "Lịch sử",
            "Lịch làm việc",
            "Phân ca",
            "Quản lý chấm công",
            "Báo cáo",
        ):
            start = QDateEdit(calendarPopup=True)
            start.setDisplayFormat("dd/MM/yyyy")
            start.setDate(QDate.currentDate().addMonths(-1))
            end = QDateEdit(calendarPopup=True)
            end.setDisplayFormat("dd/MM/yyyy")
            end.setDate(QDate.currentDate())
            controls.addWidget(QLabel("Từ"))
            controls.addWidget(start)
            controls.addWidget(QLabel("Đến"))
            controls.addWidget(end)
            filters.update({"start": start, "end": end})
        if name in ("Quản lý chấm công", "Báo cáo", "Xác minh ngẫu nhiên"):
            employees = QComboBox()
            employees.addItem("Tất cả nhân viên", None)
            for item in self.safe_get("/api/v1/employees", params={"active": True}):
                employees.addItem(f"{item['employee_code']} — {item['full_name']}", item["id"])
            controls.addWidget(employees)
            filters["employee_id"] = employees
        if name == "Báo cáo" and self.api.role == "ADMIN":
            departments = QComboBox()
            departments.addItem("Tất cả phòng ban", None)
            for item in self.safe_get("/api/v1/departments"):
                departments.addItem(item["name"], item["id"])
            controls.addWidget(departments)
            filters["department_id"] = departments
        if name == "Duyệt điều chỉnh":
            status = QComboBox()
            status.addItem("Đang chờ duyệt", "PENDING")
            status.addItem("Tất cả trạng thái", None)
            status.addItem("Đã duyệt", "APPROVED")
            status.addItem("Đã từ chối", "REJECTED")
            controls.addWidget(status)
            filters["status"] = status
        if filters:
            apply_filter = QPushButton("Áp dụng bộ lọc")
            apply_filter.setProperty("secondary", True)
            apply_filter.clicked.connect(lambda _=False, t=table, e=endpoint: self.load_table(t, e))
            controls.addWidget(apply_filter)
        self.table_filters[table] = filters

    def safe_get(self, path, **kwargs):
        try:
            data = self.api.request("GET", path, **kwargs)
            return data if isinstance(data, list) else []
        except ApiError:
            return []

    def change_table_page(self, table, endpoint, direction):
        state = self.table_pagination.get(table)
        if not state:
            return
        target = state["page"] + direction
        if 1 <= target <= state["pages"]:
            state["page"] = target
            self.load_table(table, endpoint)

    @staticmethod
    def empty_message(name):
        messages = {
            "Quản lý nhân viên": "Chưa có nhân viên phù hợp. Hãy tạo phòng ban và chức vụ trước, sau đó chọn Thêm.",
            "Phòng ban": "Chưa có phòng ban. Chọn Thêm để thiết lập cơ cấu đầu tiên.",
            "Chức vụ": "Chưa có chức vụ. Chọn Thêm để tạo danh mục chức vụ.",
            "Ca làm": "Chưa có ca làm. Chọn Thêm để khai báo thời gian và quy tắc chấm công.",
            "Phân ca": "Chưa có lịch phân ca trong phạm vi đang xem. Chọn Phân ca để tạo lịch.",
            "Loại nghỉ phép": "Chưa có loại nghỉ phép. Chọn Thêm để thiết lập chính sách phép.",
            "Quỹ phép": "Chưa cấp quỹ phép. Chọn Cấp/Cập nhật quỹ để bắt đầu.",
            "Báo cáo": "Chưa có dữ liệu công hoặc nghỉ phép trong khoảng thời gian đã chọn.",
        }
        return messages.get(name, "Chưa phát sinh dữ liệu phù hợp với bộ lọc hiện tại.")

    def show_page(self, index):
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        self.page_animation = QPropertyAnimation(effect, b"opacity", self)
        self.page_animation.setDuration(180)
        self.page_animation.setStartValue(0.35)
        self.page_animation.setEndValue(1.0)
        self.page_animation.setEasingCurve(QEasingCurve.OutCubic)
        self.page_animation.finished.connect(lambda: page.setGraphicsEffect(None))
        self.page_animation.start()

    def go_to_page(self, name):
        if name in self.page_names:
            self.show_page(self.page_names.index(name))

    @staticmethod
    def endpoint_for(name):
        return {
            "Lịch sử": "/api/v1/attendance",
            "Lịch làm việc": "/api/v1/shift-assignments",
            "Nghỉ phép": "/api/v1/leaves",
            "Thông báo": "/api/v1/notifications",
            "Hồ sơ cá nhân": "/api/v1/me",
            "Quản lý nhân viên": "/api/v1/employees",
            "Phòng ban": "/api/v1/departments",
            "Chức vụ": "/api/v1/positions",
            "Ca làm": "/api/v1/shifts",
            "Phân ca": "/api/v1/shift-assignments",
            "Quản lý chấm công": "/api/v1/attendance",
            "Duyệt điều chỉnh": "/api/v1/attendance/adjustments?status=PENDING",
            "Duyệt nghỉ phép": "/api/v1/leaves?status=PENDING",
            "Loại nghỉ phép": "/api/v1/leave-types",
            "Quỹ phép": "/api/v1/leave-balances",
            "Cảnh báo": "/api/v1/security-alerts?status=OPEN",
            "Xác minh ngẫu nhiên": "/api/v1/random-checks",
            "Thiết bị": "/api/v1/devices",
            "Client kết nối": "/api/v1/clients",
            "Tài khoản": "/api/v1/users",
            "Báo cáo": "/api/v1/reports/attendance",
            "Cấu hình hệ thống": "/api/v1/settings",
            "Nhật ký": "/api/v1/audit-logs",
        }.get(name, "/api/v1/health")

    def actions_for(self, name, table):
        common = {
            "Quản lý nhân viên": [("Gửi Random Check", lambda: self.trigger_random_check(table))],
            "Lịch sử": [("Yêu cầu điều chỉnh", lambda: self.request_adjustment(table))],
            "Nghỉ phép": [
                ("Tạo đơn", lambda: self.create_leave(table)),
                ("Hủy đơn", lambda: self.cancel_leave(table)),
            ],
            "Thông báo": [("Đánh dấu đã đọc", lambda: self.mark_read(table))],
            "Hồ sơ cá nhân": [("Đổi mật khẩu", self.change_password)],
            "Phân ca": [("Phân ca", lambda: self.assign_shift(table))],
            "Duyệt điều chỉnh": [
                ("Duyệt", lambda: self.review(table, "adjustment", True)),
                ("Từ chối", lambda: self.review(table, "adjustment", False)),
            ],
            "Duyệt nghỉ phép": [
                ("Duyệt", lambda: self.review(table, "leave", True)),
                ("Từ chối", lambda: self.review(table, "leave", False)),
            ],
            "Cảnh báo": [
                ("Xác nhận", lambda: self.review(table, "alert", True)),
                ("Bỏ cảnh báo", lambda: self.review(table, "alert", False)),
            ],
            "Báo cáo": [
                ("Xuất Excel", lambda: self.export_report("xlsx", table)),
                ("Xuất PDF", lambda: self.export_report("pdf", table)),
            ],
        }
        admin = {
            "Quản lý nhân viên": [
                ("Thêm", lambda: self.create_employee(table)),
                ("Sửa", lambda: self.edit_employee(table)),
                ("Ngừng/Kích hoạt", lambda: self.toggle_employee(table)),
                ("Gửi Random Check", lambda: self.trigger_random_check(table)),
            ],
            "Phòng ban": [
                ("Thêm", lambda: self.create_department(table)),
                ("Sửa", lambda: self.edit_department(table)),
                ("Ngừng", lambda: self.deactivate(table, "departments")),
            ],
            "Chức vụ": [
                ("Thêm", lambda: self.create_position(table)),
                ("Sửa", lambda: self.edit_position(table)),
                ("Ngừng", lambda: self.deactivate(table, "positions")),
            ],
            "Ca làm": [
                ("Thêm", lambda: self.create_shift(table)),
                ("Sửa", lambda: self.edit_shift(table)),
                ("Ngừng", lambda: self.deactivate(table, "shifts")),
            ],
            "Loại nghỉ phép": [
                ("Thêm", lambda: self.create_leave_type(table)),
                ("Sửa", lambda: self.edit_leave_type(table)),
                ("Ngừng", lambda: self.deactivate(table, "leave-types")),
            ],
            "Quỹ phép": [("Cấp/Cập nhật quỹ", lambda: self.set_leave_balance(table))],
            "Thiết bị": [
                ("Phê duyệt", lambda: self.approve_device(table, True)),
                ("Thu hồi", lambda: self.approve_device(table, False)),
            ],
            "Tài khoản": [
                ("Đổi vai trò", lambda: self.change_role(table)),
                ("Mở khóa", lambda: self.unlock_user(table)),
            ],
            "Cấu hình hệ thống": [
                ("Cập nhật", lambda: self.update_setting(table)),
                ("Sao lưu", self.create_backup),
                ("Khôi phục", self.restore_backup),
            ],
        }
        if self.api.role == "ADMIN":
            return (common | admin).get(name, [])
        return common.get(name, [])

    def load_table(self, table, endpoint):
        path, _, query = endpoint.partition("?")
        params = dict(part.split("=", 1) for part in query.split("&") if part)
        for key, widget in self.table_filters.get(table, {}).items():
            if isinstance(widget, QDateEdit):
                value = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QComboBox):
                value = widget.currentData()
            else:
                value = widget.text().strip()
            if value is not None and value != "":
                params[key] = value
            else:
                params.pop(key, None)
        if path == "/api/v1/reports/attendance" and not {"start", "end"} <= params.keys():
            params.update(
                start=QDate.currentDate().addMonths(-1).toString("yyyy-MM-dd"),
                end=QDate.currentDate().toString("yyyy-MM-dd"),
            )
        pagination_state = self.table_pagination.get(table)
        if pagination_state:
            params["page"] = pagination_state["page"]
            params["page_size"] = pagination_state["page_size"]
        loading = self.loading_bars.get(table)
        if loading:
            loading.show()
            QApplication.processEvents()
        try:
            data = self.api.request("GET", path, params=params)
        except ApiError as exc:
            QMessageBox.warning(self, "Không tải được dữ liệu", str(exc))
            return
        finally:
            if loading:
                loading.hide()
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            rows = data["items"]
            metadata = data.get("pagination", {})
            if pagination_state:
                pagination_state.update(
                    page=int(metadata.get("page", 1)),
                    pages=int(metadata.get("pages", 1)),
                    total=int(metadata.get("total", len(rows))),
                )
                pagination_state["label"].setText(
                    f"Trang {pagination_state['page']}/{pagination_state['pages']}"
                    f" — {pagination_state['total']} bản ghi"
                )
                pagination_state["previous"].setEnabled(pagination_state["page"] > 1)
                pagination_state["next"].setEnabled(
                    pagination_state["page"] < pagination_state["pages"]
                )
        elif path == "/api/v1/clients" and isinstance(data, dict):
            rows = [{"user_id": user_id, "connections": 1} for user_id in data.get("user_ids", [])]
        else:
            rows = data if isinstance(data, list) else [data]
        rows = [row for row in rows if isinstance(row, dict)]
        self.table_rows[table] = rows
        page_name = table.property("page_name")
        columns = list(TABLE_COLUMNS.get(page_name, []))
        if not columns:
            for row in rows:
                for key in row:
                    if key not in columns:
                        columns.append(key)
        table.setSortingEnabled(False)
        table.clearContents()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([COLUMN_LABELS.get(key, key) for key in columns])
        table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col_idx, key in enumerate(columns):
                value = row.get(key, "")
                item = QTableWidgetItem(self.format_cell(value))
                if key in ("status", "result", "role"):
                    self.color_status_item(item, value)
                table.setItem(row_idx, col_idx, item)
        table.resizeColumnsToContents()
        if columns:
            table.horizontalHeader().setStretchLastSection(True)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.setSortingEnabled(bool(rows))
        if table in self.empty_states:
            self.empty_states[table].setVisible(not rows)

    @staticmethod
    def format_cell(value):
        if value is None or value == "":
            return "—"
        if isinstance(value, bool):
            return "Có" if value else "Không"
        if isinstance(value, dict):
            employee = value
            if "employee_code" in employee and "full_name" in employee:
                return f"{employee['employee_code']} — {employee['full_name']}"
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, list):
            return ", ".join(str(item) for item in value) if value else "—"
        text = str(value)
        if text in STATUS_TEXT:
            return STATUS_TEXT[text]
        if "T" in text and len(text) >= 16:
            return text.replace("T", " ")[:19]
        return text

    @staticmethod
    def color_status_item(item, value):
        palette = {
            "APPROVED": ("#166534", "#DCFCE7"),
            "VERIFIED": ("#166534", "#DCFCE7"),
            "ON_TIME": ("#166534", "#DCFCE7"),
            "ADMIN": ("#155E75", "#CFFAFE"),
            "PENDING": ("#92400E", "#FEF3C7"),
            "OPEN": ("#92400E", "#FEF3C7"),
            "MANAGER": ("#5B21B6", "#EDE9FE"),
            "REJECTED": ("#991B1B", "#FEE2E2"),
            "MISSED": ("#991B1B", "#FEE2E2"),
            "LATE": ("#991B1B", "#FEE2E2"),
            "EMPLOYEE": ("#1E40AF", "#DBEAFE"),
        }
        if str(value) in palette:
            foreground, background = palette[str(value)]
            item.setForeground(QBrush(QColor(foreground)))
            item.setBackground(QBrush(QColor(background)))

    def selected(self, table):
        index, rows = table.currentRow(), self.table_rows.get(table, [])
        if index < 0 or index >= len(rows):
            QMessageBox.information(self, "Chọn dữ liệu", "Hãy chọn một dòng trước.")
            return None
        return rows[index]

    def submit_dialog(self, title, fields, method, path):
        dialog = FormDialog(title, fields, self)
        if dialog.exec() != FormDialog.Accepted:
            return None
        try:
            result = self.api.request(method, path, json=dialog.values())
            self.show_toast("Đã lưu thay đổi thành công.")
            return {} if result is None else result
        except ApiError as exc:
            QMessageBox.warning(self, "Không thực hiện được", str(exc))
            return None

    def create_leave(self, table):
        try:
            types = self.api.request("GET", "/api/v1/leave-types")
        except ApiError as exc:
            QMessageBox.warning(self, "Không tải được loại nghỉ", str(exc))
            return
        if not types:
            QMessageBox.information(
                self,
                "Chưa có loại nghỉ phép",
                "Admin cần tạo ít nhất một loại nghỉ phép trước khi nhân viên tạo đơn.",
            )
            return
        fields = [
            Field(
                "leave_type_id",
                "Loại nghỉ",
                "choice",
                options=[(x["name"], x["id"]) for x in types],
            ),
            Field("start_date", "Từ ngày", "date"),
            Field("end_date", "Đến ngày", "date"),
            Field("reason", "Lý do", "multiline"),
        ]
        if self.submit_dialog("Tạo đơn nghỉ phép", fields, "POST", "/api/v1/leaves"):
            self.load_table(table, "/api/v1/leaves")

    def cancel_leave(self, table):
        row = self.selected(table)
        if not row:
            return
        if row.get("status") not in ("PENDING", "APPROVED"):
            QMessageBox.information(
                self, "Không thể hủy", "Chỉ có thể hủy đơn đang chờ hoặc đã duyệt."
            )
            return
        if (
            QMessageBox.question(
                self,
                "Hủy đơn nghỉ phép",
                f"Bạn chắc chắn muốn hủy đơn #{row['id']}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return
        try:
            self.api.request("POST", f"/api/v1/leaves/{row['id']}/cancel")
            self.show_toast("Đã hủy đơn nghỉ phép.")
            self.load_table(table, "/api/v1/leaves")
        except ApiError as exc:
            QMessageBox.warning(self, "Không hủy được đơn", str(exc))

    def create_employee(self, table):
        try:
            departments, positions = (
                self.api.request("GET", "/api/v1/departments"),
                self.api.request("GET", "/api/v1/positions"),
            )
        except ApiError as exc:
            QMessageBox.warning(self, "Không tải được danh mục", str(exc))
            return
        if not departments or not positions:
            QMessageBox.information(
                self,
                "Cần thiết lập danh mục",
                "Hãy tạo ít nhất một Phòng ban và một Chức vụ trước khi thêm nhân viên.",
            )
            return
        fields = [
            Field("employee_code", "Mã nhân viên"),
            Field("full_name", "Họ tên"),
            Field("email", "Email"),
            Field("phone", "Điện thoại", required=False),
            Field(
                "department_id",
                "Phòng ban",
                "choice",
                options=[(x["name"], x["id"]) for x in departments],
            ),
            Field(
                "position_id",
                "Chức vụ",
                "choice",
                options=[(x["name"], x["id"]) for x in positions],
            ),
            Field("hire_date", "Ngày vào làm", "date"),
            Field("username", "Username"),
            Field("temporary_password", "Mật khẩu tạm", "password"),
            Field(
                "role",
                "Vai trò",
                "choice",
                options=[(x, x) for x in ("EMPLOYEE", "MANAGER", "ADMIN")],
            ),
        ]
        if self.submit_dialog("Thêm nhân viên", fields, "POST", "/api/v1/employees"):
            self.load_table(table, "/api/v1/employees")

    def edit_employee(self, table):
        row = self.selected(table)
        if not row:
            return
        departments = self.api.request("GET", "/api/v1/departments")
        positions = self.api.request("GET", "/api/v1/positions")
        fields = [
            Field("full_name", "Họ tên", value=row.get("full_name")),
            Field("email", "Email", value=row.get("email")),
            Field("phone", "Điện thoại", value=row.get("phone"), required=False),
            Field(
                "department_id",
                "Phòng ban",
                "choice",
                row.get("department_id"),
                [(x["name"], x["id"]) for x in departments],
            ),
            Field(
                "position_id",
                "Chức vụ",
                "choice",
                row.get("position_id"),
                [(x["name"], x["id"]) for x in positions],
            ),
            Field("hire_date", "Ngày vào làm", "date", row.get("hire_date")),
        ]
        if self.submit_dialog("Sửa nhân viên", fields, "PUT", f"/api/v1/employees/{row['id']}"):
            self.load_table(table, "/api/v1/employees")

    def create_department(self, table):
        employees = self.safe_get("/api/v1/employees", params={"active": True})
        fields = [
            Field("code", "Mã"),
            Field("name", "Tên"),
            Field(
                "manager_employee_id",
                "Người quản lý",
                "choice",
                options=[("Chưa gán", None)]
                + [(f"{x['employee_code']} — {x['full_name']}", x["id"]) for x in employees],
                required=False,
            ),
        ]
        if self.submit_dialog("Thêm phòng ban", fields, "POST", "/api/v1/departments"):
            self.load_table(table, "/api/v1/departments")

    def edit_department(self, table):
        row = self.selected(table)
        if not row:
            return
        employees = self.safe_get("/api/v1/employees", params={"active": True})
        fields = [
            Field("code", "Mã", value=row.get("code")),
            Field("name", "Tên", value=row.get("name")),
            Field(
                "manager_employee_id",
                "Người quản lý",
                "choice",
                row.get("manager_employee_id"),
                [("Chưa gán", None)]
                + [(f"{x['employee_code']} — {x['full_name']}", x["id"]) for x in employees],
                required=False,
            ),
        ]
        if self.submit_dialog("Sửa phòng ban", fields, "PUT", f"/api/v1/departments/{row['id']}"):
            self.load_table(table, "/api/v1/departments")

    def create_position(self, table):
        fields = [Field("code", "Mã"), Field("name", "Tên chức vụ")]
        if self.submit_dialog("Thêm chức vụ", fields, "POST", "/api/v1/positions"):
            self.load_table(table, "/api/v1/positions")

    def edit_position(self, table):
        row = self.selected(table)
        if not row:
            return
        fields = [
            Field("code", "Mã", value=row.get("code")),
            Field("name", "Tên chức vụ", value=row.get("name")),
        ]
        if self.submit_dialog("Sửa chức vụ", fields, "PUT", f"/api/v1/positions/{row['id']}"):
            self.load_table(table, "/api/v1/positions")

    def create_shift(self, table):
        fields = [
            Field("code", "Mã ca"),
            Field("name", "Tên ca"),
            Field("start_time", "Giờ bắt đầu", "time"),
            Field("end_time", "Giờ kết thúc", "time"),
            Field("break_minutes", "Phút nghỉ", "int"),
            Field("late_grace_minutes", "Ân hạn muộn", "int"),
            Field("early_grace_minutes", "Ân hạn về sớm", "int"),
        ]
        if self.submit_dialog("Thêm ca", fields, "POST", "/api/v1/shifts"):
            self.load_table(table, "/api/v1/shifts")

    def edit_shift(self, table):
        row = self.selected(table)
        if not row:
            return
        fields = [
            Field("code", "Mã ca", value=row.get("code")),
            Field("name", "Tên ca", value=row.get("name")),
            Field("start_time", "Giờ bắt đầu", "time", row.get("start_time")),
            Field("end_time", "Giờ kết thúc", "time", row.get("end_time")),
            Field("break_minutes", "Phút nghỉ", "int", row.get("break_minutes")),
            Field("late_grace_minutes", "Ân hạn muộn", "int", row.get("late_grace_minutes", 0)),
            Field("early_grace_minutes", "Ân hạn về sớm", "int", row.get("early_grace_minutes", 0)),
        ]
        if self.submit_dialog("Sửa ca", fields, "PUT", f"/api/v1/shifts/{row['id']}"):
            self.load_table(table, "/api/v1/shifts")

    def create_leave_type(self, table):
        fields = [
            Field("code", "Mã"),
            Field("name", "Tên loại nghỉ"),
            Field("paid", "Có lương", "bool", True),
            Field("deduct_balance", "Trừ quỹ phép", "bool", True),
        ]
        if self.submit_dialog("Thêm loại nghỉ", fields, "POST", "/api/v1/leave-types"):
            self.load_table(table, "/api/v1/leave-types")

    def edit_leave_type(self, table):
        row = self.selected(table)
        if not row:
            return
        fields = [
            Field("code", "Mã", value=row.get("code")),
            Field("name", "Tên loại nghỉ", value=row.get("name")),
            Field("paid", "Có lương", "bool", row.get("paid")),
            Field("deduct_balance", "Trừ quỹ phép", "bool", row.get("deduct_balance")),
        ]
        if self.submit_dialog("Sửa loại nghỉ", fields, "PUT", f"/api/v1/leave-types/{row['id']}"):
            self.load_table(table, "/api/v1/leave-types")

    def set_leave_balance(self, table):
        try:
            employees = self.api.request("GET", "/api/v1/employees", params={"active": True})
            leave_types = self.api.request("GET", "/api/v1/leave-types")
        except ApiError as exc:
            QMessageBox.warning(self, "Không tải được danh mục", str(exc))
            return
        if not employees or not leave_types:
            QMessageBox.information(
                self,
                "Chưa đủ dữ liệu",
                "Cần có nhân viên và loại nghỉ phép trước khi cấp quỹ phép.",
            )
            return
        fields = [
            Field(
                "employee_id",
                "Nhân viên",
                "choice",
                options=[(f"{x['employee_code']} — {x['full_name']}", x["id"]) for x in employees],
            ),
            Field(
                "leave_type_id",
                "Loại nghỉ",
                "choice",
                options=[(x["name"], x["id"]) for x in leave_types],
            ),
            Field("year", "Năm", "int", QDate.currentDate().year()),
            Field("allocated_days", "Số ngày cấp", "decimal"),
        ]
        if self.submit_dialog("Cấp quỹ phép", fields, "PUT", "/api/v1/leave-balances"):
            self.load_table(table, "/api/v1/leave-balances")

    def deactivate(self, table, resource):
        row = self.selected(table)
        if not row:
            return
        if QMessageBox.question(self, "Xác nhận", "Ngừng sử dụng mục đã chọn?") != QMessageBox.Yes:
            return
        try:
            self.api.request("DELETE", f"/api/v1/{resource}/{row['id']}")
            self.load_table(
                table,
                self.endpoint_for(
                    {
                        "departments": "Phòng ban",
                        "positions": "Chức vụ",
                        "shifts": "Ca làm",
                        "leave-types": "Loại nghỉ phép",
                    }[resource]
                ),
            )
        except ApiError as exc:
            QMessageBox.warning(self, "Không thực hiện được", str(exc))

    def assign_shift(self, table):
        try:
            employees, shifts = (
                self.api.request("GET", "/api/v1/employees", params={"active": True}),
                self.api.request("GET", "/api/v1/shifts"),
            )
        except ApiError as exc:
            QMessageBox.warning(self, "Không tải được danh mục", str(exc))
            return
        if not employees or not shifts:
            QMessageBox.information(
                self,
                "Chưa đủ dữ liệu",
                "Cần có nhân viên và ca làm trước khi thực hiện phân ca.",
            )
            return
        fields = [
            Field(
                "employee_id",
                "Nhân viên",
                "choice",
                options=[(f"{x['employee_code']} — {x['full_name']}", x["id"]) for x in employees],
            ),
            Field("shift_id", "Ca", "choice", options=[(x["name"], x["id"]) for x in shifts]),
            Field("start_date", "Từ ngày", "date"),
            Field("end_date", "Đến ngày", "date"),
            Field("weekdays", "Ngày áp dụng", "weekdays", [0, 1, 2, 3, 4]),
        ]
        dialog = FormDialog("Phân ca", fields, self)
        if dialog.exec() == FormDialog.Accepted:
            values = dialog.values()
            try:
                self.api.request("POST", "/api/v1/shift-assignments", json=values)
                self.load_table(table, "/api/v1/shift-assignments")
            except ApiError as exc:
                QMessageBox.warning(self, "Không phân ca được", str(exc))

    def request_adjustment(self, table):
        row = self.selected(table)
        if not row:
            return
        fields = [
            Field(
                "proposed_check_in", "Check-in ISO", value=row.get("check_in_at"), required=False
            ),
            Field(
                "proposed_check_out", "Check-out ISO", value=row.get("check_out_at"), required=False
            ),
            Field("reason", "Lý do", "multiline"),
        ]
        dialog = FormDialog("Yêu cầu điều chỉnh", fields, self)
        if dialog.exec() == FormDialog.Accepted:
            try:
                self.api.request(
                    "POST",
                    "/api/v1/attendance/adjustments",
                    json={"attendance_id": row["id"], **dialog.values()},
                )
                QMessageBox.information(self, "Đã gửi", "Yêu cầu đang chờ quản lý xem xét.")
            except ApiError as exc:
                QMessageBox.warning(self, "Không gửi được", str(exc))

    def review(self, table, kind, approve):
        row = self.selected(table)
        if not row:
            return
        dialog = FormDialog("Xử lý yêu cầu", [Field("note", "Ghi chú", "multiline")], self)
        if dialog.exec() != FormDialog.Accepted:
            return
        endpoints = {
            "leave": f"/api/v1/leaves/{row['id']}/review",
            "adjustment": f"/api/v1/attendance/adjustments/{row['id']}/review",
            "alert": f"/api/v1/security-alerts/{row['id']}/resolve",
        }
        reloads = {
            "leave": "/api/v1/leaves?status=PENDING",
            "adjustment": "/api/v1/attendance/adjustments",
            "alert": "/api/v1/security-alerts?status=OPEN",
        }
        try:
            self.api.request(
                "POST", endpoints[kind], json={"approve": approve, "note": dialog.values()["note"]}
            )
            self.load_table(table, reloads[kind])
        except ApiError as exc:
            QMessageBox.warning(self, "Không xử lý được", str(exc))

    def approve_device(self, table, approved):
        row = self.selected(table)
        if row:
            try:
                self.api.request(
                    "PATCH",
                    f"/api/v1/devices/{row['id']}/approve",
                    params={"approved": approved},
                )
                self.load_table(table, "/api/v1/devices")
            except ApiError as exc:
                QMessageBox.warning(self, "Không cập nhật được thiết bị", str(exc))

    def toggle_employee(self, table):
        row = self.selected(table)
        if row:
            try:
                self.api.request(
                    "PATCH",
                    f"/api/v1/employees/{row['id']}/active",
                    params={"active": not row["active"]},
                )
                self.load_table(table, "/api/v1/employees")
            except ApiError as exc:
                QMessageBox.warning(self, "Không cập nhật được nhân viên", str(exc))

    def trigger_random_check(self, table):
        row = self.selected(table)
        if not row:
            return
        if not row.get("active", True):
            QMessageBox.warning(self, "Không thể xác minh", "Nhân viên này đã ngừng hoạt động.")
            return
        if (
            QMessageBox.question(
                self,
                "Gửi xác minh hiện diện",
                f"Gửi Random Check tới {row.get('full_name', row['id'])}?",
            )
            != QMessageBox.Yes
        ):
            return
        try:
            result = self.api.request("POST", f"/api/v1/random-checks/{row['id']}")
            QMessageBox.information(
                self,
                "Đã gửi Random Check",
                f"Yêu cầu #{result['id']} đã được gửi. Theo dõi tại trang Xác minh ngẫu nhiên.",
            )
        except ApiError as exc:
            QMessageBox.warning(self, "Không gửi được Random Check", str(exc))

    def change_role(self, table):
        row = self.selected(table)
        if not row:
            return
        dialog = FormDialog(
            "Đổi vai trò",
            [
                Field(
                    "role",
                    "Vai trò",
                    "choice",
                    options=[(x, x) for x in ("EMPLOYEE", "MANAGER", "ADMIN")],
                )
            ],
            self,
        )
        if dialog.exec() == FormDialog.Accepted:
            try:
                self.api.request(
                    "PATCH",
                    f"/api/v1/users/{row['id']}/role",
                    params={"role": dialog.values()["role"]},
                )
                self.load_table(table, "/api/v1/users")
            except ApiError as exc:
                QMessageBox.warning(self, "Không đổi được vai trò", str(exc))

    def unlock_user(self, table):
        row = self.selected(table)
        if row:
            try:
                self.api.request("POST", f"/api/v1/users/{row['id']}/unlock")
                self.load_table(table, "/api/v1/users")
            except ApiError as exc:
                QMessageBox.warning(self, "Không mở khóa được tài khoản", str(exc))

    def mark_read(self, table):
        row = self.selected(table)
        if row:
            try:
                self.api.request("POST", f"/api/v1/notifications/{row['id']}/read")
                self.load_table(table, "/api/v1/notifications")
            except ApiError as exc:
                QMessageBox.warning(self, "Không cập nhật được thông báo", str(exc))

    def change_password(self):
        fields = [
            Field("current_password", "Mật khẩu hiện tại", "password"),
            Field("new_password", "Mật khẩu mới", "password"),
        ]
        if (
            self.submit_dialog("Đổi mật khẩu", fields, "POST", "/api/v1/auth/change-password")
            is not None
        ):
            QMessageBox.information(self, "Đã đổi mật khẩu", "Hãy đăng nhập lại.")
            self.close()

    def update_setting(self, table):
        row = self.selected(table)
        fields = [
            Field("key", "Khóa", value=row.get("key") if row else ""),
            Field(
                "value",
                "JSON value",
                "multiline",
                value=json.dumps(row.get("value", {}) if row else {}, ensure_ascii=False),
            ),
            Field(
                "description", "Mô tả", value=row.get("description") if row else "", required=False
            ),
        ]
        dialog = FormDialog("Cập nhật cấu hình", fields, self)
        if dialog.exec() == FormDialog.Accepted:
            values = dialog.values()
            try:
                self.api.request(
                    "PUT",
                    f"/api/v1/settings/{values['key']}",
                    json={
                        "value": json.loads(values["value"]),
                        "description": values["description"],
                    },
                )
                self.load_table(table, "/api/v1/settings")
            except (ValueError, ApiError) as exc:
                QMessageBox.warning(self, "Cấu hình không hợp lệ", str(exc))

    def create_backup(self):
        try:
            result = self.api.request("POST", "/api/v1/admin/backup")
            QMessageBox.information(self, "Sao lưu thành công", result["filename"])
        except ApiError as exc:
            QMessageBox.warning(self, "Sao lưu thất bại", str(exc))

    def restore_backup(self):
        try:
            backups = self.api.request("GET", "/api/v1/admin/backups")
        except ApiError as exc:
            QMessageBox.warning(self, "Không tải được backup", str(exc))
            return
        if not backups:
            QMessageBox.information(self, "Khôi phục", "Chưa có bản sao lưu nào trên Server.")
            return
        fields = [
            Field(
                "filename",
                "Bản sao lưu",
                "choice",
                options=[
                    (f"{x['filename']} — {x['size_bytes']} bytes", x["filename"]) for x in backups
                ],
            )
        ]
        dialog = FormDialog("Chọn bản sao lưu", fields, self)
        if dialog.exec() != FormDialog.Accepted:
            return
        filename = dialog.values()["filename"]
        if (
            QMessageBox.warning(
                self,
                "Xác nhận khôi phục",
                f"Database hiện tại sẽ được thay bằng {filename}. Tiếp tục?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return
        try:
            self.api.request("POST", f"/api/v1/admin/restore/{filename}")
            QMessageBox.information(
                self,
                "Khôi phục thành công",
                "Dữ liệu đã được khôi phục. Hãy đăng nhập lại để tải trạng thái mới.",
            )
            self.close()
        except ApiError as exc:
            QMessageBox.warning(self, "Khôi phục thất bại", str(exc))

    def export_report(self, extension, table=None):
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu báo cáo", f"attendance.{extension}", f"*.{extension}"
        )
        if not path:
            return
        params = {}
        for key, widget in self.table_filters.get(table, {}).items():
            if isinstance(widget, QDateEdit):
                value = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QComboBox):
                value = widget.currentData()
            else:
                value = widget.text().strip()
            if value is not None and value != "":
                params[key] = value
        params.setdefault("start", QDate.currentDate().addMonths(-1).toString("yyyy-MM-dd"))
        params.setdefault("end", QDate.currentDate().toString("yyyy-MM-dd"))
        try:
            with open(path, "wb") as stream:
                stream.write(self.api.download(f"/api/v1/reports/attendance.{extension}", params))
            self.show_toast(f"Đã xuất báo cáo: {path}")
        except (OSError, ApiError) as exc:
            QMessageBox.warning(self, "Không xuất được báo cáo", str(exc))

    def refresh_dashboard(self):
        if hasattr(self, "metrics") or hasattr(self, "admin_metrics"):
            try:
                data = self.api.request("GET", "/api/v1/dashboard")
                for key, label in getattr(self, "metrics", {}).items():
                    label.setText(str(data.get(key, 0)))
                for key, label in getattr(self, "admin_metrics", {}).items():
                    label.setText(str(data.get(key, 0)))
                if hasattr(self, "chart_values"):
                    for index, key in enumerate(getattr(self, "metrics", {})):
                        self.chart_values.replace(index, float(data.get(key, 0)))
            except ApiError:
                self.connection_state(False)

    def do_attendance(self, action):
        try:
            data = self.api.attendance(action)
            self.show_toast(
                f"Chấm công thành công — {STATUS_TEXT.get(data['status'], data['status'])}"
            )
        except ApiError as exc:
            QMessageBox.warning(self, "Không thể chấm công", str(exc))

    def realtime_message(self, payload):
        if payload.get("type") == "random_check":
            self.show_random_check(payload)
        elif payload.get("type") in (
            "attendance_changed",
            "leave_requested",
            "leave_cancelled",
            "security_alerts_updated",
        ):
            self.refresh_dashboard()

    def show_random_check(self, payload):
        try:
            expires_at = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
        except (KeyError, TypeError, ValueError):
            QMessageBox.warning(self, "Random Check", "Yêu cầu xác minh không có hạn hợp lệ.")
            return

        dialog = QMessageBox(self)
        dialog.setWindowTitle("Random Check — Xác minh hiện diện")
        dialog.setIcon(QMessageBox.Question)
        dialog.setText("Bạn có đang làm việc tại máy đã đăng ký không?")
        dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_button = dialog.button(QMessageBox.Yes)
        confirm_button.setText("Xác nhận hiện diện")
        dialog.button(QMessageBox.No).setText("Không xác nhận")
        timer = QTimer(dialog)
        remaining = {"seconds": 0}

        def update_countdown():
            seconds = max(0, int((expires_at - datetime.now(UTC)).total_seconds() + 0.999))
            remaining["seconds"] = seconds
            dialog.setInformativeText(f"Thời gian còn lại: {seconds:02d} giây")
            if seconds <= 0:
                timer.stop()
                confirm_button.setEnabled(False)
                dialog.setText("Yêu cầu Random Check đã hết hạn.")
                QTimer.singleShot(1000, dialog.reject)

        timer.timeout.connect(update_countdown)
        update_countdown()
        if remaining["seconds"] > 0:
            timer.start(250)
        accepted = dialog.exec() == QMessageBox.Yes and remaining["seconds"] > 0
        timer.stop()
        if not accepted:
            return
        try:
            self.api.request(
                "POST",
                "/api/v1/random-checks/respond",
                json={"challenge_token": payload["challenge_token"]},
            )
            self.show_toast("Đã xác minh hiện diện thành công.")
        except ApiError as exc:
            QMessageBox.warning(self, "Xác minh thất bại", str(exc))

    def connection_state(self, connected):
        self.connection.setText("● Đã kết nối" if connected else "● Mất kết nối — đang thử lại")
        self.connection.setStyleSheet("color: #22C55E" if connected else "color: #EF4444")

    def toggle_theme(self):
        self.dark = not self.dark
        if self.admin_only:
            self.setStyleSheet(ADMIN_DARK if self.dark else ADMIN_LIGHT)
        else:
            self.setStyleSheet(DARK if self.dark else LIGHT)

    def show_toast(self, message, error=False):
        if hasattr(self, "toast") and self.toast:
            self.toast.deleteLater()
        self.toast = QFrame(self.centralWidget())
        self.toast.setStyleSheet(
            "QFrame { background: %s; border-radius: 10px; } "
            "QLabel { color: white; background: transparent; padding: 11px 16px; font-weight: 600; }"
            % ("#B91C1C" if error else ("#0E7490" if self.admin_only else "#166534"))
        )
        box = QHBoxLayout(self.toast)
        box.setContentsMargins(0, 0, 0, 0)
        box.addWidget(QLabel(message))
        self.toast.adjustSize()
        margin = 24
        self.toast.move(
            self.centralWidget().width() - self.toast.width() - margin,
            self.centralWidget().height() - self.toast.height() - margin,
        )
        effect = QGraphicsOpacityEffect(self.toast)
        self.toast.setGraphicsEffect(effect)
        self.toast_animation = QPropertyAnimation(effect, b"opacity", self)
        self.toast_animation.setDuration(180)
        self.toast_animation.setStartValue(0.0)
        self.toast_animation.setEndValue(1.0)
        self.toast.show()
        self.toast.raise_()
        self.toast_animation.start()
        QTimer.singleShot(3200, self.toast.hide)

    def logout(self):
        try:
            self.api.request("POST", "/api/v1/auth/logout")
        except ApiError as exc:
            if (
                QMessageBox.question(
                    self,
                    "Không kết nối được Server",
                    f"Không thể thu hồi phiên trên Server: {exc}\nVẫn đăng xuất?",
                )
                != QMessageBox.Yes
            ):
                return
        self.api.token = None
        self.api.role = None
        self.api.employee_id = None
        self._logout_requested = True
        self._finish_session(logged_out=True)

    def _finish_session(self, logged_out):
        if self._session_end_emitted:
            return
        self.realtime.stop()
        self.realtime.wait(2000)
        self._session_end_emitted = True
        if logged_out:
            self.hide()
        self.session_ended.emit(logged_out)

    def closeEvent(self, event):
        self._finish_session(logged_out=self._logout_requested)
        event.accept()
