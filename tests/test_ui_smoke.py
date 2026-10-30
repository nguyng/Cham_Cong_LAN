import os
import subprocess
import sys
from pathlib import Path


def test_all_ui_pages_and_typed_dialog_construct():
    root = Path(__file__).resolve().parents[1]
    script = r"""
from PySide6.QtWidgets import QApplication, QPushButton, QTableWidget
from app.network.realtime import RealtimeThread
from app.ui.dialogs import Field, FormDialog
from app.ui.main_window import ADMIN_PAGES, EMPLOYEE_PAGES, MainWindow

RealtimeThread.start = lambda self: None
class DummyApi:
    role = "ADMIN"
    device_registration_pending = False
    websocket_url = "ws://127.0.0.1:1/api/v1/ws?token=test"
    def request(self, method, path, **kwargs):
        if path == "/api/v1/dashboard":
            return {"present": 0, "late": 0, "pending_leave": 0, "open_alerts": 0}
        return []

app = QApplication([])
window = MainWindow(DummyApi())
assert window.stack.count() == len(EMPLOYEE_PAGES) + len(ADMIN_PAGES)
labels = {button.text() for button in window.findChildren(QPushButton)}
assert {"CHECK-IN", "CHECK-OUT", "Thêm", "Sửa", "Tạo đơn", "Hủy đơn", "Trang sau ›", "Xuất Excel", "Sao lưu", "Khôi phục", "Gửi Random Check", "Đăng xuất"} <= labels
assert hasattr(window, "show_random_check")
dialog = FormDialog("Test", [Field("name", "Tên", value="Nhân viên"), Field("days", "Ngày", "int", value=2), Field("quota", "Quỹ", "decimal", value=12.5), Field("paid", "Có lương", "bool", value=True), Field("role", "Vai trò", "choice", options=[("Employee", "EMPLOYEE")])])
assert dialog.values() == {"name": "Nhân viên", "days": 2, "quota": 12.5, "paid": True, "role": "EMPLOYEE"}
dialog.close()
weekdays = FormDialog("Ngày làm", [Field("weekdays", "Ngày", "weekdays", [0, 2, 4])])
assert weekdays.values() == {"weekdays": [0, 2, 4]}
weekdays.close()
admin_window = MainWindow(DummyApi(), admin_only=True)
assert admin_window.stack.count() == len(ADMIN_PAGES)
assert "Trung tâm quản trị" in admin_window.windowTitle()
assert hasattr(admin_window, "admin_metrics")
department_table = next(table for table in admin_window.findChildren(QTableWidget) if table.property("page_name") == "Phòng ban")
admin_window.load_table(department_table, "/api/v1/departments")
assert department_table.columnCount() >= 5
assert not admin_window.empty_states[department_table].isHidden()
admin_logout_events = []
admin_window.session_ended.connect(lambda logged_out: admin_logout_events.append(logged_out))
admin_window.show()
app.processEvents()
admin_window.logout()
assert admin_logout_events == [True]
assert not admin_window.isVisible()
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
