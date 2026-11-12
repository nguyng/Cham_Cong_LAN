import os
import subprocess
import sys
from pathlib import Path


def test_all_ui_pages_and_typed_dialog_construct():
    root = Path(__file__).resolve().parents[1]
    script = r"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QScrollArea, QTableWidget
from app.network.realtime import RealtimeThread
from app.ui.dialogs import Field, FormDialog
from app.ui.login import LoginDialog
from app.ui.main_window import ADMIN_PAGES, EMPLOYEE_PAGES, MANAGER_PAGES, TABLE_COLUMNS, MainWindow

RealtimeThread.start = lambda self: None
class DummyApi:
    role = "ADMIN"
    local_server = True
    device_registration_pending = False
    websocket_url = "ws://127.0.0.1:1/api/v1/ws?token=test"
    def __init__(self):
        self.calls = []
    def clear_session(self):
        self.token = None
        self.role = None
        self.employee_id = None
        self.device_registration_pending = False
    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if path == "/api/v1/dashboard":
            return {"present": 0, "late": 0, "pending_leave": 0, "open_alerts": 0}
        if path in ("/api/v1/attendance", "/api/v1/shift-assignments"):
            return {"items": [], "pagination": {"page": 1, "pages": 1, "total": 0}}
        if path == "/api/v1/payroll":
            return {
                "summary": {"total_payroll": 0, "total_base": 0, "total_bonus": 0, "bonus_recipients": 0, "employee_count": 0},
                "monthly_chart": [{"label": f"T{i:02d}", "base": 0, "bonus": 0} for i in range(1, 13)],
                "top_earners": [],
                "items": [],
                "pagination": {"page": 1, "pages": 1, "total": 0},
            }
        return []

app = QApplication([])
class LoginApi:
    config = {"server_url": "http://127.0.0.1:8000"}
    def __init__(self):
        self.login_args = None
    def login(self, username, password, register_device=True):
        self.login_args = (username, password, register_device)
admin_login_api = LoginApi()
admin_login = LoginDialog(admin_login_api, admin_only=True)
admin_login.username.setText("manage")
admin_login.password.setText("123456")
admin_login.submit()
assert admin_login_api.login_args == ("manage", "123456", False)
admin_login.close()
user_api = DummyApi()
window = MainWindow(user_api)
assert window.page_names == EMPLOYEE_PAGES
assert window.stack.count() == len(EMPLOYEE_PAGES)
labels = {button.text() for button in window.findChildren(QPushButton)}
assert any("CHECK-IN" in label for label in labels)
assert any("CHECK-OUT" in label for label in labels)
assert {"Tạo đơn", "Hủy đơn", "Trang sau", "Đăng xuất"} <= labels
assert "Sao lưu" not in labels
window.refresh_attendance_panel()
mine_calls = [kwargs for _, path, kwargs in user_api.calls if path in ("/api/v1/attendance", "/api/v1/shift-assignments")]
assert mine_calls and all(call["params"]["mine"] is True for call in mine_calls)
assert hasattr(window, "attendance_summary")
assert hasattr(window, "attendance_location")
assert hasattr(window, "show_random_check")
window.resize(900, 600)
window.show_page(EMPLOYEE_PAGES.index("Chấm công"))
window.show()
app.processEvents()
assert window.stack.currentWidget().objectName() == "pageScroll"
assert window.check_in_button.parentWidget() is window.check_out_button.parentWidget()
assert not window.check_in_button.geometry().intersects(window.check_out_button.geometry())
assert window.check_in_button.geometry().bottom() < window.check_out_button.geometry().top()
dialog = FormDialog("Test", [Field("name", "Tên", value="Nhân viên"), Field("days", "Ngày", "int", value=2), Field("quota", "Quỹ", "decimal", value=12.5), Field("paid", "Có lương", "bool", value=True), Field("role", "Vai trò", "choice", options=[("Employee", "EMPLOYEE")])])
assert dialog.values() == {"name": "Nhân viên", "days": 2, "quota": 12.5, "paid": True, "role": "EMPLOYEE"}
dialog.close()
weekdays = FormDialog("Ngày làm", [Field("weekdays", "Ngày", "weekdays", [0, 2, 4])])
assert weekdays.values() == {"weekdays": [0, 2, 4]}
weekdays.close()
admin_window = MainWindow(DummyApi(), admin_only=True)
assert admin_window.stack.count() == len(ADMIN_PAGES)
assert "Phê duyệt thiết bị" in ADMIN_PAGES
assert "Lương & chuyên cần" in ADMIN_PAGES
assert "Thiết bị" not in ADMIN_PAGES
assert ADMIN_PAGES.index("Quản lý chấm công") < ADMIN_PAGES.index("Duyệt nghỉ phép")
assert ADMIN_PAGES.index("Duyệt nghỉ phép") < ADMIN_PAGES.index("Quản lý nhân viên")
assert ADMIN_PAGES.index("Quản lý nhân viên") < ADMIN_PAGES.index("Xác minh ngẫu nhiên")
assert ADMIN_PAGES.index("Xác minh ngẫu nhiên") < ADMIN_PAGES.index("Lương & chuyên cần")
assert ADMIN_PAGES.index("Lương & chuyên cần") < ADMIN_PAGES.index("Cấu hình hệ thống")
admin_sections = {
    label.text() for label in admin_window.findChildren(QLabel, "navSection")
}
assert {
    "TỔNG QUAN",
    "CHẤM CÔNG & CA LÀM",
    "NGHỈ PHÉP",
    "NHÂN SỰ & THIẾT BỊ",
    "GIÁM SÁT & AN NINH",
    "LƯƠNG & BÁO CÁO",
    "HỆ THỐNG",
} <= admin_sections
assert "Trung tâm quản trị" in admin_window.windowTitle()
assert hasattr(admin_window, "admin_metrics")
attendance_columns = next(
    columns
    for page, columns in TABLE_COLUMNS.items()
    if "check_in_at" in columns and "employee_code" in columns
)
assert "check_in_latitude" in attendance_columns
assert "check_out_longitude" in attendance_columns

