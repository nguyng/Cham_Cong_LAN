from datetime import UTC, datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app.location import LocationRequest
from app.network.api import ApiError


class AttendancePortalMixin:
    """Employee attendance panel behavior, isolated from the main window shell."""

    @staticmethod
    def vietnamese_weekday(weekday):
        return (
            "Thứ Hai",
            "Thứ Ba",
            "Thứ Tư",
            "Thứ Năm",
            "Thứ Sáu",
            "Thứ Bảy",
            "Chủ Nhật",
        )[weekday]

    @staticmethod
    def display_time(value):
        if not value:
            return "Chưa ghi nhận"
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone().strftime("%H:%M")
        except (TypeError, ValueError):
            return str(value)

    def refresh_attendance_panel(self):
        if not hasattr(self, "attendance_summary"):
            return
        today = datetime.now().strftime("%Y-%m-%d")
        params = {"mine": True, "start": today, "end": today, "page": 1, "page_size": 5}
        try:
            attendance_data = self.api.request("GET", "/api/v1/attendance", params=params)
            schedule_data = self.api.request(
                "GET", "/api/v1/shift-assignments", params=params
            )
        except ApiError as exc:
            self.attendance_notice.setText(f"Chưa thể tải trạng thái chấm công: {exc}")
            return

        attendance_rows = (
            attendance_data.get("items", []) if isinstance(attendance_data, dict) else []
        )
        schedule_rows = schedule_data.get("items", []) if isinstance(schedule_data, dict) else []
        record = attendance_rows[0] if attendance_rows else None
        assignment = schedule_rows[0] if schedule_rows else None
        self.attendance_summary["shift"].setText(
            assignment.get("shift_name", "Chưa có lịch làm")
            if assignment
            else "Chưa có lịch làm"
        )
        self.attendance_summary["check_in"].setText(
            self.display_time(record.get("check_in_at")) if record else "Chưa ghi nhận"
        )
        self.attendance_summary["check_out"].setText(
            self.display_time(record.get("check_out_at")) if record else "Chưa ghi nhận"
        )
        worked_minutes = int(record.get("worked_minutes") or 0) if record else 0
        self.attendance_summary["worked"].setText(
            f"{worked_minutes // 60} giờ {worked_minutes % 60:02d} phút"
            if worked_minutes
            else "—"
        )

        if not record:
            status_text, state = "CHƯA CHECK-IN", "idle"
            self.check_in_button.setEnabled(bool(assignment))
            self.check_out_button.setEnabled(False)
            notice = (
                "Bạn chưa bắt đầu ca làm hôm nay."
                if assignment
                else "Hôm nay bạn chưa được phân ca."
            )
        elif not record.get("check_out_at"):
            status_text, state = "ĐANG TRONG CA", "active"
            self.check_in_button.setEnabled(False)
            self.check_out_button.setEnabled(True)
            notice = "Ca làm đang được ghi nhận. Hãy CHECK-OUT khi kết thúc công việc."
        else:
            status_text, state = "ĐÃ HOÀN THÀNH", "complete"
            self.check_in_button.setEnabled(False)
            self.check_out_button.setEnabled(False)
            notice = f"Ca làm hôm nay đã hoàn thành — {self.format_cell(record.get('status'))}."
        self.attendance_status.setText(status_text)
        self.attendance_status.setProperty("state", state)
        self.attendance_status.style().unpolish(self.attendance_status)
        self.attendance_status.style().polish(self.attendance_status)
        self.attendance_notice.setText(notice)

    def do_attendance(self, action):
        if getattr(self, "location_request", None) is not None:
            return
        check_in_enabled = self.check_in_button.isEnabled()
        check_out_enabled = self.check_out_button.isEnabled()
        self.check_in_button.setEnabled(False)
        self.check_out_button.setEnabled(False)
        self.attendance_location.setText("Đang yêu cầu quyền và xác định tọa độ GPS…")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self._attendance_previous_buttons = (check_in_enabled, check_out_enabled)
        self._attendance_action = action
        request = LocationRequest(parent=self)
        self.location_request = request
        request.succeeded.connect(self._attendance_location_ready)
        request.failed.connect(self._attendance_location_failed)
        request.finished.connect(request.deleteLater)
        request.start()

    def _attendance_location_ready(self, location):
        completed = False
        try:
            latitude = location["latitude"]
            longitude = location["longitude"]
            accuracy = location.get("location_accuracy_meters")
            accuracy_text = f" • Sai số khoảng {accuracy:g} m" if accuracy is not None else ""
            self.attendance_location.setText(
                f"Vĩ độ: {latitude:.6f}  •  Kinh độ: {longitude:.6f}{accuracy_text}"
            )
            data = self.api.attendance(self._attendance_action, location)
            self.show_toast(f"Chấm công thành công — {self.format_cell(data['status'])}")
            self.refresh_attendance_panel()
            self.refresh_dashboard()
            completed = True
        except ApiError as exc:
            QMessageBox.warning(self, "Không thể chấm công", str(exc))
        finally:
            self._finish_attendance(completed)

    def _attendance_location_failed(self, message):
        completed = False
        if self.api.config.get("allow_lan_ip_location_fallback", True):
            self.attendance_location.setText(
                "Máy không có GPS — đang xác minh bằng địa chỉ IP mạng LAN nội bộ."
            )
            try:
                data = self.api.attendance(
                    self._attendance_action, use_lan_ip_fallback=True
                )
                self.show_toast(
                    f"Chấm công thành công bằng IP nội bộ — {self.format_cell(data['status'])}"
                )
                self.refresh_attendance_panel()
                self.refresh_dashboard()
                completed = True
            except ApiError as fallback_error:
                QMessageBox.warning(
                    self,
                    "Không thể chấm công bằng IP nội bộ",
                    str(fallback_error),
                )
        else:
            self.attendance_location.setText("Chưa xác định được vị trí GPS.")
            QMessageBox.warning(
                self,
                "Không lấy được vị trí",
                f"{message}\n\nChấm công chưa được gửi vì chế độ dự phòng IP nội bộ đang tắt.",
            )
        self._finish_attendance(completed)

    def _finish_attendance(self, completed):
        QApplication.restoreOverrideCursor()
        self.location_request = None
        if not completed:
            check_in_enabled, check_out_enabled = self._attendance_previous_buttons
            self.check_in_button.setEnabled(check_in_enabled)
            self.check_out_button.setEnabled(check_out_enabled)
