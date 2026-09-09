"""Tests for the Capstone application-side AI client.

These tests verify application-to-AI transport and response handling without
calling a live AI service. The AI service itself is treated as a downstream
dependency and is replaced with a small deterministic fake HTTP client.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx
import pytest

from src.integration.application_ai_client import (
    AIServiceConfigurationError,
    AIServiceError,
    AIServiceResponseError,
    AIServiceTimeoutError,
    ApplicationAIClient,
)


@dataclass
class FakeResponse:
    """Minimal response object needed by ApplicationAIClient._post."""

    status_code: int
    payload: Any = None
    json_error: bool = False

    def json(self) -> Any:
        if self.json_error:
            raise ValueError("invalid json")
        return self.payload


class FakeAsyncClient:
    """Deterministic async HTTP client used to test the application boundary."""

    response: FakeResponse | None = None
    request_exception: Exception | None = None
    last_url: str | None = None
    last_headers: dict[str, str] | None = None
    last_payload: dict[str, Any] | None = None

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
            raise AssertionError("Fake response was not configured")

        return type(self).response


@pytest.fixture(autouse=True)
def reset_fake_client() -> None:
    """Reset fake state before every test."""
    FakeAsyncClient.response = None
    FakeAsyncClient.request_exception = None
    FakeAsyncClient.last_url = None
    FakeAsyncClient.last_headers = None
    FakeAsyncClient.last_payload = None


@pytest.fixture
def client() -> ApplicationAIClient:
    return ApplicationAIClient(
        base_url="http://ai-service.test",
        internal_token="test-internal-token",
    )


def _patch_http_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        FakeAsyncClient,
    )


@pytest.mark.asyncio
async def test_chatbot_sends_contract_and_returns_normalized_response(
    monkeypatch: pytest.MonkeyPatch,
    client: ApplicationAIClient,
) -> None:
    _patch_http_client(monkeypatch)

    FakeAsyncClient.response = FakeResponse(
        status_code=200,
        payload={
            "reply": "Your expenses this month are 18,420 PKR.",
            "conversation_id": "conv-001",
            "intent": "own_financial_data",
            "tokens_used": 150,
            "source": "backend_financial_api",
        },
    )

    result = await client.chatbot(
        user_id="user-001",
        message="How much did I spend this month?",
        conversation_id="conv-001",
    )

    assert result.reply == "Your expenses this month are 18,420 PKR."
    assert result.conversation_id == "conv-001"
    assert result.intent == "own_financial_data"
    assert result.source == "backend_financial_api"

    assert FakeAsyncClient.last_url == (
        "http://ai-service.test/api/v1/chatbot"
    )
    assert FakeAsyncClient.last_payload == {
        "user_id": "user-001",
        "message": "How much did I spend this month?",
        "conversation_id": "conv-001",
        "history": [],
    }
    assert FakeAsyncClient.last_headers == {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Internal-Token": "test-internal-token",
    }


@pytest.mark.asyncio
async def test_chatbot_preserves_history(
    monkeypatch: pytest.MonkeyPatch,
    client: ApplicationAIClient,
) -> None:
    _patch_http_client(monkeypatch)

    FakeAsyncClient.response = FakeResponse(
        status_code=200,
        payload={
            "reply": "You spent 1000 PKR.",
            "conversation_id": "conv-002",
            "intent": "own_financial_data",
            "source": "backend_financial_api",
        },
    )

    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ]

    await client.chatbot(
        user_id="user-002",
        message="What did I spend?",
        conversation_id="conv-002",
        history=history,
    )

    assert FakeAsyncClient.last_payload is not None
    assert FakeAsyncClient.last_payload["history"] == history


@pytest.mark.asyncio
async def test_categorize_expense_returns_prediction(
    monkeypatch: pytest.MonkeyPatch,
    client: ApplicationAIClient,
) -> None:
    _patch_http_client(monkeypatch)

    FakeAsyncClient.response = FakeResponse(
        status_code=200,
        payload={
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
        amount=2500.0,
        merchant="Carrefour",
        currency="PKR",
    )

    assert result.category == "Shopping"
    assert result.confidence == 0.94
    assert result.alternative_categories == ["Groceries"]
    assert result.needs_confirmation is False
    assert result.method == "ml_model"

    assert FakeAsyncClient.last_url == (
        "http://ai-service.test/api/v1/categorize"
    )


def test_missing_internal_token_is_rejected() -> None:
    with pytest.raises(AIServiceConfigurationError) as exc_info:
        ApplicationAIClient(
            base_url="http://ai-service.test",
            internal_token="",
        )

    assert exc_info.value.error_code == "AI_SERVICE_CONFIGURATION_ERROR"


@pytest.mark.asyncio
async def test_timeout_is_mapped_to_application_error(
    monkeypatch: pytest.MonkeyPatch,
    client: ApplicationAIClient,
) -> None:
    _patch_http_client(monkeypatch)

    FakeAsyncClient.request_exception = httpx.ReadTimeout("timed out")

    with pytest.raises(AIServiceTimeoutError) as exc_info:
        await client.chatbot(
            user_id="user-001",
            message="Hello",
            conversation_id="conv-003",
        )

    assert exc_info.value.status_code == 504
    assert exc_info.value.error_code == "AI_TIMEOUT"


@pytest.mark.asyncio
async def test_authentication_failure_is_exposed_as_application_error(
    monkeypatch: pytest.MonkeyPatch,
    client: ApplicationAIClient,
) -> None:
    _patch_http_client(monkeypatch)

    FakeAsyncClient.response = FakeResponse(
        status_code=401,
        payload={"detail": "Unauthorized"},
    )

    with pytest.raises(AIServiceError) as exc_info:
        await client.chatbot(
            user_id="user-001",
            message="Hello",
            conversation_id="conv-004",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.error_code == "AI_AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_invalid_chatbot_response_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    client: ApplicationAIClient,
) -> None:
    _patch_http_client(monkeypatch)

    FakeAsyncClient.response = FakeResponse(
        status_code=200,
        payload={
            "unexpected": "payload",
        },
    )

    with pytest.raises(AIServiceResponseError) as exc_info:
        await client.chatbot(
            user_id="user-001",
            message="Hello",
            conversation_id="conv-005",
        )

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "INVALID_AI_RESPONSE"


@pytest.mark.asyncio
async def test_invalid_json_response_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    client: ApplicationAIClient,
) -> None:
    _patch_http_client(monkeypatch)

    FakeAsyncClient.response = FakeResponse(
        status_code=200,
        json_error=True,
    )

    with pytest.raises(AIServiceResponseError):
        await client.categorize_expense(
            description="Bought groceries",
            amount=2500.0,
        )
