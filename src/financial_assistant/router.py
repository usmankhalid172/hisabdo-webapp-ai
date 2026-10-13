from fastapi import APIRouter, Depends, Header

from ..schemas import ChatbotRequest, ChatbotResponse
from ..security import require_customer_access, require_internal_token
from .service import _is_own_financial_data_query, handle_chat

router = APIRouter(
    prefix="/api/v1",
    tags=["chatbot"],
    dependencies=[Depends(require_internal_token)],
)


@router.post("/chatbot", response_model=ChatbotResponse, summary="Chatbot reply for a user message")
def chatbot(
    payload: ChatbotRequest,
    authenticated_user_id: str | None = Header(
        default=None, alias="X-Authenticated-User-ID"
    ),
) -> ChatbotResponse:
    # Financial requests require a trusted upstream customer identity.
    if _is_own_financial_data_query(payload.message):
        require_customer_access(payload.user_id, authenticated_user_id)
    return handle_chat(payload)
