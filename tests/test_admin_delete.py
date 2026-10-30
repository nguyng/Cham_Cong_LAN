from app.database.session import SessionLocal
from app.models.entities import Department, ShiftAssignment, User


def test_only_admin_can_remove_records(client, manager_headers):
    with SessionLocal() as db:
        assignment_id = db.query(ShiftAssignment.id).first()[0]

    response = client.delete(
        "/api/v1/admin/records/shift-assignments",
        params={"identifier": assignment_id},
        headers=manager_headers,
    )

    assert response.status_code == 403
    with SessionLocal() as db:
        assert db.get(ShiftAssignment, assignment_id) is not None


def test_admin_can_delete_transaction_record(client, admin_headers):
    with SessionLocal() as db:
        assignment_id = db.query(ShiftAssignment.id).first()[0]

    response = client.delete(
        "/api/v1/admin/records/shift-assignments",
        params={"identifier": assignment_id},
        headers=admin_headers,
    )

    assert response.status_code == 204
    with SessionLocal() as db:
        assert db.get(ShiftAssignment, assignment_id) is None


def test_admin_delete_archives_master_data(client, admin_headers):
    with SessionLocal.begin() as db:
        department = Department(code="TMP", name="Phòng tạm")
        db.add(department)
        db.flush()
        department_id = department.id

    response = client.delete(
        "/api/v1/admin/records/departments",
        params={"identifier": department_id},
        headers=admin_headers,
    )

    assert response.status_code == 204
    with SessionLocal() as db:
        assert db.get(Department, department_id).active is False


def test_admin_cannot_remove_current_account(client, admin_headers):
    with SessionLocal() as db:
        admin_id = db.query(User.id).filter(User.username == "admin").scalar()

    response = client.delete(
        "/api/v1/admin/records/users",
        params={"identifier": admin_id},
        headers=admin_headers,
    )

    assert response.status_code == 409
    assert "đang đăng nhập" in response.json()["detail"]


def test_deleted_pending_device_can_be_registered_again(client, employee_headers, admin_headers):
    payload = {"fingerprint": "temporary-workstation", "device_name": "Máy tạm"}
    registered = client.post("/api/v1/devices", json=payload, headers=employee_headers)
    assert registered.status_code == 201

    removed = client.delete(
        "/api/v1/admin/records/devices",
        params={"identifier": registered.json()["id"]},
        headers=admin_headers,
    )
    assert removed.status_code == 204

    registered_again = client.post("/api/v1/devices", json=payload, headers=employee_headers)
    assert registered_again.status_code == 201
