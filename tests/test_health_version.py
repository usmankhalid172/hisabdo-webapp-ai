def test_health_is_public_and_ok(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_version_returns_service_info(client):
    resp = client.get("/api/v1/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "hisabdo-ai-service"
    assert body["model_provider"] == "mock"


def test_protected_endpoint_rejects_missing_token(client):
    resp = client.post("/api/v1/categorize", json={"description": "Groceries", "amount": 100})
    assert resp.status_code == 401
    body = resp.json()
    assert body["error_code"] == "UNAUTHORIZED_SERVICE"
    assert "request_id" in body


def test_protected_endpoint_accepts_valid_token(client, auth_headers):
    resp = client.post(
        "/api/v1/categorize",
        json={"description": "Grocery shopping", "amount": 100},
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_correlation_id_echoed_back(client, auth_headers):
    resp = client.get("/api/v1/health", headers={"X-Request-ID": "abc-123"})
    assert resp.headers["X-Request-ID"] == "abc-123"

    resp2 = client.get("/api/v1/health")
    assert "X-Request-ID" in resp2.headers  # auto-generated when absent
