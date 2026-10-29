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
        url = self.api.discover()
        if url:
            self.api.set_server(url)
            self.server.setText(url)
        else:
            QMessageBox.warning(self, "Khám phá Server", "Không tìm thấy Server trong mạng LAN.")

    def submit(self):
        try:
            self.api.login(self.username.text().strip(), self.password.text())
        except ApiError as exc:
            QMessageBox.critical(self, "Đăng nhập thất bại", str(exc))
            return
        self.accept()
