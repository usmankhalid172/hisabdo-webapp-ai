from fastapi import APIRouter, Depends

from ..schemas import ChatbotRequest, ChatbotResponse
from ..security import require_internal_token
from .service import handle_chat

router = APIRouter(
    prefix="/api/v1",
    tags=["chatbot"],
    dependencies=[Depends(require_internal_token)],
)


@router.post("/chatbot", response_model=ChatbotResponse, summary="Chatbot reply for a user message")
def chatbot(payload: ChatbotRequest) -> ChatbotResponse:
    return handle_chat(payload)
