
"""
Request/response contracts. These are the source of truth mirrored by the
backend's API client, per Day 15 §8.
"""
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------- §4 infra endpoints ----------

class HealthResponse(BaseModel):
    status: str = "ok"


class VersionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    service: str
    version: str
    model_provider: str


# ---------- §6.1 Chatbot ----------

class HistoryTurn(BaseModel):
    """One prior conversation turn."""
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatbotRequest(BaseModel):
    user_id: str
    message: str = Field(min_length=1)
    conversation_id: str
    history: list[HistoryTurn] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "1",
                "message": "How do I categorize an expense?",
                "conversation_id": "1",
                "history": [],
            }
        }
    }


class ChatbotCitation(BaseModel):
    """A source retrieved from the verified knowledge base."""
    title: str
    source_url: Optional[str] = None
    section: Optional[str] = None


class ChatbotResponse(BaseModel):
    reply: str
    conversation_id: str
    intent: Optional[str] = None
    tokens_used: Optional[int] = None
    source: str
    citations: list[ChatbotCitation] = Field(default_factory=list)


# ---------- §6.2 Expense categorization ----------

class CategorizeRequest(BaseModel):
    expense_id: Optional[str] = None
    description: str = Field(min_length=1)
    amount: float
    merchant: Optional[str] = None
    currency: str = "PKR"


class CategorizeResponse(BaseModel):
    category: str
    confidence: float
    alternative_categories: list[str] = Field(default_factory=list)
    needs_confirmation: bool
    method: str


class BatchCategorizeRequest(BaseModel):
    items: list[CategorizeRequest]


class BatchCategorizeResponse(BaseModel):
    results: list[CategorizeResponse]
