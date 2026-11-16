from pathlib import Path

from client.app import device_identity


def test_hardware_identity_survives_runtime_file_cleanup_and_pc_rename(monkeypatch):
    monkeypatch.setattr(device_identity, "_system_machine_id", lambda: "machine-guid")
    monkeypatch.setattr(device_identity, "_windows_volume_serial", lambda: "A1B2C3D4")
    monkeypatch.setattr(
        device_identity,
        "_installation_id",
        lambda _path: (_ for _ in ()).throw(AssertionError("unexpected fallback")),
    )
    monkeypatch.setattr(device_identity.socket, "gethostname", lambda: "PC-OLD")

    first = device_identity.machine_fingerprint(Path("client/config.json"))
    monkeypatch.setattr(device_identity.socket, "gethostname", lambda: "PC-NEW")
    second = device_identity.machine_fingerprint(Path("client/config.json"))

    assert first == second
    assert len(first) == 64


def test_installation_identity_is_used_when_hardware_id_is_unavailable(monkeypatch):
    monkeypatch.setattr(device_identity, "_system_machine_id", lambda: None)
    monkeypatch.setattr(device_identity, "_windows_volume_serial", lambda: None)
    monkeypatch.setattr(device_identity, "_installation_id", lambda _path: "installation-id")
    monkeypatch.setattr(device_identity.socket, "gethostname", lambda: "PC-OLD")

    first = device_identity.machine_fingerprint(Path("client/config.json"))
    monkeypatch.setattr(device_identity.socket, "gethostname", lambda: "PC-NEW")
    second = device_identity.machine_fingerprint(Path("client/config.json"))

    assert first == second
    assert len(first) == 64
