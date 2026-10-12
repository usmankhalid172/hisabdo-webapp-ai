
from fastapi import APIRouter, Depends

from ..schemas import ChatbotRequest, ChatbotResponse
from ..security import require_internal_token, require_authenticated_user
from ..errors import ServiceError
from .service import handle_chat

router = APIRouter(
    prefix="/api/v1",
    tags=["chatbot"],
    dependencies=[Depends(require_internal_token)],
)


@router.post(
    "/chatbot",
    response_model=ChatbotResponse,
    summary="Chatbot reply for an authenticated user",
)
def chatbot(
    payload: ChatbotRequest,
    authenticated_user_id: str = Depends(require_authenticated_user),
) -> ChatbotResponse:
    if payload.user_id != authenticated_user_id:
        raise ServiceError(
            "FORBIDDEN_ACCOUNT_ACCESS",
            "You cannot access another user's financial data",
            status_code=403,
        )

    return handle_chat(payload)
