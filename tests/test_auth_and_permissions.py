from conftest import login


def test_login_success_failure_logout(client):
    assert client.post("/api/v1/auth/login", json={"username": "employee", "password": "wrong-pass"}).status_code == 401
    auth = login(client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    assert client.get("/api/v1/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/me", headers=headers).status_code == 401


def test_failed_login_lockout(client):
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"username": "employee", "password": "wrong-pass"})
    response = client.post("/api/v1/auth/login", json={"username": "employee", "password": "EmployeePass123!"})
    assert response.status_code == 423


def test_role_authorization(client, employee_headers, admin_headers):
    payload = {"code": "HR", "name": "Nhân sự"}
    assert client.post("/api/v1/departments", json=payload, headers=employee_headers).status_code == 403
    assert client.post("/api/v1/departments", json=payload, headers=admin_headers).status_code == 201


def test_change_password_revokes_sessions(client, employee_headers):
    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "EmployeePass123!", "new_password": "NewEmployeePass123!"},
        headers=employee_headers,
    )
    assert response.status_code == 204
    assert client.get("/api/v1/me", headers=employee_headers).status_code == 401