# Sorting must not detach the visual row from the record used by edit/delete actions.
sorted_table = QTableWidget()
sorted_table.setProperty("page_name", "Quản lý nhân viên")
admin_window.configure_table(sorted_table)
admin_window.table_rows[sorted_table] = []
admin_window.table_filters[sorted_table] = {}
sort_rows = [
    {"id": 1, "employee_code": "A", "full_name": "Dòng một"},
    {"id": 2, "employee_code": "Z", "full_name": "Dòng hai"},
]
original_request = admin_window.api.request
admin_window.api.request = lambda *args, **kwargs: sort_rows
admin_window.load_table(sorted_table, "/api/v1/employees")
sorted_table.sortItems(0, Qt.DescendingOrder)
sorted_table.selectRow(0)
assert sorted_table.item(0, 0).text() == "2"
assert admin_window.selected(sorted_table)["id"] == 2
admin_window.api.request = original_request
assert "check_in_ip" in attendance_columns
assert "check_in_location_source" in attendance_columns
assert "qlineargradient" in admin_window.styleSheet()
assert "QTableWidget::item:selected" in admin_window.styleSheet()
admin_window.toggle_theme()
assert admin_window.dark is True
admin_window.toggle_theme()
assert admin_window.dark is False
admin_window.show_page(1)
app.processEvents()
assert admin_window.stack.currentIndex() == 1
admin_labels = {button.text() for button in admin_window.findChildren(QPushButton)}
assert {
    "Thêm",
    "Sửa",
    "Xóa",
    "Xuất Excel",
    "Sao lưu",
    "Khôi phục",
    "Gửi Random Check",
    "Xuất Excel",
    "Làm mới",
    "Cập nhật mức lương",
} <= admin_labels
assert "Xuất CSV" not in admin_labels
assert "Xuất file" not in admin_labels
assert "Reset" not in admin_labels
department_table = next(table for table in admin_window.findChildren(QTableWidget) if table.property("page_name") == "Phòng ban")
admin_window.load_table(department_table, "/api/v1/departments")
assert department_table.columnCount() >= 5
assert department_table.horizontalHeader().height() >= 40
assert department_table.verticalHeader().defaultSectionSize() >= 40
assert not admin_window.empty_states[department_table].isHidden()
admin_logout_events = []
admin_window.session_ended.connect(lambda logged_out: admin_logout_events.append(logged_out))
admin_window.resize(900, 600)
admin_window.show()
app.processEvents()
for button in admin_window.findChildren(QPushButton):
    assert not button.icon().isNull(), button.text()
    assert button.minimumHeight() >= 40, button.text()
    assert button.minimumWidth() >= button.fontMetrics().horizontalAdvance(button.text()) + 40
