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
assert {"CHECK-IN", "CHECK-OUT", "Thêm", "Sửa", "Tạo đơn", "Xuất Excel", "Sao lưu", "Khôi phục", "Gửi Random Check", "Đăng xuất"} <= labels
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
admin_window.close()
window.close()
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
