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
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:0.72 #F8FAFC, stop:1 #EEF2FF);
    border: 1px solid #D9E4F4;
    border-left: 4px solid #4F46E5;
    border-bottom: 2px solid #C7D2FE;
    border-radius: 17px;
}
QFrame#toolbar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:0.78 #F8FAFC, stop:1 #EEF2F7);
    border: 1px solid #D9E4F4;
    border-bottom: 2px solid #CBD5E1;
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
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFFFFF, stop:0.65 #F0F9FF, stop:1 #ECFEFF);
    border: 1px solid #BAE6FD;
    border-left: 4px solid #0EA5E9;
    border-bottom: 2px solid #7DD3FC;
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
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:1 #F8FAFC);
    border: 1px solid #E2E8F0;
    border-bottom: 2px solid #CBD5E1;
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
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FB923C, stop:0.55 #F97316, stop:1 #EA580C);
    border-color: #F97316;
    border-bottom: 3px solid #9A3412;
}
QPushButton[payrollAction="true"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FDBA74, stop:0.5 #F97316, stop:1 #C2410C);
    border-color: #EA580C;
}
QFrame#card, QFrame#adminCard, QFrame#emptyCard {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:0.74 #FBFDFF, stop:1 #F1F5F9);
    border: 1px solid #E5EAF2;
    border-bottom: 2px solid #D8E0EC;
    border-radius: 18px;
}
QFrame#card[tone="blue"], QFrame#adminCard[tone="blue"],
QFrame#attendanceSummaryCard[tone="blue"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFFFFF, stop:0.7 #F8FAFC, stop:1 #EEF2FF);
    border: 1px solid #E2E8F0;
    border-left: 4px solid #4F46E5;
}
QFrame#card[tone="violet"], QFrame#adminCard[tone="violet"],
QFrame#attendanceSummaryCard[tone="violet"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFFFFF, stop:0.7 #FAF5FF, stop:1 #F5F3FF);
    border: 1px solid #E2E8F0;
    border-left: 4px solid #7C3AED;
}
QFrame#card[tone="mint"], QFrame#adminCard[tone="mint"],
QFrame#attendanceSummaryCard[tone="mint"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFFFFF, stop:0.7 #F0FDFA, stop:1 #ECFEFF);
    border: 1px solid #E2E8F0;
    border-left: 4px solid #0F766E;
}
QFrame#card[tone="coral"], QFrame#adminCard[tone="coral"],
QFrame#attendanceSummaryCard[tone="coral"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFFFFF, stop:0.7 #FFF7ED, stop:1 #FFEDD5);
    border: 1px solid #E2E8F0;
    border-left: 4px solid #EA580C;
}
QFrame#card[tone="amber"], QFrame#adminCard[tone="amber"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFFFFF, stop:0.7 #FFFBEB, stop:1 #FFF7ED);
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
QLabel#attendanceStatus[state="late"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #9A3412, stop:0.55 #B45309, stop:1 #C2410C);
    color: #FFF7ED;
    border: 1px solid #FDBA74;
}
QFrame#attendanceActionCard, QFrame#attendanceSummaryCard {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:0.76 #FBFDFF, stop:1 #F1F5F9);
    border: 1px solid #E5EAF2;
    border-bottom: 2px solid #D8E0EC;
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
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #22C55E, stop:0.52 #16A34A, stop:1 #15803D);
    border: 1px solid #16A34A;
    border-bottom: 4px solid #14532D;
    border-radius: 16px;
    font-size: 13pt;
    font-weight: 800;
}
QPushButton[attendanceAction="checkin"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #4ADE80, stop:0.5 #22C55E, stop:1 #166534);
}
QPushButton[attendanceAction="checkout"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FB923C, stop:0.52 #F97316, stop:1 #EA580C);
    border: 1px solid #F97316;
    border-bottom: 4px solid #9A3412;
    border-radius: 16px;
    font-size: 13pt;
    font-weight: 800;
}
QPushButton[attendanceAction="checkout"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FDBA74, stop:0.5 #FB923C, stop:1 #C2410C);
}
QPushButton[attendanceAction="checkin"]:pressed,
QPushButton[attendanceAction="checkout"]:pressed {
    border-bottom-width: 1px;
    padding-top: 11px;
    padding-bottom: 7px;
}
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
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:1 #F8FAFC);
    border: 1px solid #E5EAF2;
    border-bottom: 2px solid #D8E0EC;
    border-radius: 18px;
}
QFrame#attendanceStep {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:1 #F1F5F9);
    border: 1px solid #E2E8F0;
    border-bottom: 2px solid #CBD5E1;
    border-radius: 15px;
}
QFrame#attendanceStep[tone="blue"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFFFFF, stop:1 #EEF2FF);
    border-left: 3px solid #4F46E5;
}
QFrame#attendanceStep[tone="mint"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFFFFF, stop:1 #ECFEFF);
    border-left: 3px solid #0F766E;
}
QFrame#attendanceStep[tone="coral"] {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #FFFFFF, stop:1 #FFF7ED);
    border-left: 3px solid #EA580C;
}
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
QFrame#emptyCard {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:1 #F1F5F9);
    border-style: dashed;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #818CF8, stop:0.18 #6366F1, stop:0.62 #4F46E5, stop:1 #4338CA);
    color: #FFFFFF;
    border: 1px solid #6366F1;
    border-bottom: 3px solid #312E81;
    border-radius: 13px;
    padding: 8px 15px;
    font-family: 'Segoe UI';
    font-size: 9.5pt;
    font-weight: 650;
    text-align: center;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #A5B4FC, stop:0.2 #818CF8, stop:0.62 #6366F1, stop:1 #4F46E5);
    border: 1px solid #818CF8;
    border-bottom: 3px solid #3730A3;
}
QPushButton:pressed {
    background: #3730A3;
    border-bottom-width: 1px;
    padding-top: 10px;
    padding-bottom: 6px;
}
QPushButton:disabled { background: #94A3B8; color: #E2E8F0; }
QPushButton[secondary="true"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:0.66 #F8FAFC, stop:1 #EEF2FF);
    color: #334155;
    border: 1px solid #C7D2FE;
    border-bottom: 3px solid #A5B4FC;
}
QPushButton[secondary="true"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:0.55 #EEF2FF, stop:1 #E0E7FF);
    color: #3730A3;
    border: 1px solid #A5B4FC;
}
QPushButton[danger="true"] {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #F87171, stop:0.52 #EF4444, stop:1 #DC2626);
    border: 1px solid #DC2626;
    border-bottom: 3px solid #7F1D1D;
}
QPushButton[danger="true"]:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FCA5A5, stop:0.5 #EF4444, stop:1 #B91C1C);
}
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
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4338CA, stop:0.55 #4F46E5, stop:1 #6366F1);
    color: #FFFFFF;
    border: 1px solid #6366F1;
}
QFrame#adminSidebar QPushButton[nav="true"]:checked {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #115E59, stop:0.55 #0F766E, stop:1 #14B8A6);
    border: 1px solid #14B8A6;
}
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:1 #F8FAFC);
    border: 1px solid #D8E0EC;
    border-bottom: 2px solid #CBD5E1;
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
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FFFFFF, stop:1 #F8FAFC);
    border: 1px solid #C7D2FE;
    border-bottom: 2px solid #A5B4FC;
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
    alternate-background-color: #F1F5FF;
    border: 1px solid #D9E4F4;
    border-bottom: 2px solid #CBD5E1;
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
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #EEF2FF, stop:1 #E0F2FE);
    color: #172033;
}
QTableWidget::item:selected {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4338CA, stop:0.55 #4F46E5, stop:1 #6366F1);
    color: #F9FAFB;
    border-top: 1px solid #3730A3;
    border-bottom: 1px solid #3730A3;
}
QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #F8FAFC, stop:0.58 #EEF2FF, stop:1 #E2E8F0);
    color: #334155;
    border: 0;
    border-bottom: 2px solid #C7D2FE;
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


