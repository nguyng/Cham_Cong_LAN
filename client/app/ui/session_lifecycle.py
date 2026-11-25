from datetime import UTC, datetime

from PySide6.QtCharts import QChart
from PySide6.QtCore import QPropertyAnimation, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
)

from app.network.api import ApiError
from app.ui.icons import decorate_button
from app.ui.style import ADMIN_DARK, ADMIN_LIGHT, DARK, LIGHT


class SessionLifecycleMixin:
    """Dashboard refresh, realtime events and desktop-session lifecycle."""

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
        self.connection.setText("● Máy chủ nội bộ đã dừng — đang đóng ứng dụng")
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
        if hasattr(self, "theme_button"):
            target = "sáng" if self.dark else "tối"
            self.theme_button.setText(f"Chế độ {target}")
            self.theme_button.setToolTip(f"Chuyển sang chế độ {target}")
            decorate_button(self.theme_button)
        if hasattr(self, "dashboard_chart"):
            self.dashboard_chart.setTheme(
                QChart.ChartThemeDark if self.dark else QChart.ChartThemeLight
            )
            self.dashboard_chart.setBackgroundVisible(False)
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
                    "Không thể kết nối",
                    f"{exc}\nVẫn đăng xuất?",
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