admin_nav_scroll = admin_window.findChild(QScrollArea, "navScroll")
assert admin_nav_scroll is not None
assert admin_nav_scroll.verticalScrollBar().maximum() > 0
toolbar_scroll = admin_window.stack.currentWidget().findChild(QScrollArea, "toolbarScroll")
assert toolbar_scroll is not None
assert toolbar_scroll.geometry().right() <= toolbar_scroll.parentWidget().contentsRect().right()
assert toolbar_scroll.horizontalScrollBar().maximum() > 0
admin_window.logout()
assert admin_logout_events == [True]
assert not admin_window.isVisible()
class ManagerApi(DummyApi):
    role = "MANAGER"
manager_user_window = MainWindow(ManagerApi())
manager_admin_window = MainWindow(ManagerApi(), admin_only=True)
assert manager_user_window.page_names == EMPLOYEE_PAGES
assert manager_admin_window.page_names == MANAGER_PAGES
assert MANAGER_PAGES.index("Quản lý chấm công") < MANAGER_PAGES.index("Duyệt nghỉ phép")
assert MANAGER_PAGES.index("Duyệt nghỉ phép") < MANAGER_PAGES.index("Quản lý nhân viên")
assert MANAGER_PAGES.index("Quản lý nhân viên") < MANAGER_PAGES.index("Xác minh ngẫu nhiên")
assert MANAGER_PAGES.index("Xác minh ngẫu nhiên") < MANAGER_PAGES.index("Lương & chuyên cần")
manager_admin_labels = {button.text() for button in manager_admin_window.findChildren(QPushButton)}
assert "Xóa" not in manager_admin_labels
assert "Phê duyệt thiết bị" in MANAGER_PAGES
assert "Lương & chuyên cần" in MANAGER_PAGES
assert {"Phê duyệt", "Thu hồi", "Xóa thiết bị cũ", "Xuất Excel", "Làm mới"} <= manager_admin_labels
server_stop_events = []
manager_admin_window.session_ended.connect(
    lambda logged_out: server_stop_events.append(logged_out)
)
manager_admin_window.connection_state(True)
manager_admin_window.connection_state(False)
manager_admin_window._close_after_local_server_loss(
    manager_admin_window._local_server_shutdown_generation
)
assert server_stop_events == [False]
manager_user_window.close()
logout_events = []
window.session_ended.connect(lambda logged_out: logout_events.append(logged_out))
window.show()
app.processEvents()
window.logout()
assert logout_events == [True]
assert not window.isVisible()
print("UI_SMOKE_OK")
"""
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONPATH"] = str(root / "client")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "UI_SMOKE_OK" in result.stdout


def test_manager_logout_reopens_login_instead_of_quitting():
    root = Path(__file__).resolve().parents[1]
    script = r"""
from PySide6.QtCore import QTimer
from app import main as app_main

login_count = {"value": 0}

class DummyApi:
    role = None
    employee_id = None
    token = None
    def __init__(self, _config_path):
        pass

class DummyLogin:
    Accepted = 1
    def __init__(self, api, admin_only=False):
        self.api = api
        self.admin_only = admin_only
    def show(self):
        pass
    def raise_(self):
        pass
    def activateWindow(self):
        pass
    def exec(self):
        login_count["value"] += 1
        if login_count["value"] == 1:
            self.api.role = "MANAGER"
            return self.Accepted
        return 0
    def deleteLater(self):
        pass

class DummySignal:
    def connect(self, callback):
        self.callback = callback
    def emit(self, value):
        self.callback(value)

class DummyWindow:
    def __init__(self, api, admin_only=False):
        assert api.role == "MANAGER"
        assert admin_only is True
        self.session_ended = DummySignal()
    def show(self):
        QTimer.singleShot(0, lambda: self.session_ended.emit(True))
    def deleteLater(self):
        pass

app_main.ApiClient = DummyApi
app_main.LoginDialog = DummyLogin
app_main.MainWindow = DummyWindow
result = app_main.main(admin_only=True)
assert result == 0
assert login_count["value"] == 2
print("MANAGER_LOGOUT_RELOGIN_OK")
"""
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONPATH"] = str(root / "client")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "MANAGER_LOGOUT_RELOGIN_OK" in result.stdout
