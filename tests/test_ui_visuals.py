import os
import subprocess
import sys
from pathlib import Path

from client.app.ui.style import ADMIN_DARK, ADMIN_LIGHT, DARK, LIGHT


def test_all_themes_keep_depth_and_late_status_contrast():
    for theme in (LIGHT, DARK, ADMIN_LIGHT, ADMIN_DARK):
        assert theme.count("qlineargradient") >= 20
        assert 'QLabel#attendanceStatus[state="late"]' in theme
        assert "QTableWidget::item:selected" in theme
        assert "QPushButton:hover" in theme
        assert "QPushButton:pressed" in theme

    assert "color: #FFF7ED" in LIGHT
    assert "color: #FFEDD5" in DARK
    assert "QWidget { background: #08111F; color: #E5E7EB; }" in DARK
    assert "QLabel { background: transparent; }" in DARK
    assert "QLabel#chartTitle, QLabel#summaryTitle, QLabel#summaryValue," in DARK
    assert 'QPushButton[danger="true"]' in DARK
    assert 'QPushButton[attendanceAction="checkin"]' in DARK
    assert "stop:0 #7C2D12" in DARK
    assert "stop:0 #7C2D12" in ADMIN_DARK
    assert "stop:0 #115E59" in ADMIN_LIGHT
    assert "selection-background-color: #0F766E" in ADMIN_DARK


def test_decorated_action_button_gets_elevation_but_navigation_stays_crisp():
    root = Path(__file__).resolve().parents[1]
    script = r"""
from PySide6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QPushButton
from app.ui.icons import decorate_button

app = QApplication([])
action = QPushButton("Làm mới")
decorate_button(action)
shadow = action.graphicsEffect()
assert isinstance(shadow, QGraphicsDropShadowEffect)
assert shadow.blurRadius() == 16.0
assert shadow.offset().y() == 3.0

navigation = QPushButton("Tổng quan")
decorate_button(navigation, navigation=True)
assert navigation.graphicsEffect() is None
print("VISUAL_EFFECT_OK")
"""
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONPATH"] = str(root / "client")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    assert "VISUAL_EFFECT_OK" in result.stdout
