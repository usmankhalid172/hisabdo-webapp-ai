from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping

import httpx

DEFAULT_TIMEOUT_SECONDS = 15.0
CHATBOT_ENDPOINT = "/api/v1/chatbot"
CATEGORIZE_ENDPOINT = "/api/v1/categorize"


@dataclass(slots=True)
class BoundaryResult:
    """Controlled result returned to the parent application."""

    success: bool
    data: dict[str, Any] | None = None
    error: dict[str, Any] | None = None

    @property
    def error_code(self) -> str | None:
        return self.error.get("error_code") if self.error else None


class ModelExecutionError(RuntimeError):
    """Raised when an AI/model execution step fails."""


class CrossServiceErrorBoundary:
    """Contain downstream AI failures and return a standard error payload."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        internal_token: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("AI_SERVICE_BASE_URL", "")).rstrip("/")
        self.internal_token = (
            internal_token
            if internal_token is not None
            else os.getenv("AI_SERVICE_INTERNAL_TOKEN", "")
        )
        timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else float(os.getenv("AI_SERVICE_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
        )

        if not self.base_url:
            raise ValueError("AI_SERVICE_BASE_URL is not configured.")
        if not self.internal_token:
            raise ValueError("AI_SERVICE_INTERNAL_TOKEN is not configured.")
        if timeout <= 0:
            raise ValueError("AI service timeout must be greater than zero.")

        self.timeout = httpx.Timeout(timeout)

    @staticmethod
    def _error(
        code: str,
        message: str,
        request_id: str | None,
    ) -> BoundaryResult:
        return BoundaryResult(
            success=False,
            error={
                "error_code": code,
                "message": message,
                "request_id": request_id,
            },
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Internal-Token": self.internal_token,
        }

    @staticmethod
    def _validate_payload(payload: Any) -> tuple[dict[str, Any] | None, str | None]:
        if payload is None or payload == {}:
            return None, "EMPTY_PAYLOAD"
        if not isinstance(payload, Mapping):
            return None, "INVALID_INPUT_TYPE"
        return dict(payload), None

    async def post_json(
        self,
        *,
        endpoint: str,
        payload: Any,
        request_id: str | None = None,
        fallback_message: str = "AI service is temporarily unavailable.",
    ) -> BoundaryResult:
        body, validation_error = self._validate_payload(payload)

        if validation_error == "EMPTY_PAYLOAD":
            return self._error(
                "EMPTY_PAYLOAD",
                "Request payload cannot be empty.",
                request_id,
            )
        if validation_error == "INVALID_INPUT_TYPE":
            return self._error(
                "INVALID_INPUT_TYPE",
                "Request payload must be a JSON object.",
                request_id,
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=body,
                    headers=self._headers(),
                )
        except httpx.TimeoutException:
            return self._error("AI_TIMEOUT", fallback_message, request_id)
        except httpx.RequestError:
            return self._error("AI_SERVICE_UNAVAILABLE", fallback_message, request_id)

        if response.status_code in {401, 403}:
            return self._error(
                "AUTHENTICATION_ERROR",
                "AI service authentication failed.",
                request_id,
            )

        if response.status_code == 429:
            return self._error(
                "AI_RATE_LIMITED",
                "AI service rate limit exceeded. Please try again later.",
                request_id,
            )

        if response.status_code == 422:
            return self._error(
                "VALIDATION_ERROR",
                "AI service rejected the request.",
                request_id,
            )

        if response.status_code >= 500:
            return self._error("AI_SERVICE_ERROR", fallback_message, request_id)

        if response.status_code >= 400:
            return self._error("AI_REQUEST_ERROR", fallback_message, request_id)

        try:
            data = response.json()
        except ValueError:
            return self._error(
                "INVALID_AI_RESPONSE",
                "AI service returned invalid JSON.",
                request_id,
            )

        if not isinstance(data, dict):
            return self._error(
                "INVALID_AI_RESPONSE",
                "AI service returned an unexpected response.",
                request_id,
            )

        return BoundaryResult(success=True, data=data)

    async def execute_model(
        self,
        operation: Callable[[], Awaitable[Mapping[str, Any]]],
        *,
        request_id: str | None = None,
    ) -> BoundaryResult:
        """Run a model operation and contain execution failures."""
        try:
            result = await operation()
        except ModelExecutionError:
            return self._error(
                "AI_MODEL_EXECUTION_ERROR",
                "AI model execution failed.",
                request_id,
            )
        except Exception:
            return self._error(
                "INTERNAL_ERROR",
                "Unexpected error during AI model execution.",
                request_id,
            )

        if not isinstance(result, Mapping):
            return self._error(
                "INVALID_AI_RESPONSE",
                "AI model returned an unexpected response.",
                request_id,
            )

        return BoundaryResult(success=True, data=dict(result))

    async def chatbot(
        self,
        *,
        user_id: str,
        message: str,
        conversation_id: str,
        history: list[dict[str, Any]] | None = None,
        request_id: str | None = None,
    ) -> BoundaryResult:
        if not isinstance(user_id, str):
            return self._error("INVALID_INPUT_TYPE", "user_id must be a string.", request_id)
        if not isinstance(message, str):
            return self._error("INVALID_INPUT_TYPE", "message must be a string.", request_id)
        if not message.strip():
            return self._error("EMPTY_PAYLOAD", "Chat message cannot be empty.", request_id)
        if not isinstance(conversation_id, str):
            return self._error(
                "INVALID_INPUT_TYPE",
                "conversation_id must be a string.",
                request_id,
            )
        if history is not None and not isinstance(history, list):
            return self._error("INVALID_INPUT_TYPE", "history must be a list.", request_id)

        return await self.post_json(
            endpoint=CHATBOT_ENDPOINT,
            payload={
                "user_id": user_id,
                "message": message,
                "conversation_id": conversation_id,
                "history": history or [],
            },
            request_id=request_id,
            fallback_message="AI assistant is temporarily unavailable.",
        )

    async def categorize_expense(
        self,
        *,
        description: str,
        amount: float,
        expense_id: str | None = None,
        merchant: str | None = None,
        currency: str = "PKR",
        request_id: str | None = None,
    ) -> BoundaryResult:
        if not isinstance(description, str):
            return self._error(
                "INVALID_INPUT_TYPE",
                "description must be a string.",
                request_id,
            )
        if not description.strip():
            return self._error(
                "EMPTY_PAYLOAD",
                "Expense description cannot be empty.",
                request_id,
            )
        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            return self._error(
                "INVALID_INPUT_TYPE",
                "amount must be a number.",
                request_id,
            )

        return await self.post_json(
            endpoint=CATEGORIZE_ENDPOINT,
            payload={
                "expense_id": expense_id,
                "description": description,
                "amount": amount,
                "merchant": merchant,
                "currency": currency,
            },
            request_id=request_id,
            fallback_message="Expense categorization is temporarily unavailable.",
        )
