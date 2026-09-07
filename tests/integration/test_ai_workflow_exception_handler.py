"""Tests for Task 26 fault-tolerant workflow handling."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from src.integration.ai_workflow_exception_handler import (
    Task26WorkflowClient,
    CHATBOT_FALLBACK,
    CATEGORIZATION_FALLBACK,
)

class FakeResponse:
    """Minimal fake response for deterministic workflow tests."""

    def __init__(
        self,
        status_code: int,
        payload: Any = None,
        *,
        invalid_json: bool = False,
    ) -> None:
        self.status_code = status_code
        self.payload = payload
        self.invalid_json = invalid_json

    def json(self) -> Any:
        if self.invalid_json:
            raise ValueError("invalid JSON")
        return self.payload


class FakeAsyncClient:
    """Fake HTTP client that records outgoing workflow requests."""

    response: FakeResponse | None = None
    request_exception: Exception | None = None
    last_url: str | None = None
    last_payload: dict[str, Any] | None = None
    last_headers: dict[str, str] | None = None

    def __init__(self, *, timeout: httpx.Timeout) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(
        self,
        url: str,
        *,
        json: dict[str, Any],
        headers: dict[str, str],
    ) -> FakeResponse:
        type(self).last_url = url
        type(self).last_payload = json
        type(self).last_headers = headers

        if type(self).request_exception is not None:
            raise type(self).request_exception

        if type(self).response is None:
            raise AssertionError("No fake response configured.")

        return type(self).response


@pytest.fixture(autouse=True)
def reset_fake_client() -> None:
    FakeAsyncClient.response = None
    FakeAsyncClient.request_exception = None
    FakeAsyncClient.last_url = None
    FakeAsyncClient.last_payload = None
    FakeAsyncClient.last_headers = None


@pytest.fixture
def client() -> Task26WorkflowClient:
    return Task26WorkflowClient(
        base_url="http://ai-service.test",
        internal_token="test-token",
    )


@pytest.fixture
def patch_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)


@pytest.mark.asyncio
async def test_chatbot_successfully_transmits_data(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        200,
        {
            "reply": "Your balance is 45,230.50 PKR.",
            "conversation_id": "conv-001",
            "intent": "own_financial_data",
            "source": "backend_financial_api",
        },
    )

    result = await client.chatbot(
        user_id="user-001",
        message="What is my balance?",
        conversation_id="conv-001",
    )

    assert result.is_success
    assert result.data["reply"] == "Your balance is 45,230.50 PKR."
    assert FakeAsyncClient.last_url == (
        "http://ai-service.test/api/v1/chatbot"
    )
    assert FakeAsyncClient.last_headers["X-Internal-Token"] == "test-token"


@pytest.mark.asyncio
async def test_expense_categorization_successfully_transmits_data(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        200,
        {
            "category": "Shopping",
            "confidence": 0.94,
            "alternative_categories": [],
            "needs_confirmation": False,
            "method": "ml_model",
        },
    )

    result = await client.categorize_expense(
        description="Bought groceries",
        amount=2500,
        merchant="Carrefour",
    )

    assert result.is_success
    assert result.data["category"] == "Shopping"
    assert FakeAsyncClient.last_url == (
        "http://ai-service.test/api/v1/categorize"
    )


@pytest.mark.asyncio
async def test_empty_user_payload_is_rejected_before_network_call(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    result = await client.chatbot(
        user_id="user-001",
        message="",
        conversation_id="conv-001",
    )

    assert result.status == "fallback"
    assert result.error_code == "EMPTY_PAYLOAD"
    assert FakeAsyncClient.last_url is None


@pytest.mark.asyncio
async def test_unexpected_input_type_is_rejected(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    result = await client.chatbot(
        user_id=123,  # type: ignore[arg-type]
        message="Hello",
        conversation_id="conv-001",
    )

    assert result.status == "fallback"
    assert result.error_code == "INVALID_INPUT_TYPE"
    assert result.message == CHATBOT_FALLBACK
    assert FakeAsyncClient.last_url is None


@pytest.mark.asyncio
async def test_timeout_uses_safe_fallback(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.request_exception = httpx.ReadTimeout(
        "request timed out"
    )

    result = await client.chatbot(
        user_id="user-001",
        message="Hello",
        conversation_id="conv-001",
    )

    assert result.status == "fallback"
    assert result.error_code == "AI_TIMEOUT"
    assert result.data["http_status"] == 504
    assert result.message == CHATBOT_FALLBACK


@pytest.mark.asyncio
async def test_rate_limit_uses_safe_fallback(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        429,
        {"detail": "Too many requests"},
    )

    result = await client.chatbot(
        user_id="user-001",
        message="Hello",
        conversation_id="conv-001",
    )

    assert result.status == "fallback"
    assert result.error_code == "AI_RATE_LIMITED"
    assert result.data["http_status"] == 429
    assert "rate limited" in result.message.lower()


@pytest.mark.asyncio
async def test_authentication_failure_is_mapped(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        401,
        {"detail": "Unauthorized"},
    )

    result = await client.chatbot(
        user_id="user-001",
        message="Hello",
        conversation_id="conv-001",
    )

    assert result.status == "fallback"
    assert result.error_code == "AUTHENTICATION_ERROR"
    assert result.data["http_status"] == 401


@pytest.mark.asyncio
async def test_model_execution_failure_uses_service_fallback(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        500,
        {"detail": "Model execution failed"},
    )

    result = await client.chatbot(
        user_id="user-001",
        message="Hello",
        conversation_id="conv-001",
    )

    assert result.status == "fallback"
    assert result.error_code == "AI_SERVICE_UNAVAILABLE"
    assert result.data["http_status"] == 500
    assert result.message == CHATBOT_FALLBACK


@pytest.mark.asyncio
async def test_invalid_json_response_uses_fallback(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        200,
        invalid_json=True,
    )

    result = await client.chatbot(
        user_id="user-001",
        message="Hello",
        conversation_id="conv-001",
    )

    assert result.status == "fallback"
    assert result.error_code == "INVALID_AI_RESPONSE"
    assert result.data["http_status"] == 502


@pytest.mark.asyncio
async def test_unexpected_response_structure_uses_fallback(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        200,
        ["unexpected", "list"],
    )

    result = await client.categorize_expense(
        description="Bought groceries",
        amount=2500,
    )

    assert result.status == "fallback"
    assert result.error_code == "INVALID_AI_RESPONSE"
    assert result.message == CATEGORIZATION_FALLBACK


@pytest.mark.asyncio
async def test_connection_failure_uses_unavailable_fallback(
    client: Task26WorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.request_exception = httpx.ConnectError(
        "connection failed"
    )

    result = await client.chatbot(
        user_id="user-001",
        message="Hello",
        conversation_id="conv-001",
    )

    assert result.status == "fallback"
    assert result.error_code == "AI_SERVICE_UNAVAILABLE"
    assert result.data["http_status"] == 503
