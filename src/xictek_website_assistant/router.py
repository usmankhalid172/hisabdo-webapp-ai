from fastapi import APIRouter, Depends, Request

from ..security import require_internal_token
from .rate_limit import limiter, rate_limit_string
from .schemas import IndexStatsResponse, XictekChatRequest, XictekChatResponse
from .service import get_index_stats, handle_chat

router = APIRouter(
    prefix="/api/v1/xictek",
    tags=["xictek-website-assistant"],
    dependencies=[Depends(require_internal_token)],
)


@router.post("/chat", response_model=XictekChatResponse, summary="Chat reply for a website visitor message")
@limiter.limit(rate_limit_string)
def chat(request: Request, payload: XictekChatRequest) -> XictekChatResponse:
    return handle_chat(payload)


@router.get("/index-status", response_model=IndexStatsResponse, summary="Knowledge-base index status")
def index_status() -> IndexStatsResponse:
    return get_index_stats()
