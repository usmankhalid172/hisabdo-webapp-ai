from typing import Any, Dict

from .client import AIServiceClient, AIServiceError
from .schemas import AIChatRequest, AIChatResponse


class AIIntegrationService:
    """
    Application-facing orchestration layer for AI services.

    Responsibilities:
    - prepare the downstream request
    - call the AI service client
    - validate the downstream response
    - normalize the result into the application contract
    """

    def __init__(self, client: AIServiceClient) -> None:
        self.client = client

    @staticmethod
    def _request_to_dict(request: AIChatRequest) -> Dict[str, Any]:
        """
        Convert a Pydantic model to a dictionary.

        Supports both Pydantic v1 and v2 style APIs.
        """
        if hasattr(request, "model_dump"):
            return request.model_dump()

        return request.dict()

    async def chat(
        self,
        request: AIChatRequest,
    ) -> AIChatResponse:

        payload = self._request_to_dict(request)

        try:
            raw_response = await self.client.chat(payload)

        except AIServiceError:
            # Let the API layer map the integration error.
            raise

        # Validate and normalize the AI service response.
        try:
            if hasattr(AIChatResponse, "model_validate"):
                return AIChatResponse.model_validate(raw_response)

            return AIChatResponse.parse_obj(raw_response)

        except Exception as exc:
            raise AIServiceError(
                message="AI response does not match the expected schema.",
                error_code="INVALID_AI_RESPONSE",
                status_code=502,
            ) from exc