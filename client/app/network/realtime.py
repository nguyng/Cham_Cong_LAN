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
        self._event_loop = None
        self._main_task = None

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._event_loop = loop
        task = loop.create_task(self._loop())
        self._main_task = task
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
        finally:
            pending = asyncio.all_tasks(loop)
            for pending_task in pending:
                pending_task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self._main_task = None
            self._event_loop = None
            loop.close()

    async def _loop(self):
        delay = 1
        while self.running:
            try:
                async with websockets.connect(
                    self.url_factory(), open_timeout=10, ping_interval=20
                ) as socket:
                    self.connection_changed.emit(True)
                    delay = 1
                    async for payload in socket:
                        import json

                        if isinstance(payload, str) and payload.startswith("{"):
                            self.message.emit(json.loads(payload))
            except asyncio.CancelledError:
                raise
            except Exception:
                self.connection_changed.emit(False)
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)

    def stop(self):
        self.running = False
        self.requestInterruption()
        loop = self._event_loop
        task = self._main_task
        if loop is None or task is None or loop.is_closed():
            return

        def cancel_task():
            if not task.done():
                task.cancel()

        try:
            loop.call_soon_threadsafe(cancel_task)
        except RuntimeError:
            pass
