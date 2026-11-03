from fastapi import APIRouter, Depends, Request

from ..schemas import ChatbotRequest, ChatbotResponse
from ..security import require_internal_token
from . import telemetry
from .service import handle_chat, kb_status

router = APIRouter(
    prefix="/api/v1",
    tags=["chatbot"],
    dependencies=[Depends(require_internal_token)],
)


@router.post("/chatbot", response_model=ChatbotResponse, summary="Chatbot reply for a user message")
def chatbot(payload: ChatbotRequest, request: Request) -> ChatbotResponse:
    token = telemetry.REQUEST_ID.set(getattr(request.state, "request_id", None))
    try:
        return handle_chat(payload)
    finally:
        telemetry.REQUEST_ID.reset(token)


@router.get("/metrics", summary="Chatbot counters, latency percentiles and KB index status (internal)")
def metrics() -> dict:
    return {**telemetry.METRICS.snapshot(), "kb": kb_status()}
