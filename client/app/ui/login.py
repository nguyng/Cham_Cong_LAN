from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from app.network.api import ApiError


class LoginDialog(QDialog):
    def __init__(self, api, admin_only=False):
        super().__init__()
        self.api = api
        self.admin_only = admin_only
        self.setObjectName("adminLogin" if admin_only else "employeeLogin")
        self.setWindowTitle(
            "Đăng nhập quản trị — LAN Attendance"
            if admin_only
            else "Đăng nhập nhân viên — LAN Attendance"
        )
        self.setMinimumSize(480, 390)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(55, 45, 55, 45)
        title = QLabel("ADMIN CONTROL CENTER" if admin_only else "LAN Attendance")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        subtitle = QLabel(
            "Cổng quản trị hệ thống — chỉ dành cho Admin/Manager"
            if admin_only
            else "Cổng chấm công dành cho nhân viên"
        )
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        form = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        form.addRow("Tên đăng nhập", self.username)
        form.addRow("Mật khẩu", self.password)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        discover = QPushButton("Tìm Server")
        login = QPushButton("Đăng nhập")
        discover.clicked.connect(self.find_server)
        login.clicked.connect(self.submit)
        self.password.returnPressed.connect(self.submit)
        buttons.addWidget(discover)
        buttons.addWidget(login)
        layout.addLayout(buttons)
        self.server = QLabel(self.api.config["server_url"])
        self.server.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.server)

    def find_server(self):
        try:
            url = self.api.discover()
        except (ApiError, OSError, ValueError) as exc:
            QMessageBox.warning(self, "Không thể tìm Server", str(exc))
            return
        if url:
            try:
                self.api.set_server(url)
            except ApiError as exc:
                QMessageBox.warning(self, "Không thể lưu Server", str(exc))
                return
            self.server.setText(url)
        else:
            QMessageBox.warning(
                self,
                "Không tìm thấy Server",
                "Không tìm thấy Server trong mạng LAN.\n\n"
                "Hãy kiểm tra Server đang chạy, máy đang cùng mạng LAN và Firewall cho phép UDP.",
            )

    def submit(self):
        username = self.username.text().strip()
        password = self.password.text()
        if not username or not password:
            QMessageBox.warning(
                self,
                "Thiếu thông tin đăng nhập",
                "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.",
            )
            (self.username if not username else self.password).setFocus()
            return
        try:
            self.api.login(
                username,
                password,
                register_device=not self.admin_only,
            )
        except ApiError as exc:
            QMessageBox.critical(self, "Đăng nhập thất bại", str(exc))
            return
        self.accept()
