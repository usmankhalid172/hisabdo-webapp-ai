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
    """One prior conversation turn. Both fields are required — a malformed
    entry (e.g. Swagger's old default {} placeholder) is now rejected by
    FastAPI's own validation with a clean 422, instead of crashing deep
    inside the LLM provider with a raw 500."""
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


class ChatbotResponse(BaseModel):
    reply: str
    conversation_id: str
    intent: Optional[str] = None
    tokens_used: Optional[int] = None
    source: str  # "rag" | "backend_financial_api" | "llm_general" — POC transparency, not in Day 15 contract


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
class StructuredLLMResponse(BaseModel):
    model_config = {"extra": "forbid"}

    symptoms: list[str]
    severity: str
    message: str