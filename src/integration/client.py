import os
from typing import Any, Dict, Optional

import httpx


class AIServiceError(Exception):
    """
    Base exception for AI-service communication failures.
    """

    def __init__(
        self,
        message: str,
        error_code: str = "AI_SERVICE_ERROR",
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


class AIServiceTimeoutError(AIServiceError):
    """
    Raised when the AI service does not respond within the timeout.
    """

    def __init__(self, message: str = "AI service request timed out.") -> None:
        super().__init__(
            message=message,
            error_code="AI_TIMEOUT",
            status_code=504,
        )


class AIServiceUnavailableError(AIServiceError):
    """
    Raised when the AI service cannot be reached or is unavailable.
    """

    def __init__(
        self,
        message: str = "AI service is currently unavailable.",
    ) -> None:
        super().__init__(
            message=message,
            error_code="AI_SERVICE_UNAVAILABLE",
            status_code=503,
        )


class AIServiceClient:
    """
    Client responsible for communicating with the downstream AI service.

    Configuration is obtained from environment variables:

    AI_SERVICE_BASE_URL
    AI_SERVICE_CHAT_PATH
    AI_SERVICE_API_KEY   (optional)
    AI_SERVICE_TIMEOUT
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        chat_path: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("AI_SERVICE_BASE_URL", "")
        ).rstrip("/")

        self.chat_path = (
            chat_path or os.getenv(
                "AI_SERVICE_CHAT_PATH",
                "/api/v1/ai/chat",
            )
        )

        self.api_key = (
            api_key
            if api_key is not None
            else os.getenv("AI_SERVICE_API_KEY")
        )

        timeout_value = timeout or float(
            os.getenv("AI_SERVICE_TIMEOUT", "30")
        )

        self.timeout = httpx.Timeout(timeout_value)

    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    async def chat(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a chat request to the downstream AI service.
        """

        if not self.base_url:
            raise AIServiceUnavailableError(
                "AI_SERVICE_BASE_URL is not configured."
            )

        url = f"{self.base_url}{self.chat_path}"

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:

                response = await client.post(
                    url,
                    json=payload,
                    headers=self._build_headers(),
                )

        except httpx.TimeoutException as exc:
            raise AIServiceTimeoutError() from exc

        except httpx.RequestError as exc:
            raise AIServiceUnavailableError(
                "Unable to connect to the AI service."
            ) from exc

        if response.status_code == 429:
            raise AIServiceError(
                message="AI service rate limit exceeded.",
                error_code="RATE_LIMITED",
                status_code=429,
            )

        if response.status_code in (401, 403):
            raise AIServiceError(
                message="AI service authentication/authorization failed.",
                error_code="AI_AUTHENTICATION_ERROR",
                status_code=response.status_code,
            )

        if response.status_code == 404:
            raise AIServiceError(
                message="AI service endpoint was not found.",
                error_code="AI_ENDPOINT_NOT_FOUND",
                status_code=404,
            )

        if response.status_code >= 500:
            raise AIServiceUnavailableError(
                "AI service returned a server-side error."
            )

        if response.status_code >= 400:
            raise AIServiceError(
                message="AI service rejected the request.",
                error_code="AI_REQUEST_ERROR",
                status_code=response.status_code,
            )

        try:
            return response.json()

        except ValueError as exc:
            raise AIServiceError(
                message="AI service returned invalid JSON.",
                error_code="INVALID_AI_RESPONSE",
                status_code=502,
            ) from exc