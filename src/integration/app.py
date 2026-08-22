"""FastAPI application for the HisabDo AI Financial Assistant.

Run from the repository root:

    uvicorn src.integration.app:app --reload --port 8000

Endpoints:
- GET  /health   : service + dependency status
- POST /chat     : run the assistant pipeline (with full evidence trace)
- POST /intents  : inspect intent detection only

The assistant pipeline itself is offline/deterministic; an API key is only
needed for the optional LLM polish step and is never required.
"""

from __future__ import annotations

import datetime as dt

from fastapi import FastAPI, HTTPException

from ..financial_assistant import engine as engine_mod
from ..financial_assistant import intents as intent_mod
from ..financial_assistant import knowledge_base as kb
from ..financial_assistant import llm as llm_mod
from .schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    IntentInfo,
    RetrievedEvidence,
)

app = FastAPI(
    title="HisabDo AI Financial Assistant API",
    description="Offline-first chatbot with RAG knowledge-base support.",
    version="0.1.0",
)

# A single shared assistant instance (stateless per request).
_ASSISTANT = None


def get_assistant(reference_date=None):
    """Return a shared stateless assistant (or one bound to ``reference_date``).

    The shared instance is never mutated; when a request supplies a reference
    date we build a separate instance so concurrent requests cannot race on
    shared state.
    """
    global _ASSISTANT
    if reference_date is not None:
        return engine_mod.FinancialAssistant(reference_date=reference_date)
    if _ASSISTANT is None:
        _ASSISTANT = engine_mod.FinancialAssistant()
    return _ASSISTANT


@app.get("/health", response_model=HealthResponse,
         responses={500: {"model": ErrorResponse}})
def health():
    assistant = get_assistant()
    kbs = kb.load_knowledge_base()
    return HealthResponse(
        status="ok",
        intents_supported=list(intent_mod.SUPPORTED_INTENTS),
        knowledge_base_chunks=len(kbs),
        transactions_loaded=len(assistant.transactions),
        llm_available=llm_mod.llm_available(),
    )


@app.post("/intents", response_model=IntentInfo)
def detect_intent_ep(request: ChatRequest):
    result = intent_mod.detect_intent(request.question)
    return IntentInfo(
        intent=result.intent,
        confidence=round(result.confidence, 2),
        period=result.period,
        category=result.category,
        matched=result.matched,
    )


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reference = None
    if request.reference_date:
        try:
            reference = dt.date.fromisoformat(request.reference_date)
        except ValueError as exc:
            raise HTTPException(status_code=422,
                                detail="reference_date must be YYYY-MM-DD") from exc
    assistant = get_assistant(reference)
    result = assistant.ask(request.question)
    return ChatResponse(
        question=result.question,
        intent=result.intent,
        confidence=result.confidence,
        response=result.response,
        period=result.period,
        category=result.category,
        facts=result.facts,
        retrieved=[
            RetrievedEvidence(title=r.chunk.title, score=r.score, text=r.chunk.text)
            for r in result.retrieved
        ],
        validation=result.validation,
        validation_notes=result.validation_notes,
        llm_used=result.llm_used,
        matched=result.matched,
    )