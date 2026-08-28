"""
Request/response contracts. These are the source of truth mirrored by the
backend's API client, per Day 15 §8.
"""
from typing import Optional

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

class ChatHistoryEntry(BaseModel):
    """One prior turn supplied by the caller for context.

    ``role`` is one of ``user`` / ``assistant``; ``content`` is the turn text.
    Typed (instead of a bare ``dict``) so malformed history payloads are
    rejected by Pydantic rather than silently passed through (Task 27 payload
    formatting fix).
    """
    role: str = Field(..., pattern=r"^(user|assistant)$")
    content: str = Field(..., min_length=1)


class ChatbotRequest(BaseModel):
    user_id: str
    message: str = Field(min_length=1)
    conversation_id: str
    history: list[ChatHistoryEntry] = Field(default_factory=list)


class ChatbotResponse(BaseModel):
    reply: str
    conversation_id: str
    user_id: Optional[str] = None     # echoed back for session identity
    intent: Optional[str] = None
    tokens_used: Optional[int] = None
    model: Optional[str] = None       # provider/model that answered (demo visibility)
    matched_context: Optional[str] = None  # retrieved doc title when source=="rag"
    source: str  # "rag" | "backend_financial_api" | "llm_general" | "backend_unavailable" — POC transparency, not in Day 15 contract


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
    method: str  # "rule_based" | "ml_model" — POC transparency


class BatchCategorizeRequest(BaseModel):
    items: list[CategorizeRequest]


class BatchCategorizeResponse(BaseModel):
    results: list[CategorizeResponse]
