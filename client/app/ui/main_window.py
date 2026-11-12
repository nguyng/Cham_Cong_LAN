import json
from datetime import UTC, datetime

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
)
from PySide6.QtCore import (
    QDate,
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QBrush, QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QApplication,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.network.api import ApiError
from app.network.realtime import RealtimeThread
from app.ui.attendance_portal import AttendancePortalMixin
from app.ui.catalog import (
    ADMIN_PAGES,
    COLUMN_LABELS,
    EMPLOYEE_PAGES,
    MANAGEMENT_NAV_SECTIONS,
    MANAGER_PAGES,
    PAGE_DESCRIPTIONS,
    STATUS_TEXT,
    TABLE_COLUMNS,
)
from app.ui.dialogs import Field, FormDialog
from app.ui.excel_export import styled_workbook_bytes
from app.ui.icons import decorate_button
from app.ui.leave_portal import LeavePortalMixin
from app.ui.payroll_ui import PayrollUiMixin
from app.ui.style import ADMIN_DARK, ADMIN_LIGHT, DARK, LIGHT

from ..files import write_bytes_atomic


class MainWindow(AttendancePortalMixin, LeavePortalMixin, PayrollUiMixin, QMainWindow):
    session_ended = Signal(bool)

    @staticmethod
    def add_shadow(widget, blur=24, y_offset=6, alpha=38):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(0, y_offset)
        shadow.setColor(QColor(15, 23, 42, alpha))
        widget.setGraphicsEffect(shadow)

    @staticmethod
    def configure_table(table: QTableWidget) -> None:
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setWordWrap(False)
        table.setTextElideMode(Qt.ElideRight)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        table.setShowGrid(False)
        table.setCornerButtonEnabled(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(42)
        header = table.horizontalHeader()
        header.setFixedHeight(44)
        header.setMinimumSectionSize(76)
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSectionsClickable(True)
        header.setHighlightSections(False)

    @staticmethod
    def fit_table_columns(table: QTableWidget, columns: list[str]) -> None:
        compact = {"id", "active", "approved", "paid", "deduct_balance", "year"}
        wide = {
            "full_name",
            "email",
            "reason",
            "description",
            "message",
            "employee",
            "review_note",
        }
        medium = {
            "employee_code",
            "department_name",
            "position_name",
            "status",
            "device_name",
            "username",
            "role",
        }
        coordinates = {
            "check_in_latitude",
            "check_in_longitude",
            "check_out_latitude",
            "check_out_longitude",
        }
        for index, key in enumerate(columns):
            minimum = 72 if key in compact else 185 if key in wide else 135 if key in medium else 112
            if key in coordinates:
                minimum = 128
            table.setColumnWidth(index, min(280, max(minimum, table.columnWidth(index))))
            header_item = table.horizontalHeaderItem(index)
            if header_item:
                header_item.setToolTip(header_item.text())
        table.horizontalHeader().setStretchLastSection(len(columns) <= 5)

    @staticmethod
    def toolbar_scroller(content: QWidget, height: int = 72) -> QScrollArea:
        content_layout = content.layout()
        if content_layout:
            content_layout.setSizeConstraint(QLayout.SetMinimumSize)
        content.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        content.adjustSize()
        scroller = QScrollArea(objectName="toolbarScroll")
        scroller.setSizeAdjustPolicy(QAbstractScrollArea.AdjustIgnored)
        scroller.setWidgetResizable(False)
        scroller.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        scroller.setMinimumWidth(0)
        scroller.setFrameShape(QFrame.NoFrame)
        scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroller.setMinimumHeight(height)
        scroller.setMaximumHeight(height + 12)
        scroller.setWidget(content)
        return scroller

    @staticmethod
    def vertical_page_scroller(content: QWidget) -> QScrollArea:
        if content.layout():
            content.layout().activate()
        content.setMinimumWidth(0)
        content.setMinimumHeight(content.sizeHint().height())
        scroller = QScrollArea(objectName="pageScroll")
        scroller.setWidgetResizable(True)
        scroller.setFrameShape(QFrame.NoFrame)
        scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroller.setWidget(content)
        return scroller

    def apply_control_design(self) -> None:
        for button in self.findChildren(QPushButton):
            navigation = bool(button.property("nav"))
            decorate_button(button, navigation=navigation)
            if button.property("attendanceAction"):
                button.setMinimumHeight(58)
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        for scroller in self.findChildren(QScrollArea, "toolbarScroll"):
            content = scroller.widget()
            if content and content.layout():
                content.layout().activate()
                hint = content.sizeHint()
                content.resize(QSize(max(1, hint.width()), max(1, hint.height())))
        for scroller in self.findChildren(QScrollArea, "pageScroll"):
            content = scroller.widget()
            if content and content.layout():
                content.layout().activate()
                content.setMinimumHeight(content.sizeHint().height())

    def __init__(self, api, admin_only=False):
        super().__init__()
        self.api = api
        self.admin_only = admin_only
        self.employee_portal = not admin_only
        self.dark = False
        self.table_rows = {}
        self.table_filters = {}
        self.empty_states = {}
        self.loading_bars = {}
        self.table_pagination = {}
        self.nav_buttons = []
        self._logout_requested = False
        self._session_end_emitted = False
        self._dashboard_error_shown = False
        self._realtime_error_shown = False
        self._realtime_ever_connected = False
        self._local_server_shutdown_generation = 0
        self.setWindowTitle(
            "LAN Attendance — Trung tâm quản trị"
            if admin_only
            else "LAN Attendance — Cổng nhân viên"
        )
        self.setMinimumSize(900, 600)
        self.resize(1360, 820)
        shell = QWidget(objectName="appShell")
        sidebar = QFrame(objectName="adminSidebar" if admin_only else "sidebar")
        root, sidebar_box = QHBoxLayout(shell), QVBoxLayout(sidebar)
        root.setContentsMargins(14, 14, 14, 14)
        sidebar.setFixedWidth(260 if admin_only else 230)
        sidebar_box.setContentsMargins(16, 20, 10, 16)
        sidebar_box.setSpacing(10)
        brand = QLabel("ADMIN\nCONTROL CENTER" if admin_only else "LAN\nATTENDANCE")
        brand.setStyleSheet("font-size: 17pt; font-weight: 800; letter-spacing: 1px;")
        sidebar_box.addWidget(brand)
        if self.employee_portal:
            role_text = "CHẾ ĐỘ NHÂN VIÊN"
        elif api.role == "ADMIN":
            role_text = "QUẢN TRỊ HỆ THỐNG"
        else:
            role_text = "QUẢN LÝ PHÒNG BAN"
        role = QLabel(role_text)
        role.setObjectName("roleBadge")
        role.setAlignment(Qt.AlignCenter)
        sidebar_box.addWidget(role)

        self.nav_scroll = QScrollArea(objectName="navScroll")
        self.nav_scroll.setWidgetResizable(True)
        self.nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.nav_scroll.setFrameShape(QFrame.NoFrame)
        nav_content = QWidget(objectName="navContent")
        nav = QVBoxLayout(nav_content)
        nav.setContentsMargins(0, 4, 5, 4)
        nav.setSpacing(5)
        self.stack = QStackedWidget()
        management_pages = ADMIN_PAGES if api.role == "ADMIN" else MANAGER_PAGES
        self.page_names = management_pages if admin_only else EMPLOYEE_PAGES
        for name in self.page_names:
            if admin_only and name in MANAGEMENT_NAV_SECTIONS:
                section = QLabel(MANAGEMENT_NAV_SECTIONS[name], objectName="navSection")
                section.setProperty("nav_section", True)
                nav.addWidget(section)
            button, index = QPushButton(name), self.stack.count()
            button.setProperty("nav", True)
            button.setProperty("page_name", name)
            button.setCheckable(True)
            button.setMinimumHeight(40)
            button.clicked.connect(lambda _checked=False, i=index: self.show_page(i))
            nav.addWidget(button)
            self.nav_buttons.append(button)
            self.stack.addWidget(self.make_page(name))
        nav.addStretch()
        self.nav_scroll.setWidget(nav_content)
        sidebar_box.addWidget(self.nav_scroll, 1)

        footer = QFrame(objectName="sidebarFooter")
        footer_box = QVBoxLayout(footer)
        footer_box.setContentsMargins(0, 8, 6, 0)
        footer_box.setSpacing(7)
        theme = QPushButton("Sáng / Tối")
        theme.setProperty("secondary", True)
        theme.clicked.connect(self.toggle_theme)
        footer_box.addWidget(theme)
        logout = QPushButton("Đăng xuất")
        logout.setProperty("danger", True)
        logout.clicked.connect(self.logout)
        footer_box.addWidget(logout)
        self.connection = QLabel("● Đang kết nối")
        self.connection.setWordWrap(True)
        footer_box.addWidget(self.connection)
        sidebar_box.addWidget(footer)
        root.addWidget(sidebar)
        root.addWidget(self.stack, 1)
        self.setCentralWidget(shell)
        self.setStyleSheet(ADMIN_LIGHT if admin_only else LIGHT)
        self.apply_control_design()
        required_sidebar_width = max(
            (button.minimumWidth() for button in self.nav_buttons),
            default=sidebar.width(),
        ) + 34
        sidebar.setFixedWidth(max(sidebar.width(), min(370, required_sidebar_width)))
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)
        self.realtime = RealtimeThread(
            lambda: self.api.websocket_url,
            self,
            headers_factory=lambda: self.api.websocket_headers,
        )
        self.realtime.connection_changed.connect(self.connection_state)
        self.realtime.error.connect(self.realtime_error)
        self.realtime.message.connect(self.realtime_message)
        self.realtime.start()
        QTimer.singleShot(50, self.refresh_dashboard)
        if api.device_registration_pending:
            QTimer.singleShot(
                200,
                lambda: QMessageBox.information(
                    self,
                    "Thiết bị mới",
                    "Máy này đã được đăng ký nhưng chưa được phê duyệt.\n\n"
                    "Hãy mở AttendanceAdmin → Phê duyệt thiết bị → chọn máy này → Phê duyệt, "
                    "sau đó chấm công lại.",
                ),
            )

    def make_page(self, name):
        page, layout = QWidget(), QVBoxLayout()
        page.setLayout(layout)
        layout.setContentsMargins(26, 18, 26, 18)
        header, header_box = QFrame(objectName="pageHeader"), QVBoxLayout()
        header.setLayout(header_box)
        header_box.setContentsMargins(20, 14, 20, 14)
        header_box.addWidget(QLabel(name, objectName="title"))
        subtitle = QLabel(PAGE_DESCRIPTIONS.get(name, ""), objectName="subtitle")
        subtitle.setWordWrap(True)
        header_box.addWidget(subtitle)
        self.add_shadow(header, blur=22, y_offset=4, alpha=26)
        layout.addWidget(header)
        if name == "Trung tâm điều hành":
            self.build_admin_dashboard(layout)
            return self.vertical_page_scroller(page)
        if name == "Lương & chuyên cần":
            self.build_payroll_page(layout)
            return self.vertical_page_scroller(page)
        if name == "Tổng quan":
            self.metrics, grid = {}, QGridLayout()
            metric_definitions = [
                ("present", "Đang có mặt"),
                ("late", "Đi muộn"),
                ("pending_leave", "Đơn chờ duyệt"),
                ("open_alerts", "Cảnh báo"),
            ]
            tones = ("blue", "violet", "mint", "coral")
            for i, (key, label) in enumerate(metric_definitions):
                card, box = QFrame(objectName="card"), QVBoxLayout()
                card.setProperty("tone", tones[i % len(tones)])
                card.setLayout(box)
                box.addWidget(QLabel(label))
                value = QLabel("—", objectName="metric")
                box.addWidget(value)
                self.metrics[key] = value
                grid.addWidget(card, i // 2, i % 2)
                self.add_shadow(card, blur=20, y_offset=5, alpha=24)
            layout.addLayout(grid)
            self.chart_values = QBarSet("Số lượng")
            self.chart_values.setColor(QColor("#4F46E5"))
            self.chart_values.setBorderColor(QColor("#4338CA"))
            self.chart_values.append([0] * len(metric_definitions))
            series = QBarSeries()
            series.append(self.chart_values)
            chart = QChart()
            chart.addSeries(series)
            chart.createDefaultAxes()
            chart.setTitle("Tình hình trong ngày")
            chart.setTitleFont(QFont("Segoe UI", 12, QFont.DemiBold))
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
            hero = QFrame(objectName="attendanceHero")
            self.add_shadow(hero, blur=34, y_offset=9, alpha=52)
            hero_box = QVBoxLayout(hero)
            hero_box.setContentsMargins(32, 26, 32, 26)
            hero_box.setSpacing(4)
            eyebrow = QLabel("THỜI GIAN MÁY CHỦ", objectName="attendanceEyebrow")
            eyebrow.setAlignment(Qt.AlignCenter)
            self.attendance_clock = QLabel(objectName="attendanceClock")
            self.attendance_clock.setAlignment(Qt.AlignCenter)
            self.attendance_date = QLabel(objectName="attendanceDate")
            self.attendance_date.setAlignment(Qt.AlignCenter)
            self.attendance_status = QLabel("CHƯA CHECK-IN", objectName="attendanceStatus")
            self.attendance_status.setAlignment(Qt.AlignCenter)
            hero_box.addWidget(eyebrow)
            hero_box.addWidget(self.attendance_clock)
            hero_box.addWidget(self.attendance_date)
            hero_box.addSpacing(10)
            hero_box.addWidget(self.attendance_status, 0, Qt.AlignCenter)
            layout.addWidget(hero)

            action_card = QFrame(objectName="attendanceActionCard")
            self.add_shadow(action_card, blur=22, y_offset=5, alpha=26)
            action_box = QVBoxLayout(action_card)
            action_box.setContentsMargins(24, 20, 24, 20)
            action_box.setSpacing(14)
            action_box.addWidget(QLabel("Ghi nhận thời gian làm việc", objectName="sectionTitle"))
            action_box.addWidget(
                QLabel(
                    "Chọn thao tác phù hợp. Thời gian lấy từ Server và vị trí lấy từ GPS của máy.",
                    objectName="subtitle",
                )
            )
            gps_panel = QFrame(objectName="attendanceGpsPanel")
            gps_box = QHBoxLayout(gps_panel)
            gps_box.setContentsMargins(16, 12, 16, 12)
            gps_icon = QLabel("⌖", objectName="gpsIcon")
            gps_text = QVBoxLayout()
            gps_text.setSpacing(2)
            gps_text.addWidget(QLabel("VỊ TRÍ CHẤM CÔNG", objectName="gpsTitle"))
            self.attendance_location = QLabel(
                "GPS sẽ được xác định khi bạn nhấn CHECK-IN hoặc CHECK-OUT.",
                objectName="gpsValue",
            )
            self.attendance_location.setWordWrap(True)
            gps_text.addWidget(self.attendance_location)
            gps_box.addWidget(gps_icon)
            gps_box.addLayout(gps_text, 1)
            action_box.addWidget(gps_panel)
            buttons = QVBoxLayout()
            buttons.setSpacing(14)
            self.check_in_button = QPushButton("▶  CHECK-IN")
            self.check_in_button.setProperty("attendanceAction", "checkin")
            self.check_in_button.setMinimumHeight(58)
            self.check_in_button.clicked.connect(
                lambda _checked=False: self.do_attendance("check-in")
            )
            self.check_out_button = QPushButton("■  CHECK-OUT")
            self.check_out_button.setProperty("attendanceAction", "checkout")
            self.check_out_button.setMinimumHeight(58)
            self.check_out_button.clicked.connect(
                lambda _checked=False: self.do_attendance("check-out")
            )
            buttons.addWidget(self.check_in_button)
            buttons.addWidget(self.check_out_button)
            action_box.addLayout(buttons)
            layout.addWidget(action_card)

            summary = QGridLayout()
            summary.setHorizontalSpacing(14)
            self.attendance_summary = {}
            summary_tones = ("violet", "mint", "coral", "blue")
            for column, (key, title, icon) in enumerate(
                (
                    ("shift", "Ca làm hôm nay", "◷"),
                    ("check_in", "Giờ vào", "→"),
                    ("check_out", "Giờ ra", "←"),
                    ("worked", "Thời gian làm", "◴"),
                )
            ):
                card = QFrame(objectName="attendanceSummaryCard")
                card.setProperty("tone", summary_tones[column])
                self.add_shadow(card, blur=18, y_offset=4, alpha=22)
                card_box = QVBoxLayout(card)
                card_box.setContentsMargins(18, 16, 18, 16)
                card_box.addWidget(QLabel(f"{icon}  {title}", objectName="summaryTitle"))
                value = QLabel("—", objectName="summaryValue")
                card_box.addWidget(value)
                self.attendance_summary[key] = value
                summary.addWidget(card, 0, column)
            layout.addLayout(summary)

            notice = QFrame(objectName="attendanceNotice")
            notice_box = QHBoxLayout(notice)
            notice_box.setContentsMargins(18, 12, 18, 12)
            notice_icon = QLabel("✓", objectName="noticeIcon")
            self.attendance_notice = QLabel(
                "Thiết bị, kết nối LAN và tọa độ GPS sẽ được xác minh khi chấm công.",
                objectName="noticeText",
            )
            self.attendance_notice.setWordWrap(True)
            notice_box.addWidget(notice_icon)
            notice_box.addWidget(self.attendance_notice, 1)
            layout.addWidget(notice)

            guide = QFrame(objectName="attendanceGuide")
            self.add_shadow(guide, blur=20, y_offset=5, alpha=24)
            guide_box = QVBoxLayout(guide)
            guide_box.setContentsMargins(20, 16, 20, 16)
            guide_box.addWidget(QLabel("Quy trình chấm công an toàn", objectName="sectionTitle"))
            steps = QHBoxLayout()
            steps.setSpacing(12)
            for step_index, (number, title, description) in enumerate(
                (
                ("01", "Kiểm tra ca", "Xác nhận ca làm hôm nay trước khi bắt đầu."),
                ("02", "Xác định GPS", "Cho phép Windows lấy kinh độ, vĩ độ rồi CHECK-IN."),
                ("03", "Kết thúc ca", "CHECK-OUT để lưu thời gian và vị trí rời ca."),
                )
            ):
                step = QFrame(objectName="attendanceStep")
                step.setProperty("tone", ("blue", "mint", "coral")[step_index])
                step_box = QHBoxLayout(step)
                step_box.setContentsMargins(14, 12, 14, 12)
                badge = QLabel(number, objectName="stepNumber")
                text_box = QVBoxLayout()
                text_box.addWidget(QLabel(title, objectName="stepTitle"))
                detail = QLabel(description, objectName="stepText")
                detail.setWordWrap(True)
                text_box.addWidget(detail)
                step_box.addWidget(badge)
                step_box.addLayout(text_box, 1)
                steps.addWidget(step, 1)
            guide_box.addLayout(steps)
            layout.addWidget(guide)
            layout.addStretch()

            def update_clock():
                now = datetime.now()
                self.attendance_clock.setText(now.strftime("%H:%M:%S"))
                self.attendance_date.setText(
                    f"{self.vietnamese_weekday(now.weekday())}, {now.strftime('%d/%m/%Y')}"
                )

            timer = QTimer(page)
            timer.timeout.connect(update_clock)
            update_clock()
            timer.start(1000)
            QTimer.singleShot(120, self.refresh_attendance_panel)
            return self.vertical_page_scroller(page)
        toolbar, controls = QFrame(objectName="toolbar"), QHBoxLayout()
        toolbar.setLayout(controls)
        controls.setContentsMargins(12, 10, 12, 10)
        controls.setSpacing(8)
        self.add_shadow(toolbar, blur=18, y_offset=4, alpha=20)
        table = QTableWidget()
        table.setProperty("page_name", name)
        self.configure_table(table)
        endpoint = self.endpoint_for(name)
        self.add_page_filters(name, table, controls)
        refresh = QPushButton("↻ Làm mới")
        refresh.setProperty("secondary", True)
        refresh.setToolTip("Đặt lại bộ lọc, phân trang và tải dữ liệu mới nhất")
        refresh.clicked.connect(lambda _=False, t=table, e=endpoint: self.refresh_table(t, e))
        controls.addWidget(refresh)
        if self.admin_only:
            export = QPushButton("⇩ Xuất Excel")
            export.setProperty("secondary", True)
            export.clicked.connect(lambda _=False, t=table: self.export_table_excel(t))
            controls.addWidget(export)
        for label, handler in self.actions_for(name, table):
            button = QPushButton(label)
            if label.startswith("Xóa"):
                button.setProperty("danger", True)
            button.clicked.connect(handler)
            controls.addWidget(button)
        controls.addStretch()
        layout.addWidget(self.toolbar_scroller(toolbar))
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
        tones = ("blue", "violet", "mint", "coral", "amber")
        for index, (key, title) in enumerate(definitions):
            card = QFrame(objectName="adminCard")
            card.setProperty("tone", tones[index % len(tones)])
            self.add_shadow(card, blur=20, y_offset=5, alpha=26)
            box = QVBoxLayout(card)
            box.addWidget(QLabel(title))
            value = QLabel("—", objectName="adminMetric")
            box.addWidget(value)
            self.admin_metrics[key] = value
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)

        quick_card = QFrame(objectName="card")
        quick_card.setProperty("tone", "violet")
        self.add_shadow(quick_card, blur=22, y_offset=5, alpha=25)
        quick = QVBoxLayout(quick_card)
        quick.addWidget(QLabel("Tác vụ quản trị nhanh", objectName="emptyTitle"))
        quick.addWidget(
            QLabel(
                "Thiết lập danh mục theo thứ tự: Phòng ban → Chức vụ → Ca làm → Nhân viên → Phân ca.",
                objectName="subtitle",
            )
        )
        buttons = QGridLayout()
        buttons.setHorizontalSpacing(10)
        buttons.setVerticalSpacing(10)
        for index, (label, target) in enumerate((
            ("Thêm nhân viên", "Quản lý nhân viên"),
            ("Phân ca", "Phân ca"),
            ("Duyệt nghỉ phép", "Duyệt nghỉ phép"),
            ("Xử lý cảnh báo", "Cảnh báo"),
            ("Xem bảng lương", "Lương & chuyên cần"),
            ("Xem báo cáo", "Báo cáo"),
        )):
            button = QPushButton(label)
            button.clicked.connect(lambda _=False, page_name=target: self.go_to_page(page_name))
            buttons.addWidget(button, index // 2, index % 2)
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
            search.returnPressed.connect(lambda t=table, e=endpoint: self.apply_table_filters(t, e))
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
        if name == "Phê duyệt thiết bị":
            approval = QComboBox()
            approval.addItem("Đang chờ phê duyệt", False)
            approval.addItem("Tất cả thiết bị", None)
            approval.addItem("Đã phê duyệt", True)
            controls.addWidget(approval)
            filters["approved"] = approval
        if filters:
            apply_filter = QPushButton("Áp dụng bộ lọc")
            apply_filter.setProperty("secondary", True)
            apply_filter.clicked.connect(
                lambda _=False, t=table, e=endpoint: self.apply_table_filters(t, e)
            )
            controls.addWidget(apply_filter)
        self.table_filters[table] = filters

    def safe_get(self, path, **kwargs):
        try:
            data = self.api.request("GET", path, **kwargs)
            if isinstance(data, dict) and isinstance(data.get("items"), list):
                return data["items"]
            return data if isinstance(data, list) else []
        except ApiError as exc:
            QMessageBox.warning(self, "Không tải được dữ liệu liên quan", str(exc))
            return []

    def change_table_page(self, table, endpoint, direction):
        state = self.table_pagination.get(table)
        if not state:
            return
        target = state["page"] + direction
        if 1 <= target <= state["pages"]:
            state["page"] = target
            self.load_table(table, endpoint)

    def apply_table_filters(self, table, endpoint):
        state = self.table_pagination.get(table)
        if state:
            state["page"] = 1
        self.load_table(table, endpoint)

    def refresh_table(self, table, endpoint):
        for key, widget in self.table_filters.get(table, {}).items():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QDateEdit):
                widget.setDate(
                    QDate.currentDate().addMonths(-1) if key == "start" else QDate.currentDate()
                )
        state = self.table_pagination.get(table)
        if state:
            state["page"] = 1
        table.clearSelection()
        self.load_table(table, endpoint)
        self.show_toast("Đã đặt lại bộ lọc và tải dữ liệu mới nhất.")

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
        end_position = page.pos()
        fade = QPropertyAnimation(effect, b"opacity", self)
        fade.setDuration(240)
        fade.setStartValue(0.18)
        fade.setEndValue(1.0)
        fade.setEasingCurve(QEasingCurve.OutCubic)
        slide = QPropertyAnimation(page, b"pos", self)
        slide.setDuration(260)
        slide.setStartValue(end_position + QPoint(0, 14))
        slide.setEndValue(end_position)
        slide.setEasingCurve(QEasingCurve.OutCubic)
        self.page_animation = QParallelAnimationGroup(self)
        self.page_animation.addAnimation(fade)
        self.page_animation.addAnimation(slide)
        self.page_animation.finished.connect(
            lambda current=page, position=end_position: (
                current.move(position),
                current.setGraphicsEffect(None),
            )
        )
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
            "Duyệt làm thêm giờ": "/api/v1/attendance?overtime_status=PENDING",
            "Duyệt điều chỉnh": "/api/v1/attendance/adjustments?status=PENDING",
            "Duyệt nghỉ phép": "/api/v1/leaves?status=PENDING",
            "Loại nghỉ phép": "/api/v1/leave-types",
            "Quỹ phép": "/api/v1/leave-balances",
            "Cảnh báo": "/api/v1/security-alerts?status=OPEN",
            "Xác minh ngẫu nhiên": "/api/v1/random-checks",
            "Phê duyệt thiết bị": "/api/v1/devices",
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
            "Duyệt làm thêm giờ": [
                ("Duyệt OT", lambda: self.review(table, "overtime", True)),
                ("Từ chối OT", lambda: self.review(table, "overtime", False)),
            ],
            "Duyệt nghỉ phép": [
                ("Duyệt", lambda: self.review(table, "leave", True)),
                ("Từ chối", lambda: self.review(table, "leave", False)),
            ],
            "Cảnh báo": [
                ("Xác nhận", lambda: self.review(table, "alert", True)),
                ("Bỏ cảnh báo", lambda: self.review(table, "alert", False)),
            ],
            "Phê duyệt thiết bị": [
                ("Phê duyệt", lambda: self.approve_device(table, True)),
                ("Thu hồi", lambda: self.approve_device(table, False)),
                ("Xóa thiết bị cũ", lambda: self.remove_device(table)),
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
                ("Xóa", lambda: self.delete_record(table, "employees")),
            ],
            "Phòng ban": [
                ("Thêm", lambda: self.create_department(table)),
                ("Sửa", lambda: self.edit_department(table)),
                ("Ngừng", lambda: self.deactivate(table, "departments")),
                ("Xóa", lambda: self.delete_record(table, "departments")),
            ],
            "Chức vụ": [
                ("Thêm", lambda: self.create_position(table)),
                ("Sửa", lambda: self.edit_position(table)),
                ("Ngừng", lambda: self.deactivate(table, "positions")),
                ("Xóa", lambda: self.delete_record(table, "positions")),
            ],
            "Ca làm": [
                ("Thêm", lambda: self.create_shift(table)),
                ("Sửa", lambda: self.edit_shift(table)),
                ("Ngừng", lambda: self.deactivate(table, "shifts")),
                ("Xóa", lambda: self.delete_record(table, "shifts")),
            ],
            "Phân ca": [
                ("Phân ca", lambda: self.assign_shift(table)),
                ("Xóa", lambda: self.delete_record(table, "shift-assignments")),
            ],
            "Quản lý chấm công": [
                ("Xóa", lambda: self.delete_record(table, "attendance")),
            ],
            "Duyệt điều chỉnh": [
                ("Duyệt", lambda: self.review(table, "adjustment", True)),
                ("Từ chối", lambda: self.review(table, "adjustment", False)),
                ("Xóa", lambda: self.delete_record(table, "attendance-adjustments")),
            ],
            "Duyệt nghỉ phép": [
                ("Duyệt", lambda: self.review(table, "leave", True)),
                ("Từ chối", lambda: self.review(table, "leave", False)),
                ("Xóa", lambda: self.delete_record(table, "leaves")),
            ],
            "Loại nghỉ phép": [
                ("Thêm", lambda: self.create_leave_type(table)),
                ("Sửa", lambda: self.edit_leave_type(table)),
                ("Ngừng", lambda: self.deactivate(table, "leave-types")),
                ("Xóa", lambda: self.delete_record(table, "leave-types")),
            ],
            "Quỹ phép": [
                ("Cấp/Cập nhật quỹ", lambda: self.set_leave_balance(table)),
                ("Xóa", lambda: self.delete_record(table, "leave-balances")),
            ],
            "Cảnh báo": [
                ("Xác nhận", lambda: self.review(table, "alert", True)),
                ("Bỏ cảnh báo", lambda: self.review(table, "alert", False)),
                ("Xóa", lambda: self.delete_record(table, "security-alerts")),
            ],
            "Xác minh ngẫu nhiên": [
                ("Xóa", lambda: self.delete_record(table, "random-checks")),
            ],
            "Tài khoản": [
                ("Đổi vai trò", lambda: self.change_role(table)),
                ("Mở khóa", lambda: self.unlock_user(table)),
                ("Xóa", lambda: self.delete_record(table, "users")),
            ],
            "Cấu hình hệ thống": [
                ("Cập nhật", lambda: self.update_setting(table)),
                ("Sao lưu", self.create_backup),
                ("Khôi phục", self.restore_backup),
                ("Xóa", lambda: self.delete_record(table, "settings", "key")),
            ],
        }
        if self.api.role == "ADMIN":
            return (common | admin).get(name, [])
        return common.get(name, [])

    def load_table(self, table, endpoint):
        path, _, query = endpoint.partition("?")
        params = dict(part.split("=", 1) for part in query.split("&") if part)
        if self.employee_portal and path in (
            "/api/v1/attendance",
            "/api/v1/shift-assignments",
            "/api/v1/leaves",
        ):
            params["mine"] = True
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
                if key in (
                    "check_in_latitude",
                    "check_in_longitude",
                    "check_out_latitude",
                    "check_out_longitude",
                ) and value not in (None, ""):
                    text = f"{float(value):.6f}"
                else:
                    text = self.format_cell(value)
                item = QTableWidgetItem(text)
                item.setData(Qt.UserRole, row)
                item.setToolTip(text)
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if key in ("status", "result", "role"):
                    self.color_status_item(item, value)
                elif key in ("check_in_latitude", "check_out_latitude") and value is not None:
                    item.setForeground(QBrush(QColor("#075985")))
                    item.setBackground(QBrush(QColor("#E0F2FE")))
                elif key in ("check_in_longitude", "check_out_longitude") and value is not None:
                    item.setForeground(QBrush(QColor("#166534")))
                    item.setBackground(QBrush(QColor("#DCFCE7")))
                table.setItem(row_idx, col_idx, item)
        table.resizeColumnsToContents()
        if columns:
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            self.fit_table_columns(table, columns)
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
        if index < 0:
            QMessageBox.information(self, "Chọn dữ liệu", "Hãy chọn một dòng trước.")
            return None
        anchor = table.item(index, 0)
        attached_row = anchor.data(Qt.UserRole) if anchor else None
        if isinstance(attached_row, dict):
            return attached_row
        if index >= len(rows):
            QMessageBox.information(self, "Chọn dữ liệu", "Dòng được chọn không còn hợp lệ.")
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

    def create_employee(self, table):
        try:
            departments, positions = (
                self.api.request("GET", "/api/v1/departments", params={"active": True}),
                self.api.request("GET", "/api/v1/positions", params={"active": True}),
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
        departments = self.api.request("GET", "/api/v1/departments", params={"active": True})
        positions = self.api.request("GET", "/api/v1/positions", params={"active": True})
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

    def delete_record(self, table, resource, identifier_field="id"):
        row = self.selected(table)
        if not row:
            return
        identifier = row.get(identifier_field)
        if identifier is None:
            QMessageBox.warning(self, "Không thể xóa", "Dữ liệu đã chọn không có mã hợp lệ.")
            return
        message = (
            "Xóa bản ghi đã chọn?\n\n"
            "Dữ liệu danh mục, nhân viên và tài khoản sẽ được ngừng hoạt động "
            "để giữ lịch sử. Thiết bị và các bản ghi nghiệp vụ khác sẽ bị xóa vĩnh viễn."
        )
        if QMessageBox.question(self, "Xác nhận xóa", message) != QMessageBox.Yes:
            return
        try:
            self.api.request(
                "DELETE",
                f"/api/v1/admin/records/{resource}",
                params={"identifier": str(identifier)},
            )
            self.show_toast("Đã xử lý xóa bản ghi.")
            self.load_table(table, self.endpoint_for(table.property("page_name")))
        except ApiError as exc:
            QMessageBox.warning(self, "Không thể xóa", str(exc))

    def assign_shift(self, table):
        try:
            employees, shifts = (
                self.api.request("GET", "/api/v1/employees", params={"active": True}),
                self.api.request("GET", "/api/v1/shifts", params={"active": True}),
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
            "overtime": f"/api/v1/attendance/{row['id']}/overtime/review",
        }
        reloads = {
            "leave": "/api/v1/leaves?status=PENDING",
            "adjustment": "/api/v1/attendance/adjustments",
            "alert": "/api/v1/security-alerts?status=OPEN",
            "overtime": "/api/v1/attendance?overtime_status=PENDING",
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

    def remove_device(self, table):
        row = self.selected(table)
        if not row:
            return
        message = (
            f"Xóa thiết bị {row.get('device_name') or '#' + str(row['id'])} của "
            f"{row.get('full_name') or 'nhân viên này'}?\n\n"
            "Thiết bị sẽ bị thu hồi quyền chấm công. Nếu đã có lịch sử chấm công, "
            "hệ thống sẽ lưu trữ thiết bị thay vì xóa lịch sử."
        )
        if QMessageBox.question(self, "Xóa thiết bị cũ", message) != QMessageBox.Yes:
            return
        try:
            result = self.api.request("DELETE", f"/api/v1/devices/{row['id']}")
            notice = (
                "Đã lưu trữ và thu hồi thiết bị cũ."
                if result.get("archived")
                else "Đã xóa thiết bị cũ."
            )
            self.show_toast(notice)
            self.load_table(table, "/api/v1/devices")
        except ApiError as exc:
            QMessageBox.warning(self, "Không xóa được thiết bị", str(exc))

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
            self.return_to_login()

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
            self.return_to_login()
        except ApiError as exc:
            QMessageBox.warning(self, "Khôi phục thất bại", str(exc))

    def export_report(self, extension, table=None):
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu báo cáo", f"attendance.{extension}", f"*.{extension}"
        )
        if not path:
            return
        if not path.lower().endswith(f".{extension}"):
            path += f".{extension}"
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
            content = self.api.download(f"/api/v1/reports/attendance.{extension}", params)
            write_bytes_atomic(path, content)
            self.show_toast(f"Đã xuất báo cáo: {path}")
        except (OSError, ApiError) as exc:
            QMessageBox.warning(self, "Không xuất được báo cáo", str(exc))

    def export_table_excel(self, table):
        if table.rowCount() == 0 or table.columnCount() == 0:
            QMessageBox.information(
                self, "Chưa có dữ liệu", "Không có dữ liệu đang hiển thị để xuất file."
            )
            return
        page_name = str(table.property("page_name") or "bao_cao")
        safe_name = "".join(character if character.isalnum() else "_" for character in page_name)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Xuất dữ liệu đang hiển thị",
            f"{safe_name}.xlsx",
            "Excel Workbook (*.xlsx)",
        )
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            headers = [
                table.horizontalHeaderItem(column).text()
                if table.horizontalHeaderItem(column)
                else f"Cột {column + 1}"
                for column in range(table.columnCount())
            ]
            rows = [
                [
                    table.item(row, column).text() if table.item(row, column) else ""
                    for column in range(table.columnCount())
                ]
                for row in range(table.rowCount())
            ]
            content = styled_workbook_bytes(page_name, headers, rows)
            write_bytes_atomic(path, content)
            self.show_toast(f"Đã xuất dữ liệu: {path}")
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Không xuất được file", str(exc))

    def refresh_dashboard(self):
        if hasattr(self, "metrics") or hasattr(self, "admin_metrics"):
            try:
                params = {"mine": True} if self.employee_portal else None
                data = self.api.request("GET", "/api/v1/dashboard", params=params)
                for key, label in getattr(self, "metrics", {}).items():
                    label.setText(str(data.get(key, 0)))
                for key, label in getattr(self, "admin_metrics", {}).items():
                    label.setText(str(data.get(key, 0)))
                if hasattr(self, "chart_values"):
                    for index, key in enumerate(getattr(self, "metrics", {})):
                        self.chart_values.replace(index, float(data.get(key, 0)))
            except ApiError as exc:
                self.connection_state(False)
                if not self._dashboard_error_shown:
                    self._dashboard_error_shown = True
                    self.show_toast(f"Không cập nhật được tổng quan: {exc}", error=True)

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
            if payload.get("type") == "attendance_changed":
                self.refresh_attendance_panel()

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
        if connected:
            self._realtime_ever_connected = True
            self._local_server_shutdown_generation += 1
            self._dashboard_error_shown = False
            self._realtime_error_shown = False
        elif self._realtime_ever_connected and getattr(self.api, "local_server", False):
            self._local_server_shutdown_generation += 1
            generation = self._local_server_shutdown_generation
            QTimer.singleShot(
                2500,
                lambda current=generation: self._close_after_local_server_loss(current),
            )

    def _close_after_local_server_loss(self, generation):
        if (
            generation != self._local_server_shutdown_generation
            or self._session_end_emitted
        ):
            return
        self.connection.setText("● Server nội bộ đã dừng — đang đóng ứng dụng")
        self.close()

    def realtime_error(self, message):
        self.connection_state(False)
        self.connection.setToolTip(message)
        if not self._realtime_error_shown:
            self._realtime_error_shown = True
            self.show_toast(message, error=True)

    def toggle_theme(self):
        self.dark = not self.dark
        if self.admin_only:
            self.setStyleSheet(ADMIN_DARK if self.dark else ADMIN_LIGHT)
        else:
            self.setStyleSheet(DARK if self.dark else LIGHT)
        if hasattr(self, "payroll_data"):
            self.render_payroll_charts(self.payroll_data)

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
        self.return_to_login()

    def return_to_login(self):
        """End the current UI session without terminating the desktop process."""
        self.api.clear_session()
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
