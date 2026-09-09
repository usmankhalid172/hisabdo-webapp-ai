from unittest.mock import AsyncMock

import pytest

from src.integration.client import (
    AIServiceError,
)
from src.integration.schemas import (
    AIChatRequest,
    AIChatResponse,
)
from src.integration.service import (
    AIIntegrationService,
)


@pytest.mark.asyncio
async def test_valid_chat_request_is_processed():
    mock_client = AsyncMock()

    mock_client.chat.return_value = {
        "status": "success",
        "response": "Your food spending is 5000 PKR.",
        "request_id": "req-001",
    }

    service = AIIntegrationService(mock_client)

    request = AIChatRequest(
        message="How much did I spend on food?",
        conversation_id="conv-001",
        user_id="user-001",
    )

    response = await service.chat(request)

    assert isinstance(response, AIChatResponse)
    assert response.status == "success"
    assert response.response == "Your food spending is 5000 PKR."

    mock_client.chat.assert_awaited_once()


@pytest.mark.asyncio
async def test_empty_message_is_rejected():
    with pytest.raises(ValueError):
        AIChatRequest(message="")


@pytest.mark.asyncio
async def test_invalid_ai_response_is_rejected():
    mock_client = AsyncMock()

    mock_client.chat.return_value = {
        "invalid_field": "invalid"
    }

    service = AIIntegrationService(mock_client)

    request = AIChatRequest(
        message="Test request"
    )

    with pytest.raises(AIServiceError) as exc_info:
        await service.chat(request)

    assert exc_info.value.error_code == "INVALID_AI_RESPONSE"


@pytest.mark.asyncio
async def test_ai_service_error_is_propagated():
    mock_client = AsyncMock()

    mock_client.chat.side_effect = AIServiceError(
        message="Service unavailable",
        error_code="AI_SERVICE_UNAVAILABLE",
        status_code=503,
    )

    service = AIIntegrationService(mock_client)

    request = AIChatRequest(
        message="Test request"
    )

    with pytest.raises(AIServiceError) as exc_info:
        await service.chat(request)

    assert exc_info.value.status_code == 503
    assert exc_info.value.error_code == "AI_SERVICE_UNAVAILABLE"