"""
Integration-style test: exercises the full request path (middleware ->
routing -> Pydantic validation -> service layer -> response) through a live
FastAPI TestClient, rather than calling service functions directly.
"""


def test_error_format_is_consistent_on_validation_failure(client, auth_headers):
    # amount missing -> 422, but must still come back in the shared error shape
    resp = client.post(
        "/api/v1/categorize",
        json={"description": "Something"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    body = resp.json()
    assert set(body.keys()) == {"error_code", "message", "request_id"}
    assert body["error_code"] == "VALIDATION_ERROR"


def test_openapi_schema_is_available(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    for expected in (
        "/api/v1/health",
        "/api/v1/version",
        "/api/v1/chatbot",
        "/api/v1/categorize",
        "/api/v1/categorize/batch",
    ):
        assert expected in paths


def test_full_flow_chatbot_then_categorize(client, auth_headers):
    chat_resp = client.post(
        "/api/v1/chatbot",
        json={
            "user_id": "user-42",
            "message": "How do I export my expenses?",
            "conversation_id": "conv-42",
            "history": [],
        },
        headers=auth_headers,
    )
    assert chat_resp.status_code == 200

    cat_resp = client.post(
        "/api/v1/categorize",
        json={"description": "Dinner at restaurant", "merchant": "Kolachi", "amount": 5600},
        headers=auth_headers,
    )
    assert cat_resp.status_code == 200
    assert cat_resp.json()["category"] == "Dining"
