import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen

from app.network.api import ApiClient, ApiError
from app.ui.login import LoginDialog
from app.ui.main_window import MainWindow
from app.ui.style import ADMIN_LIGHT, LIGHT


def install_exception_handler(application: QApplication):
    """Show unexpected GUI callback failures instead of silently closing the app."""
    original_hook = sys.excepthook

    def handle_exception(exc_type, exc_value, exc_traceback):
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(details, file=sys.stderr)
        try:
            if not application.closingDown():
                dialog = QMessageBox()
                dialog.setIcon(QMessageBox.Critical)
                dialog.setWindowTitle("Lỗi chương trình")
                dialog.setText("Chương trình gặp lỗi ngoài dự kiến nhưng vẫn đang được giữ mở.")
                dialog.setInformativeText(
                    "Vui lòng chụp lại cảnh báo này và thử thao tác lại. "
                    "Nếu lỗi tiếp tục xảy ra, hãy kiểm tra cửa sổ Server."
                )
                dialog.setDetailedText(details)
                dialog.exec()
        except Exception:
            original_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception


def main(admin_only: bool = False):
    application = QApplication(sys.argv)
    install_exception_handler(application)
    application.setQuitOnLastWindowClosed(False)
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
    try:
        api = ApiClient(root / "config.json")
    except (ApiError, OSError, ValueError) as exc:
        QMessageBox.critical(
            None,
            "Không thể khởi động chương trình",
            f"Không tải được cấu hình kết nối:\n{exc}\n\n"
            "Hãy kiểm tra config.json hoặc khôi phục từ config.example.json.",
        )
        return 1
    active_windows = {"login": None, "main": None}

    def end_session(logged_out, window):
        if active_windows["main"] is not window:
            return
        active_windows["main"] = None
        window.deleteLater()
        if logged_out:
            QTimer.singleShot(0, show_login)
        else:
            application.quit()

    def show_login():
        login = LoginDialog(api, admin_only=admin_only)
        active_windows["login"] = login
        if login.exec() != LoginDialog.Accepted:
            active_windows["login"] = None
            login.deleteLater()
            application.quit()
            return
        active_windows["login"] = None
        login.deleteLater()
        if admin_only and api.role not in ("ADMIN", "MANAGER"):
            logout_warning = ""
            try:
                api.request("POST", "/api/v1/auth/logout")
            except ApiError as exc:
                # The local session must still be cleared when the Server disconnects.
                logout_warning = f"\n\nKhông thể thu hồi phiên trên Server: {exc}"
            QMessageBox.critical(
                None,
                "Từ chối truy cập",
                "Ứng dụng quản trị yêu cầu quyền Manager hoặc Admin." + logout_warning,
            )
            api.clear_session()
            QTimer.singleShot(0, show_login)
            return

        window = MainWindow(api, admin_only=admin_only)
        active_windows["main"] = window
        window.session_ended.connect(
            lambda logged_out, current=window: end_session(logged_out, current)
        )
        window.show()

    QTimer.singleShot(0, show_login)
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
