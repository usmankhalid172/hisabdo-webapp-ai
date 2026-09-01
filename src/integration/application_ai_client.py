"""
Application-side client for consuming the HisabDo AI service.

This module belongs to the Capstone/application integration boundary.
It deliberately does not implement AI logic. It only:

- builds requests for the ready AI endpoints
- adds service-to-service authentication
- handles HTTP/network failures
- validates downstream responses
- converts AI-service responses into application-facing models

Environment variables:
    AI_SERVICE_BASE_URL
    AI_SERVICE_INTERNAL_TOKEN
    AI_SERVICE_TIMEOUT_SECONDS
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping

import httpx
from pydantic import BaseModel, Field, ValidationError


CHATBOT_PATH = "/api/v1/chatbot"
CATEGORIZE_PATH = "/api/v1/categorize"

DEFAULT_TIMEOUT_SECONDS = 15.0


# ---------------------------------------------------------------------------
# Application-facing response models
# ---------------------------------------------------------------------------


class ChatResult(BaseModel):
    """Normalized Financial Assistant result returned to the application."""

    reply: str
    conversation_id: str
    intent: str | None = None
    tokens_used: int | None = None
    source: str | None = None


class ExpenseCategoryResult(BaseModel):
    """Normalized expense-categorization result returned to the application."""

    category: str
    confidence: float
    alternative_categories: list[str] = Field(default_factory=list)
    needs_confirmation: bool
    method: str


@dataclass(slots=True)
class AIServiceError(Exception):
    """Base exception for application-to-AI service failures."""

    message: str
    status_code: int | None = None
    error_code: str = "AI_SERVICE_ERROR"

    def __str__(self) -> str:
        return self.message


class AIServiceConfigurationError(AIServiceError):
    """Raised when required client configuration is missing."""

    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=None,
            error_code="AI_SERVICE_CONFIGURATION_ERROR",
        )


class AIServiceTimeoutError(AIServiceError):
    """Raised when the downstream AI service exceeds the timeout."""

    def __init__(self, message: str = "AI service request timed out.") -> None:
        super().__init__(
            message=message,
            status_code=504,
            error_code="AI_TIMEOUT",
        )


class AIServiceUnavailableError(AIServiceError):
    """Raised when the downstream AI service cannot be reached."""

    def __init__(
        self,
        message: str = "AI service is currently unavailable.",
    ) -> None:
        super().__init__(
            message=message,
            status_code=503,
            error_code="AI_SERVICE_UNAVAILABLE",
        )


class AIServiceResponseError(AIServiceError):
    """Raised when the downstream AI response is invalid or unexpected."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = 502,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status_code,
            error_code="INVALID_AI_RESPONSE",
        )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class ApplicationAIClient:
    """
    Client used by the Capstone backend/application integration layer.

    The client talks only to the existing AI-service API. It does not contain
    model, RAG, prompt, or categorization logic.

    Example:
        client = ApplicationAIClient()
        result = await client.chatbot(
            user_id="user-001",
            message="How much did I spend this month?",
            conversation_id="conv-001",
        )
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

        timeout_value = (
            timeout_seconds
            if timeout_seconds is not None
            else float(
                os.getenv(
                    "AI_SERVICE_TIMEOUT_SECONDS",
                    str(DEFAULT_TIMEOUT_SECONDS),
                )
            )
        )

        if timeout_value <= 0:
            raise AIServiceConfigurationError(
                "AI_SERVICE_TIMEOUT_SECONDS must be greater than zero."
            )

        self.timeout = httpx.Timeout(timeout_value)

        if not self.base_url:
            raise AIServiceConfigurationError(
                "AI_SERVICE_BASE_URL is not configured."
            )

        if not self.internal_token:
            raise AIServiceConfigurationError(
                "AI_SERVICE_INTERNAL_TOKEN is not configured."
            )

    def _headers(self) -> dict[str, str]:
        """Build headers for authenticated service-to-service requests."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Internal-Token": self.internal_token,
        }

    async def _post(
        self,
        path: str,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        """POST JSON to the AI service and normalize transport errors."""
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=dict(payload),
                    headers=self._headers(),
                )
        except httpx.TimeoutException as exc:
            raise AIServiceTimeoutError() from exc
        except httpx.RequestError as exc:
            raise AIServiceUnavailableError(
                "Unable to connect to the AI service."
            ) from exc

        if response.status_code in {401, 403}:
            raise AIServiceError(
                message="AI service authentication failed.",
                status_code=response.status_code,
                error_code="AI_AUTHENTICATION_ERROR",
            )

        if response.status_code == 404:
            raise AIServiceError(
                message="AI service endpoint was not found.",
                status_code=404,
                error_code="AI_ENDPOINT_NOT_FOUND",
            )

        if response.status_code == 429:
            raise AIServiceError(
                message="AI service rate limit exceeded.",
                status_code=429,
                error_code="RATE_LIMITED",
            )

        if response.status_code == 422:
            raise AIServiceError(
                message="AI service rejected the request validation.",
                status_code=422,
                error_code="AI_VALIDATION_ERROR",
            )

        if response.status_code >= 500:
            raise AIServiceUnavailableError(
                "AI service returned a server-side error."
            )

        if response.status_code >= 400:
            raise AIServiceError(
                message="AI service rejected the request.",
                status_code=response.status_code,
                error_code="AI_REQUEST_ERROR",
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise AIServiceResponseError(
                "AI service returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise AIServiceResponseError(
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
    ) -> ChatResult:
        """
        Send a Financial Assistant request to the ready AI service.

        The AI-service contract requires user_id, message, and
        conversation_id. History is optional and defaults to an empty list.
        """
        payload = {
            "user_id": user_id,
            "message": message,
            "conversation_id": conversation_id,
            "history": history or [],
        }

        data = await self._post(CHATBOT_PATH, payload)

        try:
            return ChatResult.model_validate(data)
        except ValidationError as exc:
            raise AIServiceResponseError(
                "AI chatbot response does not match the expected contract."
            ) from exc

    async def categorize_expense(
        self,
        *,
        description: str,
        amount: float,
        expense_id: str | None = None,
        merchant: str | None = None,
        currency: str = "PKR",
    ) -> ExpenseCategoryResult:
        """
        Send an expense-categorization request to the ready AI service.

        The method does not perform categorization locally; it only consumes
        the existing AI service output.
        """
        payload = {
            "expense_id": expense_id,
            "description": description,
            "amount": amount,
            "merchant": merchant,
            "currency": currency,
        }

        data = await self._post(CATEGORIZE_PATH, payload)

        try:
            return ExpenseCategoryResult.model_validate(data)
        except ValidationError as exc:
            raise AIServiceResponseError(
                "AI categorization response does not match "
                "the expected contract."
            ) from exc
