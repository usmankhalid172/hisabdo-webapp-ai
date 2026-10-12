"""
Security tests for app.py.
Run with: pytest -q
These tests use the local demo-token route, which must not be enabled in production.
"""
from datetime import datetime, timedelta, timezone
import jwt
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def token(username):
    response = client.post("/demo-token", json={"username": username})
    assert response.status_code == 200
    return response.json()["access_token"]

def auth(token_value):
    return {"Authorization": f"Bearer {token_value}"}

def test_financial_endpoint_requires_authentication():
    response = client.get(
        "/financial-summary",
        params={"start_date": "2026-10-01", "end_date": "2026-11-01"},
    )
    assert response.status_code == 401

def test_user_sees_only_own_actual_records():
    alice = token("alice")
    response = client.get(
        "/financial-records",
        headers=auth(alice),
        params={
            "data_mode": "actual",
            "start_date": "2026-10-01",
            "end_date": "2026-11-01",
        },
    )
    assert response.status_code == 200
    records = response.json()
    assert records
    assert all(r["customer"] != "Customer B" for r in records)
    assert all(r["data_mode"] == "actual" for r in records)

def test_account_id_cannot_be_overridden_by_query_parameter():
    alice = token("alice")
    response = client.get(
        "/financial-summary",
        headers=auth(alice),
        params={
            "account_id": "acct_bob",
            "data_mode": "actual",
            "start_date": "2026-10-01",
            "end_date": "2026-11-01",
        },
    )
    assert response.status_code == 200
    assert response.json()["account_id"] == "acct_alice"
    assert response.json()["receivables_total"] == 1200.00

def test_demo_and_actual_records_are_separated():
    alice = token("alice")
    params = {
        "start_date": "2026-10-01",
        "end_date": "2026-11-01",
    }
    actual = client.get(
        "/financial-summary",
        headers=auth(alice),
        params={**params, "data_mode": "actual"},
    ).json()
    demo = client.get(
        "/financial-summary",
        headers=auth(alice),
        params={**params, "data_mode": "demo"},
    ).json()
    assert actual["receivables_total"] == 1200.00
    assert demo["receivables_total"] == 9999.00
    assert actual["data_mode"] == "actual"
    assert demo["data_mode"] == "demo"

def test_date_period_includes_start_and_excludes_end():
    alice = token("alice")
    response = client.get(
        "/financial-records",
        headers=auth(alice),
        params={
            "data_mode": "actual",
            "start_date": "2026-10-01",
            "end_date": "2026-10-05",
        },
    )
    assert response.status_code == 200
    records = response.json()
    assert any(r["id"] == "r1" for r in records)  # Oct 1 included
    assert not any(r["id"] == "r2" for r in records)  # Oct 5 excluded

def test_invalid_date_range_is_rejected():
    alice = token("alice")
    response = client.get(
        "/financial-summary",
        headers=auth(alice),
        params={
            "data_mode": "actual",
            "start_date": "2026-10-10",
            "end_date": "2026-10-01",
        },
    )
    assert response.status_code == 400

def test_invalid_token_is_rejected():
    response = client.get(
        "/me",
        headers=auth("this-is-not-a-valid-token"),
    )
    assert response.status_code == 401

def test_unknown_username_cannot_get_demo_token():
    response = client.post("/demo-token", json={"username": "mallory"})
    assert response.status_code == 401

def test_date_range_over_366_days_is_rejected():
    alice = token("alice")
    response = client.get(
        "/financial-summary",
        headers=auth(alice),
        params={
            "data_mode": "actual",
            "start_date": "2025-01-01",
            "end_date": "2026-02-02",
        },
    )
    assert response.status_code == 400

def test_expired_token_is_rejected():
    from app import JWT_SECRET, JWT_ALGORITHM

    expired_time = datetime.now(timezone.utc) - timedelta(minutes=1)

    expired_token = jwt.encode(
        {
            "sub": "user_alice",
            "account_id": "acct_alice",
            "role": "user",
            "exp": expired_time,
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    response = client.get(
        "/me",
        headers=auth(expired_token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"

def test_invalid_data_mode_is_rejected():
    alice = token("alice")

    response = client.get(
        "/financial-records",
        headers=auth(alice),
        params={
            "data_mode": "secret",
            "start_date": "2026-10-01",
            "end_date": "2026-11-01",
        },
    )

    assert response.status_code == 422
