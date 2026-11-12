from datetime import datetime

from PySide6.QtCharts import QBarCategoryAxis, QBarSeries, QBarSet, QChart, QChartView, QValueAxis
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.network.api import ApiError
from app.ui.catalog import COLUMN_LABELS, TABLE_COLUMNS
from app.ui.dialogs import Field


class PayrollUiMixin:
    """Payroll dashboard, charts and profile actions for Admin/Manager."""
    def build_payroll_page(self, layout):
        toolbar = QFrame(objectName="payrollToolbar")
        toolbar_box = QVBoxLayout(toolbar)
        toolbar_box.setContentsMargins(14, 11, 14, 11)
        toolbar_box.setSpacing(8)
        filters = QHBoxLayout()
        filters.setSpacing(8)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        filters.addWidget(QLabel("Kỳ lương"))
        self.add_shadow(toolbar, blur=18, y_offset=4, alpha=22)

        self.payroll_year = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year, current_year - 6, -1):
            self.payroll_year.addItem(f"Năm {year}", year)
        filters.addWidget(self.payroll_year)

        self.payroll_month = QComboBox()
        self.payroll_month.addItem("Cả năm", None)
        for month in range(1, 13):
            self.payroll_month.addItem(f"Tháng {month:02d}", month)
        filters.addWidget(self.payroll_month)

        self.payroll_employee = QComboBox()
        self.payroll_employee.addItem("Tất cả nhân viên", None)
        for employee in self.safe_get("/api/v1/employees", params={"active": True}):
            self.payroll_employee.addItem(
                f"{employee['employee_code']} — {employee['full_name']}", employee["id"]
            )
        filters.addWidget(self.payroll_employee, 1)

        self.payroll_department = None
        if self.api.role == "ADMIN":
            self.payroll_department = QComboBox()
            self.payroll_department.addItem("Tất cả phòng ban", None)
            for department in self.safe_get("/api/v1/departments"):
                self.payroll_department.addItem(department["name"], department["id"])
            filters.addWidget(self.payroll_department, 1)
        filters.addStretch()

        apply_button = QPushButton("Áp dụng")
        apply_button.clicked.connect(lambda _=False: self.load_payroll(reset_page=True))
        actions.addWidget(apply_button)
        refresh_button = QPushButton("↻ Làm mới")
        refresh_button.setProperty("secondary", True)
        refresh_button.clicked.connect(self.reset_payroll)
        actions.addWidget(refresh_button)
        update_button = QPushButton("Cập nhật mức lương")
        update_button.setProperty("payrollAction", True)
        update_button.clicked.connect(self.update_payroll_profile)
        actions.addWidget(update_button)
        export_button = QPushButton("⇩ Xuất Excel")
        export_button.setProperty("secondary", True)
        export_button.clicked.connect(lambda _=False: self.export_table_excel(self.payroll_table))
        actions.addWidget(export_button)
        actions.addStretch()
        toolbar_box.addLayout(filters)
        toolbar_box.addLayout(actions)
        layout.addWidget(self.toolbar_scroller(toolbar, height=122))

        metric_grid = QGridLayout()
        metric_grid.setHorizontalSpacing(12)
        self.payroll_metrics = {}
        metric_definitions = (
            ("total_payroll", "Tổng thực nhận", "teal"),
            ("total_base", "Lương theo ngày công", "blue"),
            ("total_bonus", "Thưởng chuyên cần", "orange"),
            ("total_overtime", "Tiền làm thêm", "blue"),
            ("bonus_recipients", "Nhân viên đạt thưởng", "violet"),
        )
        for column, (key, title, tone) in enumerate(metric_definitions):
            card = QFrame(objectName="payrollMetricCard")
            card.setProperty("tone", tone)
            card_box = QVBoxLayout(card)
            card_box.setContentsMargins(17, 13, 17, 13)
            metric_label = QLabel(title, objectName="payrollMetricLabel")
            metric_label.setWordWrap(True)
            card_box.addWidget(metric_label)
            value = QLabel("—", objectName="payrollMetricValue")
            card_box.addWidget(value)
            self.payroll_metrics[key] = value
            metric_grid.addWidget(card, 0, column)
            self.add_shadow(card, blur=18, y_offset=4, alpha=24)
        layout.addLayout(metric_grid)

        charts = QHBoxLayout()
        charts.setSpacing(12)
        monthly_card = QFrame(objectName="payrollChartCard")
        monthly_box = QVBoxLayout(monthly_card)
        monthly_box.setContentsMargins(15, 12, 15, 12)
        monthly_box.addWidget(QLabel("Xu hướng lương theo tháng", objectName="chartTitle"))
        self.payroll_monthly_chart = QChartView()
        self.payroll_monthly_chart.setRenderHint(QPainter.Antialiasing)
        self.payroll_monthly_chart.setMinimumHeight(215)
        monthly_box.addWidget(self.payroll_monthly_chart)
        charts.addWidget(monthly_card, 3)
        self.add_shadow(monthly_card, blur=18, y_offset=4, alpha=22)

        top_card = QFrame(objectName="payrollChartCard")
        top_box = QVBoxLayout(top_card)
        top_box.setContentsMargins(15, 12, 15, 12)
        top_box.addWidget(QLabel("Nhân viên có tổng thực nhận cao", objectName="chartTitle"))
        self.payroll_top_chart = QChartView()
        self.payroll_top_chart.setRenderHint(QPainter.Antialiasing)
        self.payroll_top_chart.setMinimumHeight(215)
        top_box.addWidget(self.payroll_top_chart)
        charts.addWidget(top_card, 2)
        self.add_shadow(top_card, blur=18, y_offset=4, alpha=22)
        layout.addLayout(charts)

        policy = QLabel(
            "Cách tính: lương tháng được phân bổ theo ngày đã phân ca; phép hưởng lương "
            "được tính công. Thưởng chuyên cần áp dụng khi đủ công và không đi muộn, "
            "về sớm hoặc có chấm công bất thường. "
            "Thời gian làm thêm chỉ được tính tiền sau khi Admin/Manager phê duyệt.",
            objectName="payrollPolicy",
        )
        policy.setWordWrap(True)
        layout.addWidget(policy)

        table = QTableWidget()
        table.setProperty("page_name", "Lương & chuyên cần")
        self.configure_table(table)
        table.setMinimumHeight(190)
        self.payroll_table = table
        self.table_rows[table] = []
        layout.addWidget(table, 1)

        pagination_bar = QHBoxLayout()
        self.payroll_previous = QPushButton("‹ Trang trước")
        self.payroll_previous.setProperty("secondary", True)
        self.payroll_previous.clicked.connect(lambda _=False: self.change_payroll_page(-1))
        self.payroll_page_label = QLabel("Trang 1/1 — 0 nhân viên")
        self.payroll_next = QPushButton("Trang sau ›")
        self.payroll_next.setProperty("secondary", True)
        self.payroll_next.clicked.connect(lambda _=False: self.change_payroll_page(1))
        self.payroll_page = 1
        self.payroll_pages = 1
        pagination_bar.addStretch()
        pagination_bar.addWidget(self.payroll_previous)
        pagination_bar.addWidget(self.payroll_page_label)
        pagination_bar.addWidget(self.payroll_next)
        layout.addLayout(pagination_bar)
        QTimer.singleShot(120, self.load_payroll)

    @staticmethod
    def format_money(value):
        try:
            return f"{float(value):,.0f} ₫".replace(",", ".")
        except (TypeError, ValueError):
            return "0 ₫"

    def payroll_params(self):
        params = {
            "year": self.payroll_year.currentData(),
            "page": self.payroll_page,
            "page_size": 50,
        }
        for key, widget in (
            ("month", self.payroll_month),
            ("employee_id", self.payroll_employee),
            ("department_id", self.payroll_department),
        ):
            if widget is not None and widget.currentData() is not None:
                params[key] = widget.currentData()
        return params

    def reset_payroll(self):
        self.payroll_year.setCurrentIndex(0)
        self.payroll_month.setCurrentIndex(0)
        self.payroll_employee.setCurrentIndex(0)
        if self.payroll_department is not None:
            self.payroll_department.setCurrentIndex(0)
        self.payroll_table.clearSelection()
        self.load_payroll(reset_page=True)
        self.show_toast("Đã đặt lại bộ lọc và cập nhật bảng lương.")

    def change_payroll_page(self, direction):
        target = self.payroll_page + direction
        if 1 <= target <= self.payroll_pages:
            self.payroll_page = target
            self.load_payroll()

    def load_payroll(self, reset_page=False):
        if reset_page:
            self.payroll_page = 1
        try:
            data = self.api.request("GET", "/api/v1/payroll", params=self.payroll_params())
        except ApiError as exc:
            QMessageBox.warning(self, "Không tính được bảng lương", str(exc))
            return
        if not isinstance(data, dict):
            QMessageBox.warning(self, "Dữ liệu không hợp lệ", "Server trả về bảng lương không hợp lệ.")
            return
        self.payroll_data = data
        summary = data.get("summary", {})
        self.payroll_metrics["total_payroll"].setText(
            self.format_money(summary.get("total_payroll", 0))
        )
        self.payroll_metrics["total_base"].setText(
            self.format_money(summary.get("total_base", 0))
        )
        self.payroll_metrics["total_bonus"].setText(
            self.format_money(summary.get("total_bonus", 0))
        )
        self.payroll_metrics["total_overtime"].setText(
            self.format_money(summary.get("total_overtime", 0))
        )
        self.payroll_metrics["bonus_recipients"].setText(
            f"{summary.get('bonus_recipients', 0)} / {summary.get('employee_count', 0)}"
        )
        metadata = data.get("pagination", {})
        self.payroll_page = int(metadata.get("page", 1))
        self.payroll_pages = int(metadata.get("pages", 1))
        total = int(metadata.get("total", len(data.get("items", []))))
        self.payroll_page_label.setText(
            f"Trang {self.payroll_page}/{self.payroll_pages} — {total} nhân viên"
        )
        self.payroll_previous.setEnabled(self.payroll_page > 1)
        self.payroll_next.setEnabled(self.payroll_page < self.payroll_pages)
        self.render_payroll_charts(data)
        self.render_payroll_table(data.get("items", []))

    def payroll_chart(self, title, categories, sets, y_title="Triệu đồng"):
        chart = QChart()
        chart.setTitle(title)
        chart.setTitleFont(QFont("Segoe UI", 11, QFont.DemiBold))
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.setBackgroundVisible(False)
        series = QBarSeries()
        maximum = 0.0
        for label, values, color in sets:
            bar_set = QBarSet(label)
            bar_set.setColor(QColor(color))
            bar_set.setBorderColor(QColor(color).darker(115))
            scaled_values = [float(value) / 1_000_000 for value in values]
            maximum = max(maximum, max(scaled_values, default=0))
            bar_set.append(scaled_values)
            series.append(bar_set)
        chart.addSeries(series)
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_y = QValueAxis()
        axis_y.setTitleText(y_title)
        axis_y.setLabelFormat("%.1f")
        axis_y.setRange(0, max(1, maximum * 1.18))
        axis_y.setTickCount(5)
        axis_font = QFont("Segoe UI", 8)
        axis_x.setLabelsFont(axis_font)
        axis_y.setLabelsFont(axis_font)
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        text_color = QColor("#E5E7EB" if self.dark else "#334155")
        chart.setTitleBrush(QBrush(text_color))
        chart.legend().setLabelColor(text_color)
        chart.legend().setFont(QFont("Segoe UI", 9, QFont.Medium))
        axis_x.setLabelsColor(text_color)
        axis_y.setLabelsColor(text_color)
        axis_y.setTitleBrush(QBrush(text_color))
        grid_pen = QPen(QColor("#334155" if self.dark else "#E2E8F0"))
        axis_y.setGridLinePen(grid_pen)
        return chart

    def render_payroll_charts(self, data):
        monthly = data.get("monthly_chart", [])
        self.payroll_monthly_chart.setChart(
            self.payroll_chart(
                "Lương và thưởng trong năm",
                [item.get("label", "") for item in monthly],
                (
                    ("Lương theo công", [item.get("base", 0) for item in monthly], "#0EA5E9"),
                    ("Thưởng chuyên cần", [item.get("bonus", 0) for item in monthly], "#F97316"),
                    ("Tiền làm thêm", [item.get("overtime", 0) for item in monthly], "#8B5CF6"),
                ),
            )
        )
        top = data.get("top_earners", [])
        self.payroll_top_chart.setChart(
            self.payroll_chart(
                "Top thực nhận trong kỳ",
                [item.get("label", "") for item in top] or ["Chưa có"],
                (
                    (
                        "Tổng thực nhận",
                        [item.get("total", 0) for item in top] or [0],
                        "#8B5CF6",
                    ),
                ),
            )
        )

    def render_payroll_table(self, rows):
        rows = [row for row in rows if isinstance(row, dict)]
        self.table_rows[self.payroll_table] = rows
        columns = TABLE_COLUMNS["Lương & chuyên cần"]
        table = self.payroll_table
        table.setSortingEnabled(False)
        table.clearContents()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([COLUMN_LABELS.get(key, key) for key in columns])
        table.setRowCount(len(rows))
        money_columns = {
            "base_salary",
            "attendance_bonus",
            "base_earned",
            "bonus_earned",
            "overtime_earned",
            "total_salary",
        }
        for row_index, row in enumerate(rows):
            for column_index, key in enumerate(columns):
                value = row.get(key, "")
                if key in money_columns:
                    text = self.format_money(value)
                elif key == "attendance_rate":
                    text = f"{float(value or 0):.1f}%"
                else:
                    text = self.format_cell(value)
                item = QTableWidgetItem(text)
                item.setData(Qt.UserRole, row)
                item.setToolTip(text)
                if key in money_columns or isinstance(value, (int, float)):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if key == "base_earned":
                    item.setForeground(QBrush(QColor("#0369A1")))
                    item.setBackground(QBrush(QColor("#E0F2FE")))
                elif key == "bonus_earned":
                    item.setForeground(QBrush(QColor("#C2410C")))
                    item.setBackground(QBrush(QColor("#FFEDD5")))
                elif key == "overtime_earned":
                    item.setForeground(QBrush(QColor("#6D28D9")))
                    item.setBackground(QBrush(QColor("#EDE9FE")))
                elif key == "total_salary":
                    item.setForeground(QBrush(QColor("#0F766E")))
                    item.setBackground(QBrush(QColor("#CCFBF1")))
                elif key == "absence_days" and value:
                    item.setForeground(QBrush(QColor("#B91C1C")))
                    item.setBackground(QBrush(QColor("#FEE2E2")))
                elif key == "bonus_status":
                    achieved = value == "Đạt thưởng" or str(value).startswith("1/")
                    item.setForeground(QBrush(QColor("#166534" if achieved else "#92400E")))
                    item.setBackground(QBrush(QColor("#DCFCE7" if achieved else "#FEF3C7")))
                table.setItem(row_index, column_index, item)
        table.resizeColumnsToContents()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.fit_table_columns(table, columns)
        table.setSortingEnabled(bool(rows))

    def update_payroll_profile(self):
        row = self.selected(self.payroll_table)
        if not row:
            return
        fields = [
            Field("base_salary", "Lương cơ bản/tháng (VNĐ)", "decimal", row.get("base_salary")),
            Field(
                "attendance_bonus",
                "Thưởng chuyên cần/tháng (VNĐ)",
                "decimal",
                row.get("attendance_bonus"),
            ),
            Field(
                "overtime_multiplier",
                "Hệ số tiền làm thêm (1.0–5.0)",
                "decimal",
                row.get("overtime_multiplier", 1.5),
            ),
        ]
        if self.submit_dialog(
            f"Cập nhật lương — {row.get('full_name')}",
            fields,
            "PUT",
            f"/api/v1/payroll/profiles/{row['employee_id']}",
        ):
            self.load_payroll()
