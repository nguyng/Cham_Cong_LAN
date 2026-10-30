import os
import subprocess
import sys
from pathlib import Path


def test_realtime_thread_stops_while_websocket_is_waiting():
    root = Path(__file__).resolve().parents[1]
    script = r"""
import asyncio
import threading

from app.network import realtime

connected = threading.Event()

class WaitingSocket:
    async def __aenter__(self):
        connected.set()
        return self

    async def __aexit__(self, *_args):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        await asyncio.Event().wait()

realtime.websockets.connect = lambda *_args, **_kwargs: WaitingSocket()
thread = realtime.RealtimeThread(lambda: "ws://127.0.0.1:1")
thread.start()
assert connected.wait(timeout=2)
thread.stop()
assert thread.wait(2000)
assert not thread.isRunning()
print("REALTIME_STOP_OK")
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
    assert "REALTIME_STOP_OK" in result.stdout
