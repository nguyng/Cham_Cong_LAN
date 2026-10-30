# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules


project_root = Path(SPECPATH).parent
sys.path.insert(0, str(project_root / "server"))
datas = [
    (str(project_root / "server" / "alembic.ini"), "server"),
    (str(project_root / "server" / "alembic"), "server/alembic"),
]
binaries = []
hiddenimports = collect_submodules("app")
reportlab = collect_all("reportlab")
datas += reportlab[0]
binaries += reportlab[1]
hiddenimports += reportlab[2]

analysis = Analysis(
    [str(project_root / "server_launcher.py")],
    pathex=[str(project_root / "server")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# Windows already supplies this system runtime. Endpoint protection on the build
# machine blocks copying a second ucrtbase.dll into artifacts.
analysis.binaries = [item for item in analysis.binaries if item[0].lower() != "ucrtbase.dll"]
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="AttendanceServer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
bundle = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AttendanceServer",
)
