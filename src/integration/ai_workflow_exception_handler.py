"""
Task 26: Fault-tolerant application-to-AI workflow.

Responsibility:
    Provide a small application-side boundary around the existing HisabDo AI
    routes with explicit exception handling and safe fallback behavior.

Handled cases:
    - empty user payloads
    - unexpected input types
    - API timeouts
    - HTTP 429 rate limits / quota exhaustion
    - authentication errors
    - model/inference execution failures
    - downstream service failures
    - malformed AI responses

This module does not implement or modify AI/ML logic.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

import httpx


CHATBOT_ENDPOINT = "/api/v1/chatbot"
CATEGORIZE_ENDPOINT = "/api/v1/categorize"
DEFAULT_TIMEOUT_SECONDS = 15.0

CHATBOT_FALLBACK = (
    "The AI assistant is temporarily unavailable. Please try again later."
)
CATEGORIZATION_FALLBACK = (
    "We could not categorize this expense automatically. "
    "Please select a category manually."
)


@dataclass(slots=True)
class WorkflowResult:
    """Stable application-facing result."""

    status: str
    data: dict[str, Any] | None = None
    error_code: str | None = None
    message: str | None = None

    @property
    def is_success(self) -> bool:
        """Return whether the workflow completed successfully."""
        return self.status == "success"


class Task26WorkflowClient:
    """Fault-tolerant client for the existing AI service endpoints."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        internal_token: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("AI_SERVICE_BASE_URL", "")
        ).rstrip("/")

        self.internal_token = (
            internal_token
            if internal_token is not None
            else os.getenv("AI_SERVICE_INTERNAL_TOKEN", "")
        )

        configured_timeout = (
            timeout_seconds
            if timeout_seconds is not None
            else float(
                os.getenv(
                    "AI_SERVICE_TIMEOUT_SECONDS",
                    str(DEFAULT_TIMEOUT_SECONDS),
                )
            )
        )

        if not self.base_url:
            raise ValueError("AI_SERVICE_BASE_URL is not configured.")

        if not self.internal_token:
            raise ValueError("AI_SERVICE_INTERNAL_TOKEN is not configured.")

        if configured_timeout <= 0:
            raise ValueError("AI service timeout must be greater than zero.")

        self.timeout = httpx.Timeout(configured_timeout)

    def _headers(self) -> dict[str, str]:
        """Build the service-to-service authentication headers."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Internal-Token": self.internal_token,
        }

    @staticmethod
    def _fallback(
        *,
        error_code: str,
        message: str,
        status_code: int | None = None,
    ) -> WorkflowResult:
        """Build a safe, stable fallback response."""
        data = {"http_status": status_code} if status_code is not None else None
        return WorkflowResult(
            status="fallback",
            data=data,
            error_code=error_code,
            message=message,
        )

    @staticmethod
    def _validate_payload(
        payload: Any,
    ) -> tuple[dict[str, Any] | None, WorkflowResult | None]:
        """Validate object-shaped JSON payloads before network access."""
        if payload is None or payload == {}:
            return None, Task26WorkflowClient._fallback(
                error_code="EMPTY_PAYLOAD",
                message="Request payload cannot be empty.",
                status_code=400,
            )

        if not isinstance(payload, Mapping):
            return None, Task26WorkflowClient._fallback(
                error_code="INVALID_INPUT_TYPE",
                message="Request payload must be a JSON object.",
                status_code=400,
            )

        return dict(payload), None

    async def _post(
        self,
        endpoint: str,
        payload: Mapping[str, Any],
        *,
        fallback_message: str,
    ) -> WorkflowResult:
        """Execute the downstream request and translate expected failures."""
        body, validation_result = self._validate_payload(payload)
        if validation_result is not None:
            return validation_result

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=body,
                    headers=self._headers(),
                )
        except httpx.TimeoutException:
            return self._fallback(
                error_code="AI_TIMEOUT",
                message=fallback_message,
                status_code=504,
            )
        except httpx.RequestError:
            return self._fallback(
                error_code="AI_SERVICE_UNAVAILABLE",
                message=fallback_message,
                status_code=503,
            )

        if response.status_code in {401, 403}:
            return self._fallback(
                error_code="AUTHENTICATION_ERROR",
                message="AI service authentication failed.",
                status_code=response.status_code,
            )

        if response.status_code == 429:
            return self._fallback(
                error_code="AI_RATE_LIMITED",
                message=(
                    "The AI service is temporarily rate limited. "
                    "Please try again later."
                ),
                status_code=429,
            )

        if response.status_code == 422:
            return self._fallback(
                error_code="AI_VALIDATION_ERROR",
                message="The AI service rejected the request.",
                status_code=422,
            )

        if response.status_code >= 500:
            return self._fallback(
                error_code="AI_SERVICE_UNAVAILABLE",
                message=fallback_message,
                status_code=response.status_code,
            )

        if response.status_code >= 400:
            return self._fallback(
                error_code="AI_REQUEST_ERROR",
                message=fallback_message,
                status_code=response.status_code,
            )

        try:
            data = response.json()
        except ValueError:
            return self._fallback(
                error_code="INVALID_AI_RESPONSE",
                message=fallback_message,
                status_code=502,
            )

        if not isinstance(data, dict):
            return self._fallback(
                error_code="INVALID_AI_RESPONSE",
                message=fallback_message,
                status_code=502,
            )

        return WorkflowResult(status="success", data=data)

    async def chatbot(
        self,
        *,
        user_id: str,
        message: str,
        conversation_id: str,
        history: list[dict[str, Any]] | None = None,
    ) -> WorkflowResult:
        """Send a chatbot request through the fault-tolerant boundary."""
        if not isinstance(user_id, str):
            return self._fallback(
                error_code="INVALID_INPUT_TYPE",
                message=CHATBOT_FALLBACK,
                status_code=400,
            )

        if not isinstance(message, str):
            return self._fallback(
                error_code="INVALID_INPUT_TYPE",
                message=CHATBOT_FALLBACK,
                status_code=400,
            )

        if not isinstance(conversation_id, str):
            return self._fallback(
                error_code="INVALID_INPUT_TYPE",
                message=CHATBOT_FALLBACK,
                status_code=400,
            )

        if not message.strip():
            return self._fallback(
                error_code="EMPTY_PAYLOAD",
                message="Chat message cannot be empty.",
                status_code=400,
            )

        if history is not None and not isinstance(history, list):
            return self._fallback(
                error_code="INVALID_INPUT_TYPE",
                message=CHATBOT_FALLBACK,
                status_code=400,
            )

        return await self._post(
            CHATBOT_ENDPOINT,
            {
                "user_id": user_id,
                "message": message,
                "conversation_id": conversation_id,
                "history": history or [],
            },
            fallback_message=CHATBOT_FALLBACK,
        )

    async def categorize_expense(
        self,
        *,
        description: str,
        amount: float,
        expense_id: str | None = None,
        merchant: str | None = None,
        currency: str = "PKR",
    ) -> WorkflowResult:
        """Send an expense categorization request safely."""
        if not isinstance(description, str):
            return self._fallback(
                error_code="INVALID_INPUT_TYPE",
                message=CATEGORIZATION_FALLBACK,
                status_code=400,
            )

        if not description.strip():
            return self._fallback(
                error_code="EMPTY_PAYLOAD",
                message="Expense description cannot be empty.",
                status_code=400,
            )

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            return self._fallback(
                error_code="INVALID_INPUT_TYPE",
                message=CATEGORIZATION_FALLBACK,
                status_code=400,
            )

        if expense_id is not None and not isinstance(expense_id, str):
            return self._fallback(
                error_code="INVALID_INPUT_TYPE",
                message=CATEGORIZATION_FALLBACK,
                status_code=400,
            )

        if merchant is not None and not isinstance(merchant, str):
            return self._fallback(
                error_code="INVALID_INPUT_TYPE",
                message=CATEGORIZATION_FALLBACK,
                status_code=400,
            )

        if not isinstance(currency, str):
            return self._fallback(
                error_code="INVALID_INPUT_TYPE",
                message=CATEGORIZATION_FALLBACK,
                status_code=400,
            )

        return await self._post(
            CATEGORIZE_ENDPOINT,
            {
                "expense_id": expense_id,
                "description": description,
                "amount": amount,
                "merchant": merchant,
                "currency": currency,
            },
            fallback_message=CATEGORIZATION_FALLBACK,
        )
