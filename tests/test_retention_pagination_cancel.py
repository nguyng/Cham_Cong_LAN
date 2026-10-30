from datetime import UTC, date, datetime, timedelta

from app.database.session import SessionLocal
from app.models.entities import IdempotencyRecord, LeaveBalance, LoginSession, User
from app.services.maintenance import cleanup_expired_records


def _future_workday():
    candidate = date.today() + timedelta(days=7)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def test_employee_can_cancel_approved_future_leave_and_balance_is_refunded(
    client, employee_headers, manager_headers
):
    with SessionLocal() as db:
        leave_type_id = db.query(LeaveBalance).one().leave_type_id
    start = _future_workday()
    created = client.post(
        "/api/v1/leaves",
        json={
            "leave_type_id": leave_type_id,
            "start_date": str(start),
            "end_date": str(start),
            "reason": "Nghỉ giải quyết việc gia đình",
        },
        headers=employee_headers,
    )
    assert created.status_code == 201, created.text
    leave_id = created.json()["id"]
    approved = client.post(
        f"/api/v1/leaves/{leave_id}/review",
        json={"approve": True, "note": "Đồng ý"},
        headers=manager_headers,
    )
    assert approved.status_code == 200
    with SessionLocal() as db:
        assert float(db.query(LeaveBalance).one().used_days) == 1

    cancelled = client.post(f"/api/v1/leaves/{leave_id}/cancel", headers=employee_headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"
    with SessionLocal() as db:
        assert float(db.query(LeaveBalance).one().used_days) == 0


def test_list_endpoint_returns_pagination_metadata(client, admin_headers):
    for index in range(1, 6):
        response = client.post(
            "/api/v1/departments",
            json={"code": f"P{index}", "name": f"Phòng {index}"},
            headers=admin_headers,
        )
        assert response.status_code == 201

    response = client.get(
        "/api/v1/departments",
        params={"page": 2, "page_size": 2},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["pagination"] == {"page": 2, "page_size": 2, "total": 6, "pages": 3}


def test_periodic_cleanup_removes_only_expired_records(employee_headers):
    now = datetime.now(UTC)
    with SessionLocal.begin() as db:
        user = db.query(User).filter_by(username="employee").one()
        db.add(
            IdempotencyRecord(
                user_id=user.id,
                operation="CHECK_IN",
                request_key="expired-request-key",
                response_data={},
                created_at=now - timedelta(days=2),
            )
        )
        db.add(
            LoginSession(
                id="expired-session",
                user_id=user.id,
                token_hash="expired-session-token-hash",
                client_ip="127.0.0.1",
                created_at=now - timedelta(days=10),
                expires_at=now - timedelta(days=8),
                revoked_at=now - timedelta(days=8),
            )
        )

    result = cleanup_expired_records(now)
    assert result["idempotency_records"] == 1
    assert result["login_sessions"] == 1
    with SessionLocal() as db:
        assert db.get(LoginSession, "expired-session") is None
        assert db.query(LoginSession).count() == 1
