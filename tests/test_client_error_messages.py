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


def test_validation_response_is_converted_to_readable_warning(runtime_path):
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
    assert "Thông tin chưa hợp lệ" in str(raised.value)
    assert "employee_code: không được để trống" in str(raised.value)


def test_invalid_success_response_and_timeout_are_user_friendly(runtime_path):
    def invalid_json(request):
        return httpx.Response(200, request=request, content=b"not-json")

    api = api_with_transport(runtime_path, invalid_json)
    with pytest.raises(ApiError, match="không đúng định dạng JSON"):
        api.request("GET", "/api/v1/dashboard")

    def timeout(request):
        raise httpx.ReadTimeout("timed out", request=request)

    api._client.close()
    api._client = httpx.Client(
        base_url="http://testserver",
        transport=httpx.MockTransport(timeout),
    )
    with pytest.raises(ApiError, match="Server không phản hồi"):
        api.request("GET", "/api/v1/dashboard")


def test_invalid_config_has_clear_startup_error(runtime_path):
    runtime_path.write_text("{invalid", encoding="utf-8")

    with pytest.raises(ApiError, match="không đúng định dạng JSON"):
        ApiClient(runtime_path)

    runtime_path.write_text(json.dumps({"verify_tls": False}), encoding="utf-8")
    with pytest.raises(ApiError, match="thiếu địa chỉ server_url"):
        ApiClient(runtime_path)


def test_server_validation_error_contains_field_details(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "", "password": ""},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"].startswith("Dữ liệu không hợp lệ:")
    assert payload["errors"]