def _dark(style: str, accent: str, accent_hover: str, accent_pressed: str) -> str:
    """Append semantic dark rules without converting text colors into surfaces."""

    overrides = f"""
QWidget {{ background: #08111F; color: #E5E7EB; }}
QLabel {{ background: transparent; }}
QWidget#appShell, QDialog#employeeLogin, QDialog#adminLogin {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #07111F, stop:0.58 #0B1627, stop:1 #111B31);
}}
QFrame#sidebar, QFrame#adminSidebar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #07111F, stop:0.55 #111C2E, stop:1 #172554);
}}
QFrame#adminSidebar {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #07111F, stop:0.55 #102A2E, stop:1 #134E4A);
}}
QScrollArea#navScroll, QScrollArea#navScroll QWidget#qt_scrollarea_viewport,
QScrollArea#toolbarScroll, QScrollArea#toolbarScroll QWidget#qt_scrollarea_viewport,
QScrollArea#pageScroll, QScrollArea#pageScroll QWidget#qt_scrollarea_viewport,
QWidget#navContent, QFrame#sidebarFooter {{ background: transparent; }}
QFrame#pageHeader, QFrame#toolbar, QFrame#payrollToolbar,
QFrame#payrollChartCard, QFrame#card, QFrame#adminCard, QFrame#emptyCard,
QFrame#attendanceActionCard, QFrame#attendanceSummaryCard,
QFrame#attendanceGuide, QFrame#attendanceStep {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #18253A, stop:0.7 #111C2E, stop:1 #0D1728);
    border-color: #2B3A52;
    border-bottom-color: #07111F;
}}
QFrame#pageHeader {{ border-left-color: {accent}; }}
QFrame#payrollToolbar {{ border-left-color: #0EA5E9; }}
QFrame#card[tone="blue"], QFrame#adminCard[tone="blue"],
QFrame#card[tone="violet"], QFrame#adminCard[tone="violet"],
QFrame#card[tone="mint"], QFrame#adminCard[tone="mint"],
QFrame#card[tone="coral"], QFrame#adminCard[tone="coral"],
QFrame#card[tone="amber"], QFrame#adminCard[tone="amber"],
QFrame#attendanceSummaryCard[tone="blue"],
QFrame#attendanceSummaryCard[tone="violet"],
QFrame#attendanceSummaryCard[tone="mint"],
QFrame#attendanceSummaryCard[tone="coral"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #18253A, stop:0.62 #111C2E, stop:1 #172554);
}}
QFrame#attendanceStep[tone="blue"],
QFrame#attendanceStep[tone="mint"],
QFrame#attendanceStep[tone="coral"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #18253A, stop:1 #111C2E);
}}
QFrame#attendanceGpsPanel, QFrame#attendanceNotice {{
    background: #102A35;
    border-color: #246875;
}}
QLabel#title, QLabel#emptyTitle, QLabel#sectionTitle, QLabel#stepTitle,
QLabel#chartTitle, QLabel#summaryTitle, QLabel#summaryValue,
QLabel#gpsTitle {{ color: #F8FAFC; }}
QLabel#subtitle, QLabel#emptyText, QLabel#stepText,
QLabel#gpsValue, QLabel#noticeText {{ color: #AAB8CA; }}
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #18253A, stop:1 #111C2E);
    color: #E5E7EB;
    border-color: #34445E;
    selection-background-color: {accent};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
    background: #142033;
    border-color: {accent};
}}
QComboBox QAbstractItemView {{
    background: #111C2E;
    color: #E5E7EB;
    border-color: #3D4770;
    selection-background-color: {accent};
}}
QTableWidget {{
    background: #111C2E;
    alternate-background-color: #142033;
    color: #E5E7EB;
    border-color: #2B3A52;
    gridline-color: #25344D;
    selection-background-color: {accent};
}}
QTableWidget::item {{ border-bottom-color: #25344D; }}
QTableWidget::item:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #202A48, stop:1 #18324A);
    color: #F8FAFC;
}}
QTableWidget::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {accent_pressed}, stop:0.55 {accent}, stop:1 {accent_hover});
    color: #FFFFFF;
    border-top-color: {accent_pressed};
    border-bottom-color: {accent_pressed};
}}
QHeaderView::section {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #22314A, stop:0.58 #172033, stop:1 #111C2E);
    color: #D7E0EC;
    border-bottom-color: #30415B;
}}
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {accent_hover}, stop:0.38 {accent}, stop:1 {accent_pressed});
    color: #FFFFFF;
    border-color: {accent};
    border-bottom-color: {accent_pressed};
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 {accent}, stop:0.62 {accent_hover}, stop:1 {accent_pressed});
    border-color: {accent_hover};
}}
QPushButton:pressed {{ background: {accent_pressed}; border-bottom-width: 1px; }}
QPushButton[danger="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #F87171, stop:0.52 #EF4444, stop:1 #B91C1C);
    color: #FFFFFF;
    border-color: #DC2626;
    border-bottom-color: #7F1D1D;
}}
QPushButton[danger="true"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FCA5A5, stop:0.5 #EF4444, stop:1 #991B1B);
}}
QPushButton[attendanceAction="checkin"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #22C55E, stop:0.52 #16A34A, stop:1 #15803D);
    border-color: #16A34A;
    border-bottom-color: #14532D;
}}
QPushButton[attendanceAction="checkout"],
QPushButton[payrollAction="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #FB923C, stop:0.52 #F97316, stop:1 #EA580C);
    border-color: #F97316;
    border-bottom-color: #9A3412;
}}
QPushButton[attendanceAction="checkin"]:disabled,
QPushButton[attendanceAction="checkout"]:disabled {{
    background: #334155;
    color: #94A3B8;
    border-color: #475569;
}}
QPushButton[secondary="true"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #22314A, stop:1 #17263D);
    color: #E5E7EB;
    border-color: #3D4770;
    border-bottom-color: #111827;
}}
QPushButton[secondary="true"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2B3A56, stop:1 #202A48);
    color: #FFFFFF;
    border-color: {accent};
}}
QGroupBox {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #18253A, stop:1 #111C2E);
    color: #E5E7EB;
    border-color: #3D4770;
    border-bottom-color: #07111F;
}}
QToolTip {{ background: #111827; color: #F8FAFC; border-color: #475569; }}
QLabel#attendanceStatus[state="late"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7C2D12, stop:0.55 #9A3412, stop:1 #C2410C);
    color: #FFEDD5;
    border-color: #FB923C;
}}
QLabel#payrollPolicy {{ background: #102A35; color: #A5F3FC; border-color: #246875; }}
QProgressBar {{ background: #30415B; }}
QProgressBar::chunk {{ background: {accent}; }}
QScrollBar::handle:vertical {{ background: #475569; }}
QScrollArea#toolbarScroll QScrollBar:horizontal {{ background: #172033; }}
QScrollArea#toolbarScroll QScrollBar::handle:horizontal {{ background: #64748B; }}
"""
    return style + overrides


DARK = _dark(LIGHT, "#6366F1", "#4F46E5", "#4338CA")
ADMIN_DARK = _dark(ADMIN_LIGHT, "#0F766E", "#115E59", "#134E4A")
