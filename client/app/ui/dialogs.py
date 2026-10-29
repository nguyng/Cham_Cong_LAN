from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QDate, QTime
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


@dataclass
class Field:
    key: str
    label: str
    kind: str = "text"
    value: Any = None
    options: list[tuple[str, Any]] | None = None
    required: bool = True


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
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _widget(self, field: Field):
        if field.kind == "date":
            widget = QDateEdit(calendarPopup=True)
            widget.setDisplayFormat("dd/MM/yyyy")
            widget.setDate(
                QDate.fromString(str(field.value), "yyyy-MM-dd")
                if field.value
                else QDate.currentDate()
            )
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
            widget.setRange(0, 1000000)
            widget.setDecimals(2)
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
        super().accept()
