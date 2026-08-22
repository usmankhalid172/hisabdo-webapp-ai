from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .client import (
    AIServiceError,
    AIServiceClient,
)
from .schemas import (
    AIChatRequest,
    AIChatResponse,
    AIErrorResponse,
)
from .service import AIIntegrationService


router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Integration"],
)


def get_ai_service() -> AIIntegrationService:
    """
    Create the AI integration service.

    This can later be replaced by the project's
    dependency-injection/container mechanism.
    """

    client = AIServiceClient()
    return AIIntegrationService(client)


@router.post(
    "/chat",
    response_model=AIChatResponse,
    responses={
        400: {"model": AIErrorResponse},
        401: {"model": AIErrorResponse},
        403: {"model": AIErrorResponse},
        404: {"model": AIErrorResponse},
        429: {"model": AIErrorResponse},
        502: {"model": AIErrorResponse},
        503: {"model": AIErrorResponse},
        504: {"model": AIErrorResponse},
    },
)
async def chat(request: AIChatRequest):
    """
    Application-facing AI chat endpoint.
    """

    service = get_ai_service()

    try:
        return await service.chat(request)

    except AIServiceError as exc:

        status_code = exc.status_code or 500

        error_response = AIErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
        )

        return JSONResponse(
            status_code=status_code,
            content=error_response.dict()
            if hasattr(error_response, "dict")
            else error_response.model_dump(),
        )