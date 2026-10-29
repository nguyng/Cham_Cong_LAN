import json
import socket
import threading

from app.core.config import get_settings


class DiscoveryServer:
    def __init__(self):
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True, name="udp-discovery")
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        settings = get_settings()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", settings.discovery_port))
            sock.settimeout(1)
            while not self._stop.is_set():
                try:
                    data, address = sock.recvfrom(512)
                    if data == b"LAN_ATTENDANCE_DISCOVER_V1":
                        payload = json.dumps(
                            {"service": "LAN Attendance", "port": settings.server_port, "https": bool(settings.tls_cert_file), "protocol": 1}
                        ).encode("utf-8")
                        sock.sendto(payload, address)
                except TimeoutError:
                    continue
                except OSError:
                    break


discovery_server = DiscoveryServer()
