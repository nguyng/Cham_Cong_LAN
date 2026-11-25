from datetime import UTC, datetime, timedelta

from app.database.session import SessionLocal
from app.models.entities import LoginSession, User
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
    scheduled_shift = department_schedule.json()["items"][0]
    assert scheduled_shift["shift_code"] == "HC"
    assert scheduled_shift["shift_start_time"] == "00:00"
    assert scheduled_shift["shift_end_time"] == "23:59"
    assert scheduled_shift["work_timezone"] == "Asia/Ho_Chi_Minh"
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


def test_current_admin_cannot_remove_own_admin_access(client, admin_headers):
    with SessionLocal() as db:
        admin = db.query(User).filter_by(username="admin").one()
        admin_id = admin.id
        employee_id = admin.employee_id

    demote = client.patch(
        f"/api/v1/users/{admin_id}/role",
        params={"role": "EMPLOYEE"},
        headers=admin_headers,
    )
    deactivate = client.patch(
        f"/api/v1/employees/{employee_id}/active",
        params={"active": False},
        headers=admin_headers,
    )

    assert demote.status_code == 409
    assert deactivate.status_code == 409
    assert client.get("/api/v1/me", headers=admin_headers).status_code == 200


def test_role_change_revokes_target_sessions(client, admin_headers, manager_headers):
    with SessionLocal() as db:
        manager_id = db.query(User).filter_by(username="manager").one().id

    changed = client.patch(
        f"/api/v1/users/{manager_id}/role",
        params={"role": "EMPLOYEE"},
        headers=admin_headers,
    )

    assert changed.status_code == 200
    assert client.get("/api/v1/me", headers=manager_headers).status_code == 401


def test_root_admin_is_hidden_and_protected_from_later_admins(client, admin_headers):
    with SessionLocal.begin() as db:
        root = db.query(User).filter_by(username="admin").one()
        root_id = root.id
        root_employee_id = root.employee_id
    created = client.post(
        "/api/v1/employees",
        json={
            "employee_code": "AD002",
            "full_name": "Quản trị thứ hai",
            "email": "admin2@example.com",
            "username": "admin2",
            "temporary_password": "AdminTwoPass123!",
            "role": "ADMIN",
        },
        headers=admin_headers,
    )
    assert created.status_code == 201

    admin2 = login(client, "admin2", "AdminTwoPass123!")
    admin2_headers = {"Authorization": f"Bearer {admin2['access_token']}"}

    visible_users = client.get("/api/v1/users", params={"page": 1}, headers=admin2_headers)
    assert visible_users.status_code == 200
    assert [item["username"] for item in visible_users.json()["items"]] == ["admin"]
    assert visible_users.json()["items"][0]["is_root_admin"] is True

    assert (
        client.patch(
            f"/api/v1/users/{root_id}/role",
            params={"role": "EMPLOYEE"},
            headers=admin2_headers,
        ).status_code
        == 403
    )
    assert (
        client.post(f"/api/v1/users/{root_id}/unlock", headers=admin2_headers).status_code == 403
    )
    assert (
        client.delete(
            "/api/v1/admin/records/users",
            params={"identifier": root_id},
            headers=admin2_headers,
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/api/v1/employees/{root_employee_id}/active",
            params={"active": False},
            headers=admin2_headers,
        ).status_code
        == 403
    )
    assert (
        client.put(
            f"/api/v1/employees/{root_employee_id}",
            json={
                "full_name": "Đã sửa",
                "email": "admin-updated@example.com",
            },
            headers=admin2_headers,
        ).status_code
        == 403
    )
    assert client.get("/api/v1/me", headers=admin2_headers).json()["is_root_admin"] is False
    assert client.get("/api/v1/me", headers=admin_headers).json()["is_root_admin"] is True
    root_users = client.get("/api/v1/users", params={"page": 1}, headers=admin_headers)
    assert {item["username"] for item in root_users.json()["items"]} >= {
        "admin",
        "admin2",
        "manager",
        "employee",
    }
    admin2_id = next(
        item["id"] for item in root_users.json()["items"] if item["username"] == "admin2"
    )
    assert (
        client.delete(
            "/api/v1/admin/records/users",
            params={"identifier": admin2_id},
            headers=admin_headers,
        ).status_code
        == 204
    )
    active_users = client.get("/api/v1/users", params={"page": 1}, headers=admin_headers)
    assert "admin2" not in {item["username"] for item in active_users.json()["items"]}
    archived_users = client.get(
        "/api/v1/users", params={"page": 1, "active": False}, headers=admin_headers
    )
    assert "admin2" not in {item["username"] for item in archived_users.json()["items"]}


def test_read_only_request_persists_session_last_seen(client, employee_headers):
    old_time = datetime.now(UTC) - timedelta(days=1)
    with SessionLocal.begin() as db:
        session = db.query(LoginSession).filter(LoginSession.revoked_at.is_(None)).one()
        session.last_seen_at = old_time
        session_id = session.id

    assert client.get("/api/v1/me", headers=employee_headers).status_code == 200
    with SessionLocal() as db:
        updated = db.get(LoginSession, session_id).last_seen_at.replace(tzinfo=UTC)
        assert updated > old_time + timedelta(hours=23)
