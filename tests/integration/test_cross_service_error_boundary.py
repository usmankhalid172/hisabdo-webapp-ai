from __future__ import annotations

from typing import Any

import httpx
import pytest

from src.integration.cross_service_error_boundary import (
    CrossServiceErrorBoundary,
    ModelExecutionError,
)


class FakeResponse:
    def __init__(self, status_code: int, payload: Any = None, invalid_json: bool = False):
        self.status_code = status_code
        self.payload = payload
        self.invalid_json = invalid_json

    def json(self) -> Any:
        if self.invalid_json:
            raise ValueError("invalid json")
        return self.payload


class FakeAsyncClient:
    response: FakeResponse | None = None
    request_exception: Exception | None = None
    last_url: str | None = None
    last_payload: dict[str, Any] | None = None
    last_headers: dict[str, str] | None = None

    def __init__(self, *, timeout: httpx.Timeout):
        self.timeout = timeout

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, url: str, *, json: dict[str, Any], headers: dict[str, str]) -> FakeResponse:
        type(self).last_url = url
        type(self).last_payload = json
        type(self).last_headers = headers
        if type(self).request_exception:
            raise type(self).request_exception
        if type(self).response is None:
            raise AssertionError("Fake response is not configured.")
        return type(self).response


@pytest.fixture(autouse=True)
def reset_fake_client() -> None:
    FakeAsyncClient.response = None
    FakeAsyncClient.request_exception = None
    FakeAsyncClient.last_url = None
    FakeAsyncClient.last_payload = None
    FakeAsyncClient.last_headers = None


@pytest.fixture
def client() -> CrossServiceErrorBoundary:
    return CrossServiceErrorBoundary(
        base_url="http://ai-service.test",
        internal_token="test-token",
    )


@pytest.fixture
def patch_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)


@pytest.mark.asyncio
async def test_successful_chatbot_flow(client, patch_httpx) -> None:
    FakeAsyncClient.response = FakeResponse(
        200,
        {"reply": "Your balance is 45,230.50 PKR.", "conversation_id": "conv-1"},
    )
    result = await client.chatbot(
        user_id="user-1",
        message="What is my balance?",
        conversation_id="conv-1",
        request_id="req-1",
    )

    assert result.success
    assert result.data["reply"] == "Your balance is 45,230.50 PKR."
    assert FakeAsyncClient.last_url == "http://ai-service.test/api/v1/chatbot"
    assert FakeAsyncClient.last_headers["X-Internal-Token"] == "test-token"


@pytest.mark.asyncio
async def test_timeout_returns_standard_error(client, patch_httpx) -> None:
    FakeAsyncClient.request_exception = httpx.ReadTimeout("timeout")
    result = await client.chatbot(
        user_id="user-1",
        message="Hello",
        conversation_id="conv-1",
        request_id="req-timeout",
    )

    assert result.error == {
        "error_code": "AI_TIMEOUT",
        "message": "AI assistant is temporarily unavailable.",
        "request_id": "req-timeout",
    }


@pytest.mark.asyncio
async def test_rate_limit_returns_standard_error(client, patch_httpx) -> None:
    FakeAsyncClient.response = FakeResponse(429, {"detail": "Too many requests"})
    result = await client.chatbot(
        user_id="user-1",
        message="Hello",
        conversation_id="conv-1",
        request_id="req-429",
    )

    assert result.error["error_code"] == "AI_RATE_LIMITED"
    assert result.error["request_id"] == "req-429"


@pytest.mark.asyncio
async def test_empty_payload_is_rejected_without_network_call(client, patch_httpx) -> None:
    result = await client.post_json(
        endpoint="/api/v1/chatbot",
        payload={},
        request_id="req-empty",
    )

    assert result.error_code == "EMPTY_PAYLOAD"
    assert FakeAsyncClient.last_url is None


@pytest.mark.asyncio
async def test_unexpected_input_type_is_rejected(client, patch_httpx) -> None:
    result = await client.post_json(
        endpoint="/api/v1/chatbot",
        payload=["invalid"],
        request_id="req-type",
    )

    assert result.error_code == "INVALID_INPUT_TYPE"
    assert FakeAsyncClient.last_url is None


@pytest.mark.asyncio
async def test_authentication_failure_is_contained(client, patch_httpx) -> None:
    FakeAsyncClient.response = FakeResponse(401, {"detail": "Unauthorized"})
    result = await client.chatbot(
        user_id="user-1",
        message="Hello",
        conversation_id="conv-1",
        request_id="req-auth",
    )

    assert result.error_code == "AUTHENTICATION_ERROR"


@pytest.mark.asyncio
async def test_model_execution_failure_is_contained(client) -> None:
    async def failing_model() -> dict[str, Any]:
        raise ModelExecutionError("inference failed")

    result = await client.execute_model(
        failing_model,
        request_id="req-model",
    )

    assert result.error == {
        "error_code": "AI_MODEL_EXECUTION_ERROR",
        "message": "AI model execution failed.",
        "request_id": "req-model",
    }


@pytest.mark.asyncio
async def test_unexpected_model_exception_is_contained(client) -> None:
    async def failing_model() -> dict[str, Any]:
        raise RuntimeError("unexpected model failure")

    result = await client.execute_model(
        failing_model,
        request_id="req-model-2",
    )

    assert result.error_code == "INTERNAL_ERROR"


@pytest.mark.asyncio
async def test_invalid_json_response_is_contained(client, patch_httpx) -> None:
    FakeAsyncClient.response = FakeResponse(200, invalid_json=True)
    result = await client.chatbot(
        user_id="user-1",
        message="Hello",
        conversation_id="conv-1",
        request_id="req-json",
    )

    assert result.error_code == "INVALID_AI_RESPONSE"


@pytest.mark.asyncio
async def test_invalid_response_shape_is_contained(client, patch_httpx) -> None:
    FakeAsyncClient.response = FakeResponse(200, ["unexpected"])
    result = await client.categorize_expense(
        description="Groceries",
        amount=2500,
        request_id="req-shape",
    )

    assert result.error_code == "INVALID_AI_RESPONSE"


@pytest.mark.asyncio
async def test_connection_failure_is_contained(client, patch_httpx) -> None:
    FakeAsyncClient.request_exception = httpx.ConnectError("connection failed")
    result = await client.chatbot(
        user_id="user-1",
        message="Hello",
        conversation_id="conv-1",
        request_id="req-network",
    )

    assert result.error_code == "AI_SERVICE_UNAVAILABLE"
