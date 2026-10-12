
from fastapi import APIRouter, Depends, Header

from ..errors import ServiceError
from ..schemas import ChatbotRequest, ChatbotResponse
from ..security import require_internal_token
from .service import handle_chat, _is_own_financial_data_query

router = APIRouter(
    prefix="/api/v1",
    tags=["chatbot"],
    dependencies=[Depends(require_internal_token)],
)


@router.post(
    "/chatbot",
    response_model=ChatbotResponse,
    summary="Chatbot reply for a user message",
)
def chatbot(
    payload: ChatbotRequest,
    authenticated_user_id: str | None = Header(
        default=None,
        alias="X-Authenticated-User-Id",
    ),
) -> ChatbotResponse:
    if _is_own_financial_data_query(payload.message):
        if not authenticated_user_id:
            raise ServiceError(
                "UNAUTHENTICATED_USER",
                "Authenticated user identity is required for financial data.",
                status_code=401,
            )

        if payload.user_id != authenticated_user_id:
            raise ServiceError(
                "FORBIDDEN",
                "You cannot access another user's financial data.",
                status_code=403,
            )

    return handle_chat(payload)