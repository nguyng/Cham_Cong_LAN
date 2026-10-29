"""Read-only LAN/TLS checks plus an optional authenticated WebSocket round trip."""

import argparse
import getpass
import json
import socket
import ssl
import sys
from urllib.parse import urlparse

import httpx
from websockets.sync.client import connect


def tls_context(ca_file: str | None) -> ssl.SSLContext:
    return ssl.create_default_context(cafile=ca_file)


def discover(port: int, timeout: float) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(timeout)
        sock.sendto(b"LAN_ATTENDANCE_DISCOVER_V1", ("255.255.255.255", port))
        payload, address = sock.recvfrom(512)
    result = json.loads(payload.decode("utf-8"))
    if result.get("service") != "LAN Attendance" or result.get("protocol") != 1:
        raise RuntimeError("Phản hồi UDP không đúng giao thức LAN Attendance v1")
    result["address"] = address[0]
    return result


def websocket_round_trip(
    server_url: str,
    token: str,
    context: ssl.SSLContext | None,
    timeout: float,
) -> dict:
    parsed = urlparse(server_url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    url = f"{scheme}://{parsed.netloc}/api/v1/ws?token={token}"
    arguments = {"open_timeout": timeout, "close_timeout": timeout}
    if scheme == "wss":
        arguments["ssl"] = context
    with connect(url, **arguments) as websocket:
        connected = json.loads(websocket.recv(timeout=timeout))
        if connected.get("type") != "connected":
            raise RuntimeError("WebSocket không gửi sự kiện connected")
        websocket.send("ping")
        if websocket.recv(timeout=timeout) != "pong":
            raise RuntimeError("WebSocket không phản hồi pong")
    return connected


def main() -> int:
    parser = argparse.ArgumentParser(description="Nghiệm thu kết nối LAN Attendance từ máy Client")
    parser.add_argument(
        "--server-url", required=True, help="Ví dụ https://attendance.company.local:8000"
    )
    parser.add_argument("--ca-file", help="PEM của CA nội bộ; bỏ trống để dùng Windows trust store")
    parser.add_argument("--discovery-port", type=int, default=37020)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--skip-discovery", action="store_true")
    parser.add_argument("--username", help="Nếu có, kiểm tra thêm login và WebSocket")
    arguments = parser.parse_args()

    server_url = arguments.server_url.rstrip("/")
    parsed = urlparse(server_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        parser.error("--server-url phải là URL HTTP/HTTPS đầy đủ")
    context = tls_context(arguments.ca_file) if parsed.scheme == "https" else None
    checks: dict[str, object] = {}
    token = None

    try:
        with httpx.Client(
            base_url=server_url, verify=context or True, timeout=arguments.timeout
        ) as client:
            response = client.get("/api/v1/health")
            response.raise_for_status()
            health = response.json()
            if health.get("status") != "ok":
                raise RuntimeError("Health endpoint không trả trạng thái ok")
            checks["health"] = health

            if not arguments.skip_discovery:
                discovery = discover(arguments.discovery_port, arguments.timeout)
                if int(discovery["port"]) != (
                    parsed.port or (443 if parsed.scheme == "https" else 80)
                ):
                    raise RuntimeError("Cổng UDP discovery khác cổng trong server URL")
                if bool(discovery["https"]) != (parsed.scheme == "https"):
                    raise RuntimeError("Trạng thái HTTPS của UDP discovery không khớp server URL")
                checks["discovery"] = discovery

            if arguments.username:
                password = getpass.getpass("Mật khẩu (không hiển thị): ")
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": arguments.username, "password": password},
                )
                login.raise_for_status()
                token = login.json()["access_token"]
                checks["websocket"] = websocket_round_trip(
                    server_url, token, context, arguments.timeout
                )
                logout = client.post(
                    "/api/v1/auth/logout",
                    headers={"Authorization": f"Bearer {token}"},
                )
                logout.raise_for_status()
                token = None
                checks["authenticated_logout"] = True
    except (httpx.HTTPError, OSError, ValueError, KeyError, RuntimeError) as exc:
        print(
            json.dumps(
                {"ok": False, "error": str(exc), "checks": checks}, ensure_ascii=False, indent=2
            )
        )
        return 1

    print(json.dumps({"ok": True, "checks": checks}, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
