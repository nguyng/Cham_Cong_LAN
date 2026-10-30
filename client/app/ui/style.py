BASE = """
QWidget {
    background: #F5F7FB;
    color: #172033;
    font: 10pt 'Segoe UI';
}
QLabel { background: transparent; }
QToolTip { background: #0F172A; color: #F8FAFC; border: 0; padding: 6px; }
QFrame#sidebar { background: #0F172A; border-radius: 18px; }
QFrame#adminSidebar {
    background: #071426;
    border: 1px solid #183B5B;
    border-radius: 18px;
}
QScrollArea#navScroll, QScrollArea#navScroll QWidget#qt_scrollarea_viewport,
QWidget#navContent {
    background: transparent;
    border: 0;
}
QFrame#sidebarFooter {
    background: transparent;
    border: 0;
    border-top: 1px solid #24354C;
}
QScrollArea#navScroll QScrollBar:vertical {
    background: transparent;
    width: 7px;
    margin: 3px 0;
}
QScrollArea#navScroll QScrollBar::handle:vertical {
    background: #475569;
    border-radius: 3px;
    min-height: 34px;
}
QFrame#adminSidebar QScrollArea#navScroll QScrollBar::handle:vertical {
    background: #0E7490;
}
QScrollArea#navScroll QScrollBar::handle:vertical:hover { background: #22D3EE; }
QScrollArea#navScroll QScrollBar::add-line:vertical,
QScrollArea#navScroll QScrollBar::sub-line:vertical { height: 0; }
QScrollArea#navScroll QScrollBar::add-page:vertical,
QScrollArea#navScroll QScrollBar::sub-page:vertical { background: transparent; }
QFrame#sidebar QLabel, QFrame#adminSidebar QLabel {
    color: #E5E7EB;
    background: transparent;
}
QFrame#pageHeader, QFrame#toolbar { background: transparent; border: 0; }
QFrame#card, QFrame#adminCard, QFrame#emptyCard {
    background: #FFFFFF;
    border: 1px solid #E5EAF2;
    border-radius: 14px;
}
QFrame#attendanceHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #172554, stop:0.55 #1E3A8A, stop:1 #2563EB);
    border: 1px solid #3B82F6;
    border-radius: 20px;
}
QFrame#attendanceHero QLabel { color: #F8FAFC; background: transparent; }
QLabel#attendanceEyebrow {
    color: #93C5FD;
    font-size: 9pt;
    font-weight: 750;
    letter-spacing: 2px;
}
QLabel#attendanceClock { font-size: 42pt; font-weight: 800; letter-spacing: 2px; }
QLabel#attendanceDate { color: #CBD5E1; font-size: 11pt; }
QLabel#attendanceStatus {
    border-radius: 13px;
    padding: 6px 16px;
    font-size: 9pt;
    font-weight: 800;
}
QLabel#attendanceStatus[state="idle"] { background: #334155; color: #E2E8F0; }
QLabel#attendanceStatus[state="active"] { background: #166534; color: #DCFCE7; }
QLabel#attendanceStatus[state="complete"] { background: #1D4ED8; color: #DBEAFE; }
QFrame#attendanceActionCard, QFrame#attendanceSummaryCard {
    background: #FFFFFF;
    border: 1px solid #E5EAF2;
    border-radius: 15px;
}
QLabel#sectionTitle { color: #172033; font-size: 14pt; font-weight: 750; }
QPushButton[attendanceAction="checkin"] {
    background: #16A34A;
    border-radius: 12px;
    font-size: 13pt;
    font-weight: 800;
}
QPushButton[attendanceAction="checkin"]:hover { background: #15803D; }
QPushButton[attendanceAction="checkout"] {
    background: #EA580C;
    border-radius: 12px;
    font-size: 13pt;
    font-weight: 800;
}
QPushButton[attendanceAction="checkout"]:hover { background: #C2410C; }
QPushButton[attendanceAction="checkin"]:disabled,
QPushButton[attendanceAction="checkout"]:disabled { background: #CBD5E1; color: #64748B; }
QLabel#summaryTitle { color: #64748B; font-size: 9pt; font-weight: 650; }
QLabel#summaryValue { color: #172033; font-size: 14pt; font-weight: 750; }
QFrame#attendanceNotice {
    background: #EFF6FF;
    border: 1px solid #BFDBFE;
    border-radius: 12px;
}
QLabel#noticeIcon {
    color: #FFFFFF;
    background: #2563EB;
    border-radius: 10px;
    min-width: 20px;
    min-height: 20px;
    max-width: 20px;
    max-height: 20px;
    qproperty-alignment: AlignCenter;
    font-weight: 800;
}
QLabel#noticeText { color: #1E3A5F; }
QFrame#attendanceGuide {
    background: #FFFFFF;
    border: 1px solid #E5EAF2;
    border-radius: 15px;
}
QFrame#attendanceStep {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 11px;
}
QLabel#stepNumber {
    color: #2563EB;
    background: #DBEAFE;
    border-radius: 17px;
    min-width: 34px;
    min-height: 34px;
    max-width: 34px;
    max-height: 34px;
    qproperty-alignment: AlignCenter;
    font-size: 9pt;
    font-weight: 800;
}
QLabel#stepTitle { color: #172033; font-weight: 750; }
QLabel#stepText { color: #64748B; font-size: 9pt; }
QFrame#adminCard { border-top: 3px solid #0891B2; }
QFrame#emptyCard { background: #F8FAFC; border-style: dashed; }
QPushButton {
    background: #2563EB;
    color: #FFFFFF;
    border: 0;
    border-radius: 9px;
    padding: 9px 15px;
    font-weight: 600;
}
QPushButton:hover { background: #1D4ED8; }
QPushButton:pressed { background: #1E40AF; }
QPushButton:disabled { background: #94A3B8; color: #E2E8F0; }
QPushButton[secondary="true"] { background: #E8EEF8; color: #26344D; }
QPushButton[secondary="true"]:hover { background: #D9E4F4; }
QPushButton[danger="true"] { background: #DC2626; }
QPushButton[danger="true"]:hover { background: #B91C1C; }
QPushButton[nav="true"] {
    background: transparent;
    text-align: left;
    color: #CBD5E1;
    padding: 10px 13px;
    border-radius: 9px;
}
QPushButton[nav="true"]:hover { background: #1F2937; color: #FFFFFF; }
QPushButton[nav="true"]:checked { background: #2563EB; color: #FFFFFF; }
QFrame#adminSidebar QPushButton[nav="true"]:checked { background: #0E7490; }
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background: #FFFFFF;
    border: 1px solid #D8E0EC;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #2563EB;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus { border: 1px solid #2563EB; }
QTableWidget {
    background: #FFFFFF;
    alternate-background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    gridline-color: #EEF2F7;
    selection-background-color: #DBEAFE;
    selection-color: #172033;
}
QHeaderView::section {
    background: #EFF4FF;
    color: #334155;
    border: 0;
    border-bottom: 1px solid #DDE6F2;
    padding: 9px;
    font-weight: 650;
}
QProgressBar { background: #DDE6F2; border: 0; border-radius: 2px; }
QProgressBar::chunk { background: #2563EB; border-radius: 2px; }
QLabel#title { font-size: 21pt; font-weight: 750; color: #111827; }
QLabel#subtitle { color: #64748B; font-size: 10pt; }
QLabel#metric { font-size: 25pt; font-weight: 750; color: #2563EB; }
QLabel#adminMetric { font-size: 25pt; font-weight: 750; color: #0891B2; }
QLabel#roleBadge {
    color: #A5F3FC;
    background: #164E63;
    border: 1px solid #155E75;
    border-radius: 8px;
    padding: 5px 9px;
    font-weight: 700;
}
QLabel#emptyTitle { color: #334155; font-size: 13pt; font-weight: 700; }
QLabel#emptyText { color: #64748B; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 5px; min-height: 28px; }
"""

LIGHT = BASE
ADMIN_LIGHT = (
    BASE.replace("#2563EB", "#0E7490").replace("#1D4ED8", "#0F6478").replace("#1E40AF", "#155E75")
)


def _dark(style: str) -> str:
    replacements = (
        ("#F5F7FB", "#08111F"),
        ("#172033", "#E5E7EB"),
        ("#FFFFFF", "#111C2E"),
        ("#F8FAFC", "#142033"),
        ("#E5EAF2", "#25344D"),
        ("#D8E0EC", "#34445E"),
        ("#E2E8F0", "#2B3A52"),
        ("#EEF2F7", "#25344D"),
        ("#EFF4FF", "#17263D"),
        ("#DDE6F2", "#30415B"),
        ("#334155", "#D7E0EC"),
        ("#111827", "#F8FAFC"),
        ("#64748B", "#AAB8CA"),
        ("#E8EEF8", "#24344C"),
        ("#26344D", "#E5E7EB"),
        ("#D9E4F4", "#30445F"),
        ("#DBEAFE", "#1E4D68"),
    )
    for source, target in replacements:
        style = style.replace(source, target)
    return style


DARK = _dark(LIGHT)
ADMIN_DARK = _dark(ADMIN_LIGHT)
