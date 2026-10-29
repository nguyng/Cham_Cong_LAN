import hashlib
import json
import socket
import time
import uuid
from pathlib import Path

import httpx


class ApiError(RuntimeError):
    """User-facing REST/network failure."""


class ApiClient:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()
        self.token: str | None = None
        self.role: str | None = None
        self.employee_id: int | None = None
        self.device_registration_pending = False
        self._client = self._make_client()

    @property
    def device_fingerprint(self) -> str:
        identity = f"{socket.gethostname()}:{uuid.getnode()}"
        return hashlib.sha256(identity.encode("utf-8")).hexdigest()

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            example = self.config_path.with_name("config.example.json")
            if example.exists():
                return json.loads(example.read_text(encoding="utf-8"))
            return {"server_url": "http://127.0.0.1:8000", "verify_tls": True, "discovery_port": 37020, "request_timeout_seconds": 10}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def _make_client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.config["server_url"].rstrip("/"),
            verify=self.config.get("verify_tls", True),
            timeout=self.config.get("request_timeout_seconds", 10),
        )

    @property
    def websocket_url(self) -> str:
        scheme = "wss" if self.config["server_url"].startswith("https") else "ws"
        base = self.config["server_url"].split("://", 1)[1].rstrip("/")
        return f"{scheme}://{base}/api/v1/ws?token={self.token}"

    def request(self, method: str, path: str, **kwargs):
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            response = self._client.request(method, path, headers=headers, **kwargs)
        except httpx.HTTPError as exc:
            raise ApiError(f"Không thể kết nối Server: {exc}") from exc
        if response.status_code >= 400:
            try:
                message = response.json().get("detail", response.text)
            except ValueError:
                message = response.text
            raise ApiError(str(message))
        if response.status_code == 204:
            return None
        return response.json()

    def login(self, username: str, password: str):
        data = self.request("POST", "/api/v1/auth/login", json={"username": username, "password": password, "device_fingerprint": self.device_fingerprint})
        self.token = data["access_token"]
        self.role = data["role"]
        self.employee_id = data["employee_id"]
        try:
            registered = self.request(
                "POST",
                "/api/v1/devices",
                json={"fingerprint": self.device_fingerprint, "device_name": socket.gethostname()},
            )
            self.device_registration_pending = not registered["approved"]
        except ApiError as exc:
            if "đã được đăng ký" not in str(exc):
                raise
            devices = self.request("GET", "/api/v1/devices/me")
            self.device_registration_pending = not any(item["approved"] and item["active"] for item in devices)
        return data

    def attendance(self, action: str):
        return self.request("POST", f"/api/v1/attendance/{action}", json={"device_fingerprint": self.device_fingerprint, "idempotency_key": str(uuid.uuid4())})

    def download(self, path: str, params: dict | None = None) -> bytes:
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = self._client.get(path, params=params, headers=headers)
        except httpx.HTTPError as exc:
            raise ApiError(f"Không thể tải tệp: {exc}") from exc
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise ApiError(str(detail))
        return response.content

    def discover(self, attempts: int = 3) -> str | None:
        port = int(self.config.get("discovery_port", 37020))
        for _ in range(attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.settimeout(1.5)
                sock.sendto(b"LAN_ATTENDANCE_DISCOVER_V1", ("255.255.255.255", port))
                try:
                    data, address = sock.recvfrom(512)
                    result = json.loads(data.decode("utf-8"))
                    scheme = "https" if result.get("https") else "http"
                    return f"{scheme}://{address[0]}:{result['port']}"
                except (TimeoutError, ValueError, KeyError):
                    time.sleep(0.2)
        return None

    def set_server(self, url: str):
        self.config["server_url"] = url.rstrip("/")
        self.config_path.write_text(json.dumps(self.config, ensure_ascii=False, indent=2), encoding="utf-8")
        self._client.close()
        self._client = self._make_client()
