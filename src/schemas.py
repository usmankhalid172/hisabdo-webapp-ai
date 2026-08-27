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

class ChatbotRequest(BaseModel):
    user_id: str
    message: str = Field(min_length=1)
    conversation_id: str
    history: list[dict] = Field(default_factory=list)


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
