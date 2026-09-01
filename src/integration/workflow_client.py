"""
End-to-end workflow client for Task 23-24.

Responsibility:
    Validate application workflow payloads and transmit data to the
    existing HisabDo AI service.

This module does not implement AI/ML logic. It only handles the
application-to-AI transport boundary and predictable fallback errors.

Supported downstream capabilities:
    POST /api/v1/chatbot
    POST /api/v1/categorize
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

import httpx


CHATBOT_ENDPOINT = "/api/v1/chatbot"
CATEGORIZE_ENDPOINT = "/api/v1/categorize"
DEFAULT_TIMEOUT_SECONDS = 15.0


@dataclass(slots=True)
class WorkflowError(Exception):
    """Base error returned by the workflow integration boundary."""

    message: str
    error_code: str
    status_code: int | None = None

    def __str__(self) -> str:
        return self.message


class EmptyPayloadError(WorkflowError):
    """Raised when an empty request payload is supplied."""

    def __init__(self) -> None:
        super().__init__(
            message="Request payload cannot be empty.",
            error_code="EMPTY_PAYLOAD",
            status_code=400,
        )


class InvalidInputTypeError(WorkflowError):
    """Raised when the workflow receives an unexpected input type."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="INVALID_INPUT_TYPE",
            status_code=400,
        )


class WorkflowTimeoutError(WorkflowError):
    """Raised when the downstream AI service times out."""

    def __init__(self) -> None:
        super().__init__(
            message="AI service request timed out.",
            error_code="AI_TIMEOUT",
            status_code=504,
        )


class WorkflowUnavailableError(WorkflowError):
    """Raised when the downstream AI service cannot be reached."""

    def __init__(self) -> None:
        super().__init__(
            message="AI service is unavailable.",
            error_code="AI_SERVICE_UNAVAILABLE",
            status_code=503,
        )


class WorkflowServiceError(WorkflowError):
    """Raised when the downstream AI service rejects the request."""

    pass


class WorkflowResponseError(WorkflowError):
    """Raised when a successful response is not valid JSON/object data."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            error_code="INVALID_AI_RESPONSE",
            status_code=502,
        )


class AIWorkflowClient:
    """
    Application-side workflow client.

    The client validates the workflow input before transmission and converts
    common transport/service failures into predictable WorkflowError types.

    Configuration:
        AI_SERVICE_BASE_URL
        AI_SERVICE_INTERNAL_TOKEN
        AI_SERVICE_TIMEOUT_SECONDS
    """

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
            raise WorkflowServiceError(
                message="AI_SERVICE_BASE_URL is not configured.",
                error_code="CONFIGURATION_ERROR",
            )

        if not self.internal_token:
            raise WorkflowServiceError(
                message="AI_SERVICE_INTERNAL_TOKEN is not configured.",
                error_code="CONFIGURATION_ERROR",
            )

        if configured_timeout <= 0:
            raise WorkflowServiceError(
                message="AI service timeout must be greater than zero.",
                error_code="CONFIGURATION_ERROR",
            )

        self.timeout = httpx.Timeout(configured_timeout)

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Internal-Token": self.internal_token,
        }

    @staticmethod
    def _validate_payload(payload: Any) -> dict[str, Any]:
        if payload is None:
            raise EmptyPayloadError()

        if not isinstance(payload, Mapping):
            raise InvalidInputTypeError(
                "Request payload must be a JSON object."
            )

        if not payload:
            raise EmptyPayloadError()

        return dict(payload)

    async def _post(
        self,
        endpoint: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        body = self._validate_payload(payload)
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=body,
                    headers=self._headers(),
                )
        except httpx.TimeoutException as exc:
            raise WorkflowTimeoutError() from exc
        except httpx.RequestError as exc:
            raise WorkflowUnavailableError() from exc

        if response.status_code in {401, 403}:
            raise WorkflowServiceError(
                message="AI service authentication failed.",
                error_code="AUTHENTICATION_ERROR",
                status_code=response.status_code,
            )

        if response.status_code == 404:
            raise WorkflowServiceError(
                message="AI service endpoint was not found.",
                error_code="ENDPOINT_NOT_FOUND",
                status_code=404,
            )

        if response.status_code == 422:
            raise WorkflowServiceError(
                message="AI service rejected the request validation.",
                error_code="VALIDATION_ERROR",
                status_code=422,
            )

        if response.status_code == 429:
            raise WorkflowServiceError(
                message="AI service rate limit exceeded.",
                error_code="RATE_LIMITED",
                status_code=429,
            )

        if response.status_code >= 500:
            raise WorkflowUnavailableError()

        if response.status_code >= 400:
            raise WorkflowServiceError(
                message="AI service rejected the request.",
                error_code="AI_REQUEST_ERROR",
                status_code=response.status_code,
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise WorkflowResponseError(
                "AI service returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise WorkflowResponseError(
                "AI service returned an unexpected response structure."
            )

        return data

    async def chatbot(
        self,
        *,
        user_id: str,
        message: str,
        conversation_id: str,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Transmit a chatbot workflow request and return its response."""
        if not isinstance(user_id, str):
            raise InvalidInputTypeError("user_id must be a string.")

        if not isinstance(message, str):
            raise InvalidInputTypeError("message must be a string.")

        if not isinstance(conversation_id, str):
            raise InvalidInputTypeError(
                "conversation_id must be a string."
            )

        if not message.strip():
            raise EmptyPayloadError()

        if history is not None and not isinstance(history, list):
            raise InvalidInputTypeError("history must be a list.")

        payload = {
            "user_id": user_id,
            "message": message,
            "conversation_id": conversation_id,
            "history": history or [],
        }

        return await self._post(CHATBOT_ENDPOINT, payload)

    async def categorize_expense(
        self,
        *,
        description: str,
        amount: float,
        expense_id: str | None = None,
        merchant: str | None = None,
        currency: str = "PKR",
    ) -> dict[str, Any]:
        """Transmit an expense-categorization workflow request."""
        if not isinstance(description, str):
            raise InvalidInputTypeError(
                "description must be a string."
            )

        if not description.strip():
            raise EmptyPayloadError()

        if not isinstance(amount, (int, float)) or isinstance(amount, bool):
            raise InvalidInputTypeError(
                "amount must be a number."
            )

        if expense_id is not None and not isinstance(expense_id, str):
            raise InvalidInputTypeError(
                "expense_id must be a string or null."
            )

        if merchant is not None and not isinstance(merchant, str):
            raise InvalidInputTypeError(
                "merchant must be a string or null."
            )

        if not isinstance(currency, str):
            raise InvalidInputTypeError(
                "currency must be a string."
            )

        payload = {
            "expense_id": expense_id,
            "description": description,
            "amount": amount,
            "merchant": merchant,
            "currency": currency,
        }

        return await self._post(CATEGORIZE_ENDPOINT, payload)
