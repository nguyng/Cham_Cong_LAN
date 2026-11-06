import hashlib
import json
import socket
import time
import uuid
from pathlib import Path

import httpx


class ApiError(RuntimeError):
    """User-facing REST/network failure."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


VALIDATION_MESSAGES = {
    "missing": "không được để trống",
    "string_too_short": "quá ngắn",
    "string_too_long": "quá dài",
    "greater_than_equal": "nhỏ hơn giá trị cho phép",
    "less_than_equal": "lớn hơn giá trị cho phép",
    "date_from_datetime_parsing": "không đúng định dạng ngày",
    "time_parsing": "không đúng định dạng giờ",
    "int_parsing": "phải là số nguyên",
    "float_parsing": "phải là số",
    "bool_parsing": "phải là đúng hoặc sai",
    "literal_error": "không thuộc danh sách được phép",
}


def _validation_message(errors: list) -> str:
    messages = []
    for error in errors:
        if not isinstance(error, dict):
            continue
        location = error.get("loc", [])
        field = ".".join(str(part) for part in location if part not in ("body", "query", "path"))
        error_type = str(error.get("type", ""))
        message = VALIDATION_MESSAGES.get(error_type, str(error.get("msg", "không hợp lệ")))
        messages.append(f"{field}: {message}" if field else message)
    return "Dữ liệu không hợp lệ: " + "; ".join(messages or ["vui lòng kiểm tra lại thông tin"])


def _response_error(response: httpx.Response) -> ApiError:
    try:
        payload = response.json()
    except ValueError:
        payload = None
    detail = payload.get("detail") if isinstance(payload, dict) else None
    if isinstance(detail, list):
        message = _validation_message(detail)
    elif isinstance(detail, dict):
        message = str(detail.get("message") or detail.get("error") or detail)
    elif detail:
        message = str(detail)
    else:
        message = response.text.strip() or "Server không cung cấp nội dung lỗi."
    prefixes = {
        400: "Yêu cầu không hợp lệ",
        401: "Phiên đăng nhập không hợp lệ",
        403: "Không đủ quyền truy cập",
        404: "Không tìm thấy dữ liệu",
        409: "Dữ liệu bị xung đột",
        410: "Yêu cầu đã hết hạn",
        422: "Thông tin chưa hợp lệ",
        423: "Tài khoản đang bị khóa",
        429: "Thao tác quá thường xuyên",
    }
    prefix = prefixes.get(response.status_code, "Lỗi Server" if response.status_code >= 500 else "Lỗi yêu cầu")
    return ApiError(f"{prefix}: {message}", response.status_code)


def _network_error(exc: httpx.HTTPError, action: str = "kết nối Server") -> ApiError:
    if isinstance(exc, httpx.TimeoutException):
        return ApiError(f"Server không phản hồi khi {action}. Vui lòng kiểm tra Server và thử lại.")
    if isinstance(exc, httpx.ConnectError):
        return ApiError(
            "Không thể kết nối Server. Hãy kiểm tra Server đang chạy, địa chỉ IP và kết nối LAN."
        )
    return ApiError(f"Không thể {action}. Vui lòng kiểm tra mạng LAN và thử lại.")


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
                try:
                    config = json.loads(example.read_text(encoding="utf-8"))
                except (OSError, ValueError) as exc:
                    raise ApiError(f"Không đọc được cấu hình mẫu: {exc}") from exc
            else:
                config = {
                    "server_url": "http://127.0.0.1:8000",
                    "verify_tls": True,
                    "discovery_port": 37020,
                    "request_timeout_seconds": 10,
                }
        else:
            try:
                config = json.loads(self.config_path.read_text(encoding="utf-8"))
            except OSError as exc:
                raise ApiError(f"Không đọc được tệp cấu hình: {exc}") from exc
            except ValueError as exc:
                raise ApiError("Tệp config.json không đúng định dạng JSON.") from exc
        if not isinstance(config, dict) or not isinstance(config.get("server_url"), str):
            raise ApiError("Tệp config.json thiếu địa chỉ server_url.")
        if not config["server_url"].startswith(("http://", "https://")):
            raise ApiError("server_url trong config.json phải bắt đầu bằng http:// hoặc https://.")
        try:
            if int(config.get("discovery_port", 37020)) not in range(1, 65536):
                raise ValueError
            if float(config.get("request_timeout_seconds", 10)) <= 0:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise ApiError("Cổng khám phá hoặc thời gian chờ trong config.json không hợp lệ.") from exc
        return config

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
            raise _network_error(exc) from exc
        if response.status_code >= 400:
            raise _response_error(response)
        if response.status_code == 204:
            return None
        try:
            return response.json()
        except ValueError as exc:
            raise ApiError("Server trả về dữ liệu không đúng định dạng JSON.") from exc

    def clear_session(self):
        self.token = None
        self.role = None
        self.employee_id = None
        self.device_registration_pending = False

    def login(self, username: str, password: str, register_device: bool = True):
        self.clear_session()
        data = self.request(
            "POST",
            "/api/v1/auth/login",
            json={
                "username": username,
                "password": password,
                "device_fingerprint": self.device_fingerprint if register_device else None,
            },
        )
        self.token = data["access_token"]
        self.role = data["role"]
        self.employee_id = data["employee_id"]
        if not register_device:
            return data
        try:
            registered = self.request(
                "POST",
                "/api/v1/devices",
                json={"fingerprint": self.device_fingerprint, "device_name": socket.gethostname()},
            )
            self.device_registration_pending = not registered["approved"]
        except ApiError:
            try:
                self.request("POST", "/api/v1/auth/logout")
            except ApiError:
                pass
            self.clear_session()
            raise
        return data

    def attendance(self, action: str):
        return self.request(
            "POST",
            f"/api/v1/attendance/{action}",
            json={
                "device_fingerprint": self.device_fingerprint,
                "idempotency_key": str(uuid.uuid4()),
            },
        )

    def download(self, path: str, params: dict | None = None) -> bytes:
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = self._client.get(path, params=params, headers=headers)
        except httpx.HTTPError as exc:
            raise _network_error(exc, "tải tệp từ Server") from exc
        if response.status_code >= 400:
            raise _response_error(response)
        return response.content

    def discover(self, attempts: int = 3) -> str | None:
        port = int(self.config.get("discovery_port", 37020))
        for _ in range(attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    sock.settimeout(1.5)
                    sock.sendto(b"LAN_ATTENDANCE_DISCOVER_V1", ("255.255.255.255", port))
                    data, address = sock.recvfrom(512)
                    result = json.loads(data.decode("utf-8"))
                    scheme = "https" if result.get("https") else "http"
                    return f"{scheme}://{address[0]}:{result['port']}"
            except (TimeoutError, ValueError, KeyError):
                time.sleep(0.2)
            except OSError as exc:
                raise ApiError(f"Không thể tìm Server trong mạng LAN: {exc}") from exc
        return None

    def set_server(self, url: str):
        if not url.startswith(("http://", "https://")):
            raise ApiError("Địa chỉ Server phải bắt đầu bằng http:// hoặc https://.")
        updated_config = {**self.config, "server_url": url.rstrip("/")}
        try:
            self.config_path.write_text(
                json.dumps(updated_config, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            raise ApiError(f"Không thể lưu địa chỉ Server vào config.json: {exc}") from exc
        self.config = updated_config
        self._client.close()
        self._client = self._make_client()
