from conftest import login


def test_login_success_failure_logout(client):
    assert (
        client.post(
            "/api/v1/auth/login", json={"username": "employee", "password": "wrong-pass"}
        ).status_code
        == 401
    )
    auth = login(client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    assert client.get("/api/v1/me", headers=headers).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/me", headers=headers).status_code == 401


def test_failed_login_lockout(client):
    for _ in range(5):
        client.post("/api/v1/auth/login", json={"username": "employee", "password": "wrong-pass"})
    response = client.post(
        "/api/v1/auth/login", json={"username": "employee", "password": "EmployeePass123!"}
    )
    assert response.status_code == 423


def test_role_authorization(client, employee_headers, admin_headers):
    payload = {"code": "HR", "name": "Nhân sự"}
    assert (
        client.post("/api/v1/departments", json=payload, headers=employee_headers).status_code
        == 403
    )
    assert (
        client.post("/api/v1/departments", json=payload, headers=admin_headers).status_code == 201
    )


def test_manager_employee_portal_scope_only_returns_own_data(client, manager_headers):
    department_schedule = client.get(
        "/api/v1/shift-assignments", params={"page": 1}, headers=manager_headers
    )
    own_schedule = client.get(
        "/api/v1/shift-assignments",
        params={"mine": True, "page": 1},
        headers=manager_headers,
    )
    department_dashboard = client.get("/api/v1/dashboard", headers=manager_headers)
    own_dashboard = client.get(
        "/api/v1/dashboard", params={"mine": True}, headers=manager_headers
    )

    assert department_schedule.status_code == 200
    assert own_schedule.status_code == 200
    assert department_schedule.json()["pagination"]["total"] == 1
    assert own_schedule.json()["pagination"]["total"] == 0
    assert department_dashboard.json()["total_employees"] == 3
    assert own_dashboard.json()["total_employees"] == 1


def test_change_password_revokes_sessions(client, employee_headers):
    response = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "EmployeePass123!", "new_password": "NewEmployeePass123!"},
        headers=employee_headers,
    )
    assert response.status_code == 204
    assert client.get("/api/v1/me", headers=employee_headers).status_code == 401
