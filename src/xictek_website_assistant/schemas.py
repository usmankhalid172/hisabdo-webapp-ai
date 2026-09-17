"""
Request/response contracts for the XICTEK website assistant.

Deliberately its own shape, not reusing `src.schemas.ChatbotRequest` —
this bot has no `user_id` / authenticated-account concept (any website
visitor can use it) and no financial-data routing, so the HisabDo
chatbot's fields don't apply here.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class XictekChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str
    history: list[HistoryTurn] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "What services does XICTEK offer?",
                "conversation_id": "demo-1",
                "history": [],
            }
        }
    }


class SourceRef(BaseModel):
    """A knowledge-base chunk the answer was grounded in, surfaced so the
    widget can show 'source: xicteksystems.com/services' style attribution
    and so answers stay auditable during the demo/QA phase."""

    title: str
    url: Optional[str] = None
    score: float


class XictekChatResponse(BaseModel):
    reply: str
    conversation_id: str
    sources: list[SourceRef] = Field(default_factory=list)
    intent: str  # "answered" | "declined_prompt_injection" | "declined_out_of_scope" | "general"
    tokens_used: Optional[int] = None


class IndexStatsResponse(BaseModel):
    """Surfaced at GET /api/v1/xictek/index-status so the team lead can
    verify the knowledge base was actually built before demoing, instead
    of finding out mid-Swagger-demo that ingest.py was never run."""

    chunk_count: int
    embedding_model: str
    index_built: bool
