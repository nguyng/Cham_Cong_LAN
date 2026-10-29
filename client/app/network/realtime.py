import asyncio

import websockets
from PySide6.QtCore import QThread, Signal


class RealtimeThread(QThread):
    message = Signal(dict)
    connection_changed = Signal(bool)

    def __init__(self, url_factory, parent=None):
        super().__init__(parent)
        self.url_factory = url_factory
        self.running = True

    def run(self):
        asyncio.run(self._loop())

    async def _loop(self):
        delay = 1
        while self.running:
            try:
                async with websockets.connect(self.url_factory(), open_timeout=10, ping_interval=20) as socket:
                    self.connection_changed.emit(True)
                    delay = 1
                    async for payload in socket:
                        import json

                        if isinstance(payload, str) and payload.startswith("{"):
                            self.message.emit(json.loads(payload))
            except Exception:
                self.connection_changed.emit(False)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)

    def stop(self):
        self.running = False
        self.requestInterruption()
