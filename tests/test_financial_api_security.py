from src.main import app
from src.security import require_authenticated_user


def test_chatbot_accepts_matching_authenticated_account(
    client,
    auth_headers,
):
    app.dependency_overrides[require_authenticated_user] = (
        lambda: "customer-1"
    )

    try:
        response = client.post(
            "/api/v1/chatbot",
            headers=auth_headers,
            json={
                "user_id": "customer-1",
                "message": "Hello",
                "conversation_id": "security-test-matching",
                "history": [],
            },
        )
    finally:
        app.dependency_overrides.pop(
            require_authenticated_user,
            None,
        )

    assert response.status_code == 200


def test_chatbot_rejects_different_authenticated_account(
    client,
    auth_headers,
):
    app.dependency_overrides[require_authenticated_user] = (
        lambda: "customer-1"
    )

    try:
        response = client.post(
            "/api/v1/chatbot",
            headers=auth_headers,
            json={
                "user_id": "customer-2",
                "message": "Show my financial summary",
                "conversation_id": "security-test-mismatch",
                "history": [],
            },
        )
    finally:
        app.dependency_overrides.pop(
            require_authenticated_user,
            None,
        )

    assert response.status_code == 403
