import sys
from pathlib import Path

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from app.network.api import ApiClient
from app.ui.login import LoginDialog
from app.ui.main_window import MainWindow
from app.ui.style import ADMIN_LIGHT, LIGHT


def main(admin_only: bool = False):
    application = QApplication(sys.argv)
    application.setApplicationName("LAN Attendance Admin" if admin_only else "LAN Attendance")
    application.setStyleSheet(ADMIN_LIGHT if admin_only else LIGHT)
    pixmap = QPixmap(680, 360)
    pixmap.fill(QColor("#071426" if admin_only else "#111827"))
    painter = QPainter(pixmap)
    painter.setPen(QColor("#F8FAFC"))
    painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
    painter.drawText(
        pixmap.rect(),
        Qt.AlignCenter,
        "ADMIN CONTROL CENTER" if admin_only else "LAN ATTENDANCE",
    )
    painter.setPen(QColor("#22D3EE" if admin_only else "#60A5FA"))
    painter.setFont(QFont("Segoe UI", 11))
    painter.drawText(
        0,
        225,
        680,
        40,
        Qt.AlignCenter,
        "Đang mở trung tâm quản trị…" if admin_only else "Đang khởi tạo kết nối nội bộ an toàn…",
    )
    painter.end()
    splash = QSplashScreen(pixmap)
    splash.show()
    loop = QEventLoop()
    QTimer.singleShot(800, loop.quit)
    loop.exec()
    splash.close()
    root = (
        Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parents[1]
    )
    api = ApiClient(root / "config.json")
    login = LoginDialog(api, admin_only=admin_only)
    if login.exec() != LoginDialog.Accepted:
        return 0
    if admin_only and api.role not in ("ADMIN", "MANAGER"):
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.critical(
            None, "Từ chối truy cập", "Ứng dụng quản trị yêu cầu quyền Manager hoặc Admin."
        )
        return 1
    window = MainWindow(api, admin_only=admin_only)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
