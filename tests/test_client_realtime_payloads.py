import os
import subprocess
import sys
from pathlib import Path


def test_malformed_realtime_payload_does_not_disconnect_or_hide_next_message():
    root = Path(__file__).resolve().parents[1]
    script = r"""
from PySide6.QtCore import Qt
from app.network import realtime

events = {"connections": [], "errors": [], "messages": []}

class PayloadSocket:
    def __init__(self):
        self.payloads = iter(("{invalid", '{"type":"attendance_changed"}'))
    async def __aenter__(self):
        return self
    async def __aexit__(self, *_args):
        return False
    def __aiter__(self):
        return self
    async def __anext__(self):
        try:
            return next(self.payloads)
        except StopIteration:
            thread.running = False
            raise StopAsyncIteration

realtime.websockets.connect = lambda *_args, **_kwargs: PayloadSocket()
thread = realtime.RealtimeThread(lambda: "ws://127.0.0.1:1")
thread.connection_changed.connect(events["connections"].append, Qt.DirectConnection)
thread.error.connect(events["errors"].append, Qt.DirectConnection)
thread.message.connect(events["messages"].append, Qt.DirectConnection)
thread.start()
assert thread.wait(2000)
assert events["connections"] == [True]
assert events["errors"] == []
assert events["messages"] == [{"type": "attendance_changed"}]
print("REALTIME_PAYLOAD_OK")
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(root / "client")
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert "REALTIME_PAYLOAD_OK" in result.stdout
