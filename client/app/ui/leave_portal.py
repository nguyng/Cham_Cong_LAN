from PySide6.QtWidgets import QMessageBox

from app.network.api import ApiError
from app.ui.dialogs import Field


class LeavePortalMixin:
    """Employee leave-request actions, including cancellation."""

    def create_leave(self, table):
        try:
            response = self.api.request("GET", "/api/v1/leave-types")
            leave_types = response.get("items", []) if isinstance(response, dict) else response
        except ApiError as exc:
            QMessageBox.warning(self, "Không tải được loại nghỉ", str(exc))
            return
        if not leave_types:
            QMessageBox.information(
                self,
                "Chưa có loại nghỉ phép",
                "Admin cần tạo ít nhất một loại nghỉ phép trước khi nhân viên tạo đơn.",
            )
            return
        fields = [
            Field(
                "leave_type_id",
                "Loại nghỉ",
                "choice",
                options=[(item["name"], item["id"]) for item in leave_types],
            ),
            Field("start_date", "Từ ngày", "date"),
            Field("end_date", "Đến ngày", "date"),
            Field("reason", "Lý do", "multiline"),
        ]
        if self.submit_dialog("Tạo đơn nghỉ phép", fields, "POST", "/api/v1/leaves"):
            self.load_table(table, "/api/v1/leaves")

    def cancel_leave(self, table):
        row = self.selected(table)
        if not row:
            return
        if row.get("status") not in ("PENDING", "APPROVED"):
            QMessageBox.information(
                self,
                "Không thể hủy",
                "Chỉ có thể hủy đơn đang chờ hoặc đã duyệt nhưng chưa bắt đầu.",
            )
            return
        if (
            QMessageBox.question(
                self,
                "Hủy đơn nghỉ phép",
                f"Bạn chắc chắn muốn hủy đơn #{row['id']}?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return
        try:
            self.api.request("POST", f"/api/v1/leaves/{row['id']}/cancel")
            self.show_toast("Đã hủy đơn nghỉ phép.")
            self.load_table(table, "/api/v1/leaves")
        except ApiError as exc:
            QMessageBox.warning(self, "Không hủy được đơn", str(exc))
