"""Tests for the Task 23-24 end-to-end workflow client.

The tests use mocked HTTP responses so no live AI service or credentials are
required. They verify both successful data transmission and the required
fallback/error scenarios.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from src.integration.workflow_client import (
    AIWorkflowClient,
    EmptyPayloadError,
    InvalidInputTypeError,
    WorkflowResponseError,
    WorkflowServiceError,
    WorkflowTimeoutError,
)


class FakeResponse:
    """Small HTTP response stand-in for deterministic integration tests."""

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
            raise ValueError("invalid json")
        return self.payload


class FakeAsyncClient:
    """Fake async HTTP client that records the outgoing workflow request."""

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
def client() -> AIWorkflowClient:
    return AIWorkflowClient(
        base_url="http://ai-service.test",
        internal_token="test-token",
    )


@pytest.fixture
def patch_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)


@pytest.mark.asyncio
async def test_chatbot_transmits_data_and_returns_ai_output(
    client: AIWorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        200,
        {
            "reply": "Your balance is 45,230.50 PKR.",
            "conversation_id": "conv-001",
            "intent": "own_financial_data",
            "tokens_used": 120,
            "source": "backend_financial_api",
        },
    )

    result = await client.chatbot(
        user_id="user-001",
        message="What is my balance?",
        conversation_id="conv-001",
    )

    assert result["reply"] == "Your balance is 45,230.50 PKR."
    assert result["conversation_id"] == "conv-001"
    assert FakeAsyncClient.last_url == (
        "http://ai-service.test/api/v1/chatbot"
    )
    assert FakeAsyncClient.last_payload == {
        "user_id": "user-001",
        "message": "What is my balance?",
        "conversation_id": "conv-001",
        "history": [],
    }
    assert FakeAsyncClient.last_headers["X-Internal-Token"] == "test-token"


@pytest.mark.asyncio
async def test_expense_workflow_transmits_data_and_returns_category(
    client: AIWorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        200,
        {
            "category": "Shopping",
            "confidence": 0.94,
            "alternative_categories": ["Groceries"],
            "needs_confirmation": False,
            "method": "ml_model",
        },
    )

    result = await client.categorize_expense(
        expense_id="exp-001",
        description="Bought groceries",
        amount=2500,
        merchant="Carrefour",
    )

    assert result["category"] == "Shopping"
    assert result["confidence"] == 0.94
    assert FakeAsyncClient.last_url == (
        "http://ai-service.test/api/v1/categorize"
    )


@pytest.mark.asyncio
async def test_empty_payload_is_rejected_before_network_call(
    client: AIWorkflowClient,
    patch_httpx: None,
) -> None:
    with pytest.raises(EmptyPayloadError) as exc_info:
        await client.categorize_expense(
            description="",
            amount=2500,
        )

    assert exc_info.value.error_code == "EMPTY_PAYLOAD"
    assert FakeAsyncClient.last_url is None


@pytest.mark.asyncio
async def test_unexpected_input_type_is_rejected(
    client: AIWorkflowClient,
    patch_httpx: None,
) -> None:
    with pytest.raises(InvalidInputTypeError) as exc_info:
        await client.chatbot(
            user_id=123,  # type: ignore[arg-type]
            message="Hello",
            conversation_id="conv-001",
        )

    assert exc_info.value.error_code == "INVALID_INPUT_TYPE"
    assert FakeAsyncClient.last_url is None


@pytest.mark.asyncio
async def test_timeout_uses_predictable_fallback_error(
    client: AIWorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.request_exception = httpx.ReadTimeout(
        "request timed out"
    )

    with pytest.raises(WorkflowTimeoutError) as exc_info:
        await client.chatbot(
            user_id="user-001",
            message="Hello",
            conversation_id="conv-001",
        )

    assert exc_info.value.error_code == "AI_TIMEOUT"
    assert exc_info.value.status_code == 504


@pytest.mark.asyncio
async def test_authentication_failure_is_mapped(
    client: AIWorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        401,
        {"detail": "Unauthorized"},
    )

    with pytest.raises(WorkflowServiceError) as exc_info:
        await client.chatbot(
            user_id="user-001",
            message="Hello",
            conversation_id="conv-001",
        )

    assert exc_info.value.error_code == "AUTHENTICATION_ERROR"
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_invalid_json_response_is_rejected(
    client: AIWorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        200,
        invalid_json=True,
    )

    with pytest.raises(WorkflowResponseError) as exc_info:
        await client.chatbot(
            user_id="user-001",
            message="Hello",
            conversation_id="conv-001",
        )

    assert exc_info.value.error_code == "INVALID_AI_RESPONSE"


@pytest.mark.asyncio
async def test_unexpected_response_structure_is_rejected(
    client: AIWorkflowClient,
    patch_httpx: None,
) -> None:
    FakeAsyncClient.response = FakeResponse(
        200,
        ["not", "an", "object"],
    )

    with pytest.raises(WorkflowResponseError) as exc_info:
        await client.categorize_expense(
            description="Bought groceries",
            amount=2500,
        )

    assert exc_info.value.status_code == 502
