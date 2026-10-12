
import os
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

from src.main import app
from src.security import require_authenticated_user
from src.errors import ServiceError


def test_missing_authenticated_user_is_rejected():
    request = SimpleNamespace(state=SimpleNamespace())

    with pytest.raises(ServiceError) as exc:
        require_authenticated_user(request)

    assert exc.value.status_code == 401
    assert exc.value.error_code == "UNAUTHORIZED_USER"


def test_blank_authenticated_user_is_rejected():
    request = SimpleNamespace(
        state=SimpleNamespace(authenticated_user_id=" ")
    )

    with pytest.raises(ServiceError) as exc:
        require_authenticated_user(request)

    assert exc.value.status_code == 401
    assert exc.value.error_code == "UNAUTHORIZED_USER"


def test_verified_user_id_is_returned():
    request = SimpleNamespace(
        state=SimpleNamespace(authenticated_user_id="customer-1")
    )

    assert require_authenticated_user(request) == "customer-1"


def test_mock_financial_data_is_not_returned_as_real_data():
    from src.integration.backend_client import get_backend_client

    with pytest.raises(ServiceError) as exc:
        get_backend_client().get_user_financial_summary("test-user")

    assert exc.value.status_code == 503
    assert exc.value.error_code == "FINANCIAL_BACKEND_UNAVAILABLE"


def test_demo_transactions_are_not_used_as_real_financial_data(monkeypatch):
    from src.financial_assistant import service
    from src.schemas import ChatbotRequest

    def reject_demo_retrieval():
        raise AssertionError(
            "Financial questions must not access demo/RAG data"
        )

    monkeypatch.setattr(
        service,
        "get_retriever",
        reject_demo_retrieval,
    )

    # Prevent a real LLM request during this security test.
    monkeypatch.setattr(
        service,
        "get_llm_provider",
        lambda: SimpleNamespace(
            generate_reply=lambda *args, **kwargs: ("test reply", 0)
        ),
    )

    request = ChatbotRequest(
        user_id="customer-1",
        message="What is my balance?",
        conversation_id="demo-data-security-test",
        history=[],
    )

    with pytest.raises(ServiceError) as exc:
        service.handle_chat(request)

    assert exc.value.status_code == 503
    assert exc.value.error_code == "FINANCIAL_BACKEND_UNAVAILABLE"


def test_chatbot_rejects_missing_authenticated_identity(client, auth_headers):
    response = client.post(
        "/api/v1/chatbot",
        headers={
            "X-Internal-Token": auth_headers["X-Internal-Token"],
        },
        json={
            "user_id": "customer-1",
            "message": "Hello",
            "conversation_id": "security-test-1",
            "history": [],
        },
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "UNAUTHORIZED_USER"


def test_chatbot_rejects_access_to_another_account(client, auth_headers):
    app.dependency_overrides[require_authenticated_user] = (
        lambda: "customer-1"
    )

    try:
        response = client.post(
            "/api/v1/chatbot",
            headers=auth_headers,
            json={
                "user_id": "customer-2",
                "message": "Hello",
                "conversation_id": "security-test-2",
                "history": [],
            },
        )
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN_ACCOUNT_ACCESS"


def test_chatbot_accepts_matching_authenticated_account(client, auth_headers):
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
                "conversation_id": "security-test-3",
                "history": [],
            },
        )
    finally:
        app.dependency_overrides.pop(require_authenticated_user, None)

    assert response.status_code == 200
    assert response.json()["conversation_id"] == "security-test-3"
