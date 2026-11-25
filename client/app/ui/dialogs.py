from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QDate, QRectF, Qt, QTime
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
)

from app.timezone import local_today
from app.ui.icons import decorate_button


@dataclass
class Field:
    key: str
    label: str
    kind: str = "text"
    value: Any = None
    options: list[tuple[str, Any]] | None = None
    required: bool = True


class CalendarDateEdit(QDateEdit):
    def __init__(self, accent: str = "#4F46E5", parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setProperty("calendarPicker", True)
        self.calendar_accent = QColor(accent)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        button = QRectF(self.width() - 34, 2, 32, self.height() - 4)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.calendar_accent)
        painter.drawRoundedRect(button, 8, 8)

        center_x = button.center().x()
        center_y = button.center().y()
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(
            QRectF(center_x - 6, center_y - 5, 12, 10), 1.5, 1.5
        )
        painter.drawLine(center_x - 6, center_y - 2, center_x + 6, center_y - 2)
        painter.drawLine(center_x - 3, center_y - 7, center_x - 3, center_y - 4)
        painter.drawLine(center_x + 3, center_y - 7, center_x + 3, center_y - 4)


class FormDialog(QDialog):
    def __init__(self, title: str, fields: list[Field], parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(480)
        self.fields = fields
        self.widgets: dict[str, Any] = {}
        root = QVBoxLayout(self)
        form = QFormLayout()
        for field in fields:
            widget = self._widget(field)
            self.widgets[field.key] = widget
            form.addRow(field.label, widget)
        root.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok_button = buttons.button(QDialogButtonBox.Ok)
        cancel_button = buttons.button(QDialogButtonBox.Cancel)
        self.ok_button = ok_button
        ok_button.setText("Lưu thay đổi")
        cancel_button.setText("Hủy")
        cancel_button.setProperty("secondary", True)
        decorate_button(ok_button)
        decorate_button(cancel_button)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _widget(self, field: Field):
        if field.kind == "date":
            parent = self.parentWidget()
            accent = (
                "#0F766E"
                if parent is not None and getattr(parent, "admin_only", False)
                else "#4F46E5"
            )
            widget = CalendarDateEdit(accent)
            widget.setDisplayFormat("dd/MM/yyyy")
            widget.setMinimumDate(QDate(2020, 1, 1))
            widget.setMaximumDate(QDate(2100, 12, 31))
            widget.calendarWidget().setFirstDayOfWeek(Qt.Monday)
            widget.calendarWidget().setGridVisible(True)
            widget.setFixedWidth(220)
            if field.value:
                widget.setDate(QDate.fromString(str(field.value), "yyyy-MM-dd"))
            else:
                today = local_today()
                widget.setDate(QDate(today.year, today.month, today.day))
            return widget
        if field.kind == "time":
            widget = QTimeEdit()
            widget.setDisplayFormat("HH:mm")
            widget.setTime(
                QTime.fromString(str(field.value), "HH:mm:ss")
                if field.value
                else QTime.currentTime()
            )
            return widget
        if field.kind == "int":
            widget = QSpinBox()
            widget.setRange(0, 1000000)
            widget.setValue(int(field.value or 0))
            return widget
        if field.kind == "decimal":
            widget = QDoubleSpinBox()
            widget.setRange(0, 999999999999)
            widget.setDecimals(2)
            widget.setSingleStep(100000)
            widget.setGroupSeparatorShown(True)
            widget.setValue(float(field.value or 0))
            return widget
        if field.kind == "multiline":
            widget = QTextEdit(str(field.value or ""))
            widget.setMaximumHeight(110)
            return widget
        if field.kind == "choice":
            widget = QComboBox()
            for label, value in field.options or []:
                widget.addItem(label, value)
            selected = widget.findData(field.value)
            if selected >= 0:
                widget.setCurrentIndex(selected)
            return widget
        if field.kind == "bool":
            widget = QCheckBox()
            widget.setChecked(bool(field.value))
            return widget
        if field.kind == "weekdays":
            widget = QGroupBox()
            grid = QGridLayout(widget)
            selected = set(field.value if field.value is not None else [0, 1, 2, 3, 4])
            boxes = []
            for index, label in enumerate(
                ("Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật")
            ):
                box = QCheckBox(label)
                box.setChecked(index in selected)
                grid.addWidget(box, index // 4, index % 4)
                boxes.append(box)
            widget.setProperty("weekday_boxes", boxes)
            return widget
        widget = QLineEdit(str(field.value or ""))
        if field.kind == "password":
            widget.setEchoMode(QLineEdit.Password)
        return widget

    def values(self) -> dict:
        result = {}
        for field in self.fields:
            widget = self.widgets[field.key]
            if field.kind == "date":
                result[field.key] = widget.date().toString("yyyy-MM-dd")
            elif field.kind == "time":
                result[field.key] = widget.time().toString("HH:mm:ss")
            elif field.kind == "int":
                result[field.key] = widget.value() if field.required or widget.value() else None
            elif field.kind == "decimal":
                result[field.key] = widget.value()
            elif field.kind == "multiline":
                result[field.key] = widget.toPlainText().strip()
            elif field.kind == "choice":
                result[field.key] = widget.currentData()
            elif field.kind == "bool":
                result[field.key] = widget.isChecked()
            elif field.kind == "weekdays":
                result[field.key] = [
                    index
                    for index, box in enumerate(widget.property("weekday_boxes"))
                    if box.isChecked()
                ]
            else:
                value = widget.text().strip()
                result[field.key] = value if value or field.required else None
        return result

    def accept(self):
        values = self.values()
        missing = []
        for field in self.fields:
            value = values[field.key]
            if field.required and (value is None or value == "" or value == []):
                missing.append(field.label)
        if missing:
            QMessageBox.warning(
                self,
                "Thiếu thông tin",
                "Vui lòng nhập/chọn: " + ", ".join(missing),
            )
            return
        if "start_date" in values and "end_date" in values:
            start_date = QDate.fromString(str(values["start_date"]), "yyyy-MM-dd")
            end_date = QDate.fromString(str(values["end_date"]), "yyyy-MM-dd")
            if start_date.isValid() and end_date.isValid() and end_date < start_date:
                QMessageBox.warning(
                    self,
                    "Khoảng ngày không hợp lệ",
                    "Ngày kết thúc phải từ ngày bắt đầu trở đi.",
                )
                return
        super().accept()
