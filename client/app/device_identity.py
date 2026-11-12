import hashlib
import os
import platform
import socket
import uuid
from pathlib import Path

from .files import write_text_atomic


def _windows_machine_guid() -> str | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        ) as key:
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            return str(value).strip() or None
    except OSError:
        return None


def _windows_volume_serial() -> str | None:
    if os.name != "nt":
        return None
    try:
        import ctypes

        drive = os.environ.get("SystemDrive", "C:").rstrip("\\/") + "\\"
        serial = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive),
            None,
            0,
            ctypes.byref(serial),
            None,
            None,
            None,
            0,
        )
        return f"{serial.value:08X}" if ok else None
    except (AttributeError, OSError, ValueError):
        return None


def _system_machine_id() -> str | None:
    if os.name == "nt":
        return _windows_machine_guid()
    for path in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
        try:
            value = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if value:
            return value
    return None


def _installation_id(config_path: Path) -> str | None:
    identity_path = config_path.with_name("device.id")
    try:
        value = identity_path.read_text(encoding="ascii").strip()
        if 16 <= len(value) <= 128:
            return value
    except OSError:
        pass
    value = uuid.uuid4().hex
    try:
        identity_path.parent.mkdir(parents=True, exist_ok=True)
        write_text_atomic(identity_path, value, encoding="ascii")
        return value
    except OSError:
        return None


def machine_fingerprint(config_path: Path) -> str:
    """Hash stable OS and installation identifiers without exposing raw hardware IDs."""

    components = {
        "machine_id": _system_machine_id(),
        "volume_serial": _windows_volume_serial(),
        "installation_id": _installation_id(config_path),
        "host": socket.gethostname(),
        "platform": platform.system(),
    }
    stable = "|".join(f"{key}={value}" for key, value in components.items() if value)
    if not stable:
        stable = f"fallback={socket.gethostname()}:{uuid.getnode()}"
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()
