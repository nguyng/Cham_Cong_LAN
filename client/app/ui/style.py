# Design system: neutral surfaces (60%), deep navigation (30%) and one role-specific
# accent (10%). Indigo identifies the employee portal; Admin replaces it with Teal.
BASE = """
QWidget {
    background: #F7F8FC;
    color: #172033;
    font-family: 'Segoe UI';
    font-size: 10pt;
}
QWidget#appShell, QDialog#employeeLogin, QDialog#adminLogin {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #F8FAFC, stop:0.58 #F7F8FC, stop:1 #F1F5F9);
}
QLabel { background: transparent; }
QToolTip {
    background: #0F172A;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 7px 10px;
}
QFrame#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #111827, stop:0.55 #172033, stop:1 #1E1B4B);
    border: 1px solid #334155;
    border-radius: 22px;
}
QFrame#adminSidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #0F172A, stop:0.55 #12343B, stop:1 #134E4A);
    border: 1px solid #2D5B59;
    border-radius: 22px;
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
QLabel#navSection {
    color: #94A3B8;
    font-size: 8pt;
    font-weight: 700;
    padding: 10px 8px 3px 8px;
    border-bottom: 1px solid #334155;
}
QFrame#adminSidebar QLabel#navSection {
    color: #99F6E4;
    border-bottom: 1px solid #2D5B59;
}
QFrame#pageHeader {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #4F46E5;
    border-radius: 17px;
}
QFrame#toolbar {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 15px;
}
QScrollArea#toolbarScroll,
QScrollArea#toolbarScroll QWidget#qt_scrollarea_viewport {
    background: transparent;
    border: 0;
}
QScrollArea#pageScroll,
QScrollArea#pageScroll QWidget#qt_scrollarea_viewport {
    background: transparent;
    border: 0;
}
QScrollArea#toolbarScroll QScrollBar:horizontal {
    background: #EEF2F7;
    height: 8px;
    margin: 1px 8px;
    border-radius: 4px;
}
QScrollArea#toolbarScroll QScrollBar::handle:horizontal {
    background: #94A3B8;
    border-radius: 4px;
    min-width: 44px;
}
QScrollArea#toolbarScroll QScrollBar::handle:horizontal:hover { background: #4F46E5; }
QScrollArea#toolbarScroll QScrollBar::add-line:horizontal,
QScrollArea#toolbarScroll QScrollBar::sub-line:horizontal { width: 0; }
QFrame#payrollToolbar {
    background: #FFFFFF;
    border: 1px solid #BAE6FD;
    border-left: 4px solid #0EA5E9;
    border-radius: 16px;
}
QFrame#payrollMetricCard {
    border: 1px solid rgba(255, 255, 255, 70);
    border-radius: 18px;
}
QFrame#payrollMetricCard[tone="teal"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0F766E, stop:1 #14B8A6);
}
QFrame#payrollMetricCard[tone="blue"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #0369A1, stop:1 #0EA5E9);
}
QFrame#payrollMetricCard[tone="orange"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #C2410C, stop:1 #F97316);
}
QFrame#payrollMetricCard[tone="violet"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #6D28D9, stop:1 #8B5CF6);
}
QLabel#payrollMetricLabel { color: #E0F2FE; font-size: 9pt; font-weight: 650; }
QLabel#payrollMetricValue { color: #FFFFFF; font-size: 20pt; font-weight: 800; }
QFrame#payrollChartCard {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 18px;
}
QLabel#chartTitle { color: #172033; font-size: 12pt; font-weight: 750; }
QChartView { background: transparent; border: 0; }
QLabel#payrollPolicy {
    color: #155E75;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ECFEFF, stop:1 #FFF7ED);
    border: 1px solid #A5F3FC;
    border-radius: 13px;
    padding: 9px 13px;
}
QPushButton[payrollAction="true"] {
    background: #F97316;
    border-color: #F97316;
}
QPushButton[payrollAction="true"]:hover {
    background: #C2410C;
    border-color: #C2410C;
}
QFrame#card, QFrame#adminCard, QFrame#emptyCard {
    background: #FFFFFF;
    border: 1px solid #E5EAF2;
    border-radius: 18px;
}
QFrame#card[tone="blue"], QFrame#adminCard[tone="blue"],
QFrame#attendanceSummaryCard[tone="blue"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #4F46E5;
}
QFrame#card[tone="violet"], QFrame#adminCard[tone="violet"],
QFrame#attendanceSummaryCard[tone="violet"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #7C3AED;
}
QFrame#card[tone="mint"], QFrame#adminCard[tone="mint"],
QFrame#attendanceSummaryCard[tone="mint"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #0F766E;
}
QFrame#card[tone="coral"], QFrame#adminCard[tone="coral"],
QFrame#attendanceSummaryCard[tone="coral"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #EA580C;
}
QFrame#card[tone="amber"], QFrame#adminCard[tone="amber"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #D97706;
}
QFrame#attendanceHero {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #312E81, stop:0.52 #3730A3, stop:1 #1D4ED8);
    border: 1px solid #4F46E5;
    border-radius: 24px;
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
    border-radius: 18px;
}
QFrame#attendanceGpsPanel {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ECFEFF, stop:1 #EEF2FF);
    border: 1px solid #A5F3FC;
    border-radius: 14px;
}
QLabel#gpsIcon {
    color: #FFFFFF;
    background: #0891B2;
    border-radius: 18px;
    min-width: 36px;
    min-height: 36px;
    max-width: 36px;
    max-height: 36px;
    qproperty-alignment: AlignCenter;
    font-size: 16pt;
    font-weight: 800;
}
QLabel#gpsTitle { color: #0E7490; font-size: 8pt; font-weight: 800; letter-spacing: 1px; }
QLabel#gpsValue { color: #164E63; font-size: 10pt; font-weight: 650; }
QLabel#sectionTitle { color: #172033; font-size: 14pt; font-weight: 750; }
QPushButton[attendanceAction="checkin"] {
    background: #15803D;
    border: 1px solid #16A34A;
    border-radius: 16px;
    font-size: 13pt;
    font-weight: 800;
}
QPushButton[attendanceAction="checkin"]:hover { background: #166534; }
QPushButton[attendanceAction="checkout"] {
    background: #EA580C;
    border: 1px solid #F97316;
    border-radius: 16px;
    font-size: 13pt;
    font-weight: 800;
}
QPushButton[attendanceAction="checkout"]:hover { background: #C2410C; }
QPushButton[attendanceAction="checkin"]:disabled,
QPushButton[attendanceAction="checkout"]:disabled { background: #CBD5E1; color: #64748B; }
QLabel#summaryTitle { color: #64748B; font-size: 9pt; font-weight: 650; }
QLabel#summaryValue { color: #172033; font-size: 14pt; font-weight: 750; }
QFrame#attendanceNotice {
    background: #EEF2FF;
    border: 1px solid #C7D2FE;
    border-radius: 16px;
}
QLabel#noticeIcon {
    color: #FFFFFF;
    background: #4F46E5;
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
    border-radius: 18px;
}
QFrame#attendanceStep {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 15px;
}
QFrame#attendanceStep[tone="blue"] { background: #F8FAFC; border-left: 3px solid #4F46E5; }
QFrame#attendanceStep[tone="mint"] { background: #F8FAFC; border-left: 3px solid #0F766E; }
QFrame#attendanceStep[tone="coral"] { background: #F8FAFC; border-left: 3px solid #EA580C; }
QFrame#attendanceStep[tone="mint"] QLabel#stepNumber {
    color: #0F766E; background: #CCFBF1;
}
QFrame#attendanceStep[tone="coral"] QLabel#stepNumber {
    color: #C2410C; background: #FFEDD5;
}
QLabel#stepNumber {
    color: #4F46E5;
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
QFrame#emptyCard { background: #F8FAFC; border-style: dashed; }
QPushButton {
    background: #4F46E5;
    color: #FFFFFF;
    border: 1px solid #4F46E5;
    border-radius: 13px;
    padding: 8px 15px;
    font-family: 'Segoe UI';
    font-size: 9.5pt;
    font-weight: 650;
    text-align: center;
}
QPushButton:hover {
    background: #4338CA;
    border: 1px solid #4338CA;
}
QPushButton:pressed { background: #3730A3; padding-top: 11px; padding-bottom: 9px; }
QPushButton:disabled { background: #94A3B8; color: #E2E8F0; }
QPushButton[secondary="true"] {
    background: #FFFFFF;
    color: #334155;
    border: 1px solid #C7D2FE;
}
QPushButton[secondary="true"]:hover {
    background: #EEF2FF;
    color: #3730A3;
    border: 1px solid #A5B4FC;
}
QPushButton[danger="true"] {
    background: #DC2626;
    border: 1px solid #DC2626;
}
QPushButton[danger="true"]:hover { background: #B91C1C; }
QPushButton[nav="true"] {
    background: transparent;
    text-align: left;
    color: #CBD5E1;
    padding: 9px 13px;
    border: 1px solid transparent;
    border-radius: 13px;
}
QPushButton[nav="true"]:hover {
    background: rgba(255, 255, 255, 28);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 45);
}
QPushButton[nav="true"]:checked {
    background: #4F46E5;
    color: #FFFFFF;
    border: 1px solid #6366F1;
}
QFrame#adminSidebar QPushButton[nav="true"]:checked {
    background: #0F766E;
    border: 1px solid #14B8A6;
}
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background: #FFFFFF;
    border: 1px solid #D8E0EC;
    border-radius: 12px;
    padding: 9px 11px;
    selection-background-color: #4F46E5;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {
    border: 2px solid #4F46E5;
    background: #F8FBFF;
}
QGroupBox {
    background: #FFFFFF;
    border: 1px solid #C7D2FE;
    border-radius: 14px;
    margin-top: 8px;
    padding: 10px;
}
QComboBox::drop-down, QDateEdit::drop-down, QTimeEdit::drop-down {
    border: 0;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #C7D2FE;
    border-radius: 10px;
    selection-background-color: #4F46E5;
    selection-color: #F9FAFB;
    padding: 5px;
}
QTableWidget {
    background: #FFFFFF;
    alternate-background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 17px;
    gridline-color: #EEF2F7;
    selection-background-color: #4F46E5;
    selection-color: #F9FAFB;
    font-family: 'Segoe UI';
    font-size: 9.5pt;
}
QTableWidget::item {
    padding: 7px 9px;
    border-bottom: 1px solid #EEF2F7;
}
QTableWidget::item:hover {
    background: #EEF2FF;
    color: #172033;
}
QTableWidget::item:selected {
    background: #4F46E5;
    color: #F9FAFB;
    border-top: 1px solid #3730A3;
    border-bottom: 1px solid #3730A3;
}
QHeaderView::section {
    background: #F1F5F9;
    color: #334155;
    border: 0;
    border-bottom: 1px solid #DDE6F2;
    padding: 10px 9px;
    font-family: 'Segoe UI';
    font-size: 9.5pt;
    font-weight: 700;
}
QProgressBar { background: #DDE6F2; border: 0; border-radius: 3px; }
QProgressBar::chunk {
    background: #4F46E5;
    border-radius: 3px;
}
QLabel#title { font-size: 22pt; font-weight: 800; color: #111827; }
QLabel#subtitle { color: #475569; font-size: 10pt; }
QLabel#metric { font-size: 25pt; font-weight: 750; color: #4F46E5; }
QLabel#adminMetric { font-size: 25pt; font-weight: 750; color: #0F766E; }
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
    BASE.replace("#4F46E5", "#0F766E")
    .replace("#4338CA", "#115E59")
    .replace("#3730A3", "#134E4A")
    .replace("#6366F1", "#14B8A6")
    .replace("#7C3AED", "#0E7490")
    .replace("#2563EB", "#0F766E")
    .replace("#1D4ED8", "#0F6478")
    .replace("#1E40AF", "#155E75")
)


def _dark(style: str) -> str:
    replacements = (
        ("#F7F8FC", "#08111F"),
        ("#F6F8FF", "#08111F"),
        ("#F8FBFF", "#111C2E"),
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
        ("#EFF6FF", "#162A43"),
        ("#F0F9FF", "#11283A"),
        ("#F1F5F9", "#172033"),
        ("#F5F3FF", "#251F3D"),
        ("#ECFEFF", "#123039"),
        ("#FFF7ED", "#382519"),
        ("#FFFBEA", "#352F16"),
        ("#EEF2FF", "#202A48"),
        ("#E0F2FE", "#163047"),
        ("#BFDBFE", "#254B70"),
        ("#C7D2FE", "#3D4770"),
        ("#DDD6FE", "#4A416C"),
        ("#A5F3FC", "#246875"),
        ("#FED7AA", "#704326"),
        ("#FDE68A", "#675823"),
        ("#CCFBF1", "#164E4A"),
        ("#FFEDD5", "#57311F"),
        ("#1E1B4B", "#E0E7FF"),
        ("#475569", "#AAB8CA"),
    )
    for source, target in replacements:
        style = style.replace(source, target)
    return style


DARK = _dark(LIGHT)
ADMIN_DARK = _dark(ADMIN_LIGHT)
