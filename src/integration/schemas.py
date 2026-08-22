"""Request/response schemas (Pydantic) for the HisabDo AI API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chatbot message."""
    question: str = Field(..., min_length=1, max_length=2000,
                          description="The user's financial question.")
    reference_date: Optional[str] = Field(
        None, pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Optional reference date (YYYY-MM-DD) for relative periods.")


class RetrievedEvidence(BaseModel):
    """One retrieved knowledge-base chunk."""
    title: str
    score: float
    text: str


class ChatResponse(BaseModel):
    """Outgoing chatbot answer with pipeline trace for evidence."""
    question: str
    intent: str
    confidence: float
    response: str
    period: Optional[str] = None
    category: Optional[str] = None
    facts: Dict[str, Any] = Field(default_factory=dict)
    retrieved: List[RetrievedEvidence] = Field(default_factory=list)
    validation: str = "pass"
    validation_notes: List[str] = Field(default_factory=list)
    llm_used: bool = False
    matched: List[str] = Field(default_factory=list)


class IntentInfo(BaseModel):
    intent: str
    confidence: float
    period: Optional[str] = None
    category: Optional[str] = None
    matched: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    intents_supported: List[str]
    knowledge_base_chunks: int
    transactions_loaded: int
    llm_available: bool


class ErrorResponse(BaseModel):
    detail: str