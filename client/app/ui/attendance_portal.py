from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from app.location import LocationRequest
from app.network.api import ApiError
from app.timezone import local_today, to_local_datetime


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
        parsed = to_local_datetime(value)
        return parsed.strftime("%H:%M") if parsed else str(value)

    @staticmethod
    def attendance_worked_minutes(record):
        raw_minutes = record.get("worked_minutes")
        if raw_minutes not in (None, ""):
            try:
                return max(0, int(float(raw_minutes)))
            except (TypeError, ValueError):
                pass
        check_in = to_local_datetime(record.get("check_in_at"))
        check_out = to_local_datetime(record.get("check_out_at"))
        if check_in and check_out:
            return max(0, int((check_out - check_in).total_seconds() // 60))
        return None

    @staticmethod
    def is_late_attendance(record):
        status = str(record.get("status") or "")
        try:
            late_minutes = int(record.get("late_minutes") or 0)
        except (TypeError, ValueError):
            late_minutes = 0
        return (
            record.get("is_late") is True
            or status in {"LATE", "LATE_AND_EARLY"}
            or late_minutes > 0
        )

    @staticmethod
    def worked_time_text(minutes):
        if minutes is None:
            return "Chưa tính"
        return f"{minutes // 60} giờ {minutes % 60:02d} phút"

    def show_attendance_result(self, data, *, lan_fallback=False):
        status_text = self.format_cell(data.get("status"))
        method_text = " bằng IP nội bộ" if lan_fallback else ""
        if self.is_late_attendance(data):
            late_minutes = int(data.get("late_minutes") or 0)
            detail = f" {late_minutes} phút" if late_minutes else ""
            self.show_toast(
                f"Cảnh báo đi muộn{detail}{method_text} — {status_text}",
                error=True,
            )
            return
        self.show_toast(f"Chấm công thành công{method_text} — {status_text}")

    def refresh_attendance_panel(self):
        if not hasattr(self, "attendance_summary"):
            return
        today = local_today().isoformat()
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
        shift_data = assignment or record or {}
        shift_text = shift_data.get("shift_name") or "Chưa có lịch làm"
        shift_start = shift_data.get("shift_start_time") or (
            record.get("shift_start_time") if record else None
        )
        shift_end = shift_data.get("shift_end_time") or (
            record.get("shift_end_time") if record else None
        )
        if shift_start and shift_end:
            shift_text = f"{shift_text} • {shift_start}–{shift_end}"
        self.attendance_summary["shift"].setText(shift_text)
        self.attendance_summary["check_in"].setText(
            self.display_time(record.get("check_in_at")) if record else "Chưa ghi nhận"
        )
        self.attendance_summary["check_out"].setText(
            self.display_time(record.get("check_out_at")) if record else "Chưa ghi nhận"
        )
        worked_minutes = self.attendance_worked_minutes(record) if record else None
        if record and record.get("check_out_at"):
            worked_text = self.worked_time_text(worked_minutes)
        elif record:
            worked_text = "Đang tính…"
        else:
            worked_text = "—"
        self.attendance_summary["worked"].setText(worked_text)

        is_late = bool(record and self.is_late_attendance(record))
        late_minutes = int(record.get("late_minutes") or 0) if record else 0
        late_detail = f"{late_minutes} phút" if late_minutes else "quá giờ quy định"
        scheduled_start = (
            record.get("shift_start_time") if record else None
        ) or shift_data.get("shift_start_time")

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
            self.check_in_button.setEnabled(False)
            self.check_out_button.setEnabled(True)
            if is_late:
                status_text, state = f"ĐI MUỘN • {late_detail.upper()}", "late"
                shift_note = f" so với giờ vào ca {scheduled_start}" if scheduled_start else ""
                notice = (
                    f"Cảnh báo: bạn check-in muộn {late_detail}{shift_note}. "
                    "Giờ vào thực tế vẫn được ghi nhận đầy đủ."
                )
            else:
                status_text, state = "ĐANG TRONG CA", "active"
                notice = (
                    "Ca làm đang được ghi nhận. "
                    "Hãy CHECK-OUT khi kết thúc công việc."
                )
        else:
            self.check_in_button.setEnabled(False)
            self.check_out_button.setEnabled(False)
            result_text = self.format_cell(record.get("status"))
            if is_late:
                status_text, state = "ĐÃ HOÀN THÀNH • ĐI MUỘN", "late"
                notice = (
                    f"Cảnh báo đi muộn {late_detail}. Ca đã hoàn thành "
                    f"với {self.worked_time_text(worked_minutes)} — {result_text}."
                )
            else:
                status_text, state = "ĐÃ HOÀN THÀNH", "complete"
                notice = (
                    f"Ca làm hôm nay đã hoàn thành với "
                    f"{self.worked_time_text(worked_minutes)} — {result_text}."
                )
        self.attendance_status.setText(status_text)
        self.attendance_status.setProperty("state", state)
        self.attendance_status.style().unpolish(self.attendance_status)
        self.attendance_status.style().polish(self.attendance_status)
        self.attendance_notice.setProperty("state", "warning" if is_late else "normal")
        self.attendance_notice.style().unpolish(self.attendance_notice)
        self.attendance_notice.style().polish(self.attendance_notice)
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
            self.show_attendance_result(data)
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
                self.show_attendance_result(data, lan_fallback=True)
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
