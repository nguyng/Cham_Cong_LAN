import json
import sys
from pathlib import Path

from scripts import acceptance_lan

ROOT = Path(__file__).resolve().parents[1]


class FakeSocket:
    def __init__(self):
        self.messages = iter((json.dumps({"type": "connected", "role": "EMPLOYEE"}), "pong"))
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def recv(self, *, timeout):
        assert timeout == 3
        return next(self.messages)

    def send(self, message):
        self.sent.append(message)


def test_acceptance_websocket_uses_authorization_header(monkeypatch):
    captured = {}
    socket = FakeSocket()

    def fake_connect(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return socket

    monkeypatch.setattr(acceptance_lan, "connect", fake_connect)
    result = acceptance_lan.websocket_round_trip(
        "http://192.168.1.10:8000", "private-token", None, 3
    )

    assert captured["url"] == "ws://192.168.1.10:8000/api/v1/ws"
    assert "private-token" not in captured["url"]
    assert captured["kwargs"]["additional_headers"] == {
        "Authorization": "Bearer private-token"
    }
    assert "ssl" not in captured["kwargs"]
    assert socket.sent == ["ping"]
    assert result["type"] == "connected"


def test_acceptance_websocket_passes_tls_context(monkeypatch):
    captured = {}
    context = object()

    def fake_connect(url, **kwargs):
        captured.update(url=url, kwargs=kwargs)
        return FakeSocket()

    monkeypatch.setattr(acceptance_lan, "connect", fake_connect)
    acceptance_lan.websocket_round_trip("https://attendance.local", "token", context, 3)

    assert captured["url"] == "wss://attendance.local/api/v1/ws"
    assert captured["kwargs"]["ssl"] is context


def test_acceptance_reports_invalid_ca_without_traceback(monkeypatch, capsys):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "acceptance_lan.py",
            "--server-url",
            "https://attendance.local",
            "--ca-file",
            "missing-ca.pem",
        ],
    )
    monkeypatch.setattr(
        acceptance_lan,
        "tls_context",
        lambda _path: (_ for _ in ()).throw(OSError("Không đọc được CA")),
    )

    assert acceptance_lan.main() == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert "Không đọc được CA" in payload["error"]


def test_source_runner_has_server_watchdog_and_explicit_entrypoints():
    script = (ROOT / "scripts" / "run_all.ps1").read_text(encoding="utf-8")
    assert "server_launcher.py" in script
    assert "admin_launcher.py" in script
    assert "client_launcher.py" in script
    assert "Wait-Process -Id" in script
    assert "-WindowStyle Hidden" in script
    assert "/PID $($AdminShell.Id) /T /F" in script
    assert "/PID $($UserShell.Id) /T /F" in script


def test_setup_only_seeds_an_empty_database():
    script = (ROOT / "scripts" / "setup.ps1").read_text(encoding="utf-8")
    assert "seed_sample_data.py' --if-empty --skip-backups" in script
