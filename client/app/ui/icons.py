from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPushButton, QSizePolicy, QStyle, QWidget


def clean_button_text(text: str) -> str:
    """Remove text-glyph icons; buttons use crisp native icons instead."""

    cleaned = text.strip()
    for marker in ("↻", "⇩", "‹", "▶", "■"):
        cleaned = cleaned.removeprefix(marker).strip()
    cleaned = cleaned.removesuffix("›").strip()
    return cleaned


def action_icon(widget: QWidget, text: str, *, navigation: bool = False):
    value = text.casefold()
    standard = QStyle.StandardPixmap

    if navigation:
        if any(word in value for word in ("tổng quan", "trung tâm")):
            icon = standard.SP_DirHomeIcon
        elif any(word in value for word in ("chấm công", "client kết nối", "thiết bị")):
            icon = standard.SP_ComputerIcon
        elif any(word in value for word in ("báo cáo", "nhật ký", "lịch sử")):
            icon = standard.SP_FileDialogDetailedView
        elif any(word in value for word in ("lương", "quỹ phép")):
            icon = standard.SP_DriveHDIcon
        elif any(word in value for word in ("cảnh báo", "xác minh")):
            icon = standard.SP_MessageBoxWarning
        elif any(word in value for word in ("cấu hình", "tài khoản", "nhân viên")):
            icon = standard.SP_FileDialogInfoView
        elif any(word in value for word in ("duyệt", "nghỉ phép")):
            icon = standard.SP_DialogYesButton
        elif any(word in value for word in ("phòng ban", "chức vụ", "ca làm", "phân ca")):
            icon = standard.SP_DirIcon
        else:
            icon = standard.SP_FileIcon
        return widget.style().standardIcon(icon)

    if "check-in" in value:
        icon = standard.SP_MediaPlay
    elif "check-out" in value:
        icon = standard.SP_MediaStop
    elif "trang trước" in value:
        icon = standard.SP_ArrowBack
    elif "trang sau" in value:
        icon = standard.SP_ArrowForward
    elif any(word in value for word in ("làm mới", "reset", "thử lại")):
        icon = standard.SP_BrowserReload
    elif any(word in value for word in ("xóa", "loại bỏ")):
        icon = standard.SP_TrashIcon
    elif any(word in value for word in ("hủy", "từ chối", "thu hồi", "đăng xuất", "bỏ cảnh báo")):
        icon = standard.SP_DialogCancelButton
    elif any(word in value for word in ("xuất", "sao lưu")):
        icon = standard.SP_DialogSaveButton
    elif any(word in value for word in ("khôi phục", "tìm server", "mở")):
        icon = standard.SP_DialogOpenButton
    elif any(word in value for word in ("thêm", "tạo", "phân ca", "cấp/")):
        icon = standard.SP_FileDialogNewFolder
    elif any(word in value for word in ("duyệt", "xác nhận", "đăng nhập")):
        icon = standard.SP_DialogYesButton
    elif any(
        word in value
        for word in ("áp dụng", "cập nhật", "sửa", "đổi", "kích hoạt", "mở khóa", "ngừng")
    ):
        icon = standard.SP_DialogApplyButton
    elif any(word in value for word in ("sáng", "tối")):
        icon = standard.SP_DesktopIcon
    elif "cảnh báo" in value:
        icon = standard.SP_MessageBoxWarning
    else:
        icon = standard.SP_CommandLink
    return widget.style().standardIcon(icon)


def decorate_button(button: QPushButton, *, navigation: bool = False) -> None:
    text = clean_button_text(button.text())
    button.setText(text)
    button.setIcon(action_icon(button, text, navigation=navigation))
    button.setIconSize(QSize(20, 20) if navigation else QSize(18, 18))
    button.setMinimumHeight(42 if navigation else 40)
    text_width = button.fontMetrics().horizontalAdvance(text)
    button.setMinimumWidth(max(110, text_width + (70 if navigation else 64)))
    button.setSizePolicy(
        QSizePolicy.Expanding if navigation else QSizePolicy.Minimum,
        QSizePolicy.Fixed,
    )
    if not button.toolTip():
        button.setToolTip(text)
