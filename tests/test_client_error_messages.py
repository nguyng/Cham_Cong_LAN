import json
from pathlib import Path

import httpx
import pytest

from client.app.network.api import ApiClient, ApiError


@pytest.fixture
def runtime_path(request):
    directory = Path(".test-runtime") / "client-errors"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{request.node.name}.json"
    path.unlink(missing_ok=True)
    yield path
    path.unlink(missing_ok=True)


def api_with_transport(config_path, handler):
    api = ApiClient(config_path)
    api._client.close()
    api._client = httpx.Client(
        base_url="http://testserver",
        transport=httpx.MockTransport(handler),
    )
    return api


def test_validation_response_hides_field_names_and_system_details(runtime_path):
    def handler(request):
        return httpx.Response(
            422,
            request=request,
            json={
                "detail": [
                    {
                        "loc": ["body", "employee_code"],
                        "msg": "Field required",
                        "type": "missing",
                    }
                ]
            },
        )

    api = api_with_transport(runtime_path, handler)
    with pytest.raises(ApiError) as raised:
        api.request("POST", "/api/v1/employees", json={})

    assert raised.value.status_code == 422
    assert str(raised.value) == "Thông tin chưa hợp lệ. Vui lòng kiểm tra lại."
    assert "employee_code" not in str(raised.value)
    assert "422" not in str(raised.value)


def test_internal_server_error_hides_codes_and_english_details(runtime_path):
    def handler(request):
        return httpx.Response(
            500,
            request=request,
            json={"detail": "Internal Server Error. Mã lỗi: ABC123"},
        )

    api = api_with_transport(runtime_path, handler)
    with pytest.raises(ApiError) as raised:
        api.request("GET", "/api/v1/dashboard")

    assert str(raised.value) == "Hệ thống đang gặp sự cố. Vui lòng thử lại sau."
    assert "ABC123" not in str(raised.value)
    assert "500" not in str(raised.value)
    assert "Internal Server Error" not in str(raised.value)


def test_attendance_conflict_uses_a_short_vietnamese_message(runtime_path):
    def handler(request):
        return httpx.Response(
            409,
            request=request,
            json={"detail": "Chỉ được check-in trong giờ của ca làm đã phân"},
        )

    api = api_with_transport(runtime_path, handler)
    with pytest.raises(ApiError) as raised:
        api.request("POST", "/api/v1/attendance/check-in")

    assert str(raised.value) == "Chỉ check-in trong giờ ca đã phân."
    assert "409" not in str(raised.value)


def test_invalid_success_response_and_timeout_are_user_friendly(runtime_path):
    def invalid_json(request):
        return httpx.Response(200, request=request, content=b"not-json")

    api = api_with_transport(runtime_path, invalid_json)
    with pytest.raises(ApiError, match="Không đọc được dữ liệu"):
        api.request("GET", "/api/v1/dashboard")

    def timeout(request):
        raise httpx.ReadTimeout("timed out", request=request)

    api._client.close()
    api._client = httpx.Client(
        base_url="http://testserver",
        transport=httpx.MockTransport(timeout),
    )
    with pytest.raises(ApiError, match="Máy chủ không phản hồi"):
        api.request("GET", "/api/v1/dashboard")


def test_invalid_config_has_clear_startup_error(runtime_path):
    runtime_path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ApiError, match="Cấu hình ứng dụng không hợp lệ"):
        ApiClient(runtime_path)

    runtime_path.write_text(json.dumps({"verify_tls": False}), encoding="utf-8")
    with pytest.raises(ApiError, match="Thiếu địa chỉ máy chủ"):
        ApiClient(runtime_path)

    runtime_path.write_text(json.dumps({"server_url": "http://"}), encoding="utf-8")
    with pytest.raises(ApiError, match="Địa chỉ máy chủ không hợp lệ"):
        ApiClient(runtime_path)

    runtime_path.write_text(
        json.dumps({"server_url": "http://127.0.0.1:8000", "verify_tls": "false"}),
        encoding="utf-8",
    )
    with pytest.raises(ApiError, match="Thiết lập kết nối không hợp lệ"):
        ApiClient(runtime_path)


def test_attendance_sends_gps_coordinates(runtime_path):
    captured = {}

    def handler(request):
        captured.update(json.loads(request.content))
        return httpx.Response(201, request=request, json={"status": "OPEN"})

    api = api_with_transport(runtime_path, handler)
    api.attendance(
        "check-in",
        {
            "latitude": 10.776889,
            "longitude": 106.700806,
            "location_accuracy_meters": 8.5,
        },
    )

    assert captured["latitude"] == 10.776889
    assert captured["longitude"] == 106.700806
    assert captured["location_accuracy_meters"] == 8.5
    assert captured["device_fingerprint"]
    assert captured["idempotency_key"]


def test_attendance_sends_explicit_lan_ip_fallback(runtime_path):
    captured = {}

    def handler(request):
        captured.update(json.loads(request.content))
        return httpx.Response(201, request=request, json={"status": "OPEN"})

    api = api_with_transport(runtime_path, handler)
    api.attendance("check-in", use_lan_ip_fallback=True)

    assert captured["location_source"] == "LAN_IP_FALLBACK"
    assert "latitude" not in captured
    assert "longitude" not in captured


def test_server_validation_error_contains_field_details(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "", "password": ""},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"].startswith("Dữ liệu không hợp lệ:")
    assert payload["errors"]


def test_request_does_not_mutate_caller_headers(runtime_path):
    def handler(request):
        assert request.headers["authorization"] == "Bearer session-token"
        return httpx.Response(200, request=request, json={"ok": True})

    api = api_with_transport(runtime_path, handler)
    api.token = "session-token"
    headers = {"X-Request-Source": "test"}

    assert api.request("GET", "/api/v1/health", headers=headers) == {"ok": True}
    assert headers == {"X-Request-Source": "test"}


def test_websocket_token_is_sent_in_authorization_header(runtime_path):
    api = ApiClient(runtime_path)
    api.token = "private-session-token"

    assert api.websocket_url.endswith("/api/v1/ws")
    assert "private-session-token" not in api.websocket_url
    assert api.websocket_headers == {"Authorization": "Bearer private-session-token"}


def test_only_loopback_server_enables_coupled_shutdown(runtime_path):
    api = ApiClient(runtime_path)
    assert api.local_server is True

    api.config["server_url"] = "http://203.0.113.20:8000"
    assert api.local_server is False
