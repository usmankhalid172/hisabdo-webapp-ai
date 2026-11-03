"""
handle_chat — orchestrates the XICTEK website assistant request path:

    1. deterministic guardrails (length cap, injection/extraction heuristics)
    2. embed the query, retrieve top-k relevant chunks from the vector store
    3. call the configured LLM with retrieved context + SYSTEM_PROMPT
    4. shape the response, including which chunks it was grounded in

Steps 1 short-circuit before the LLM is ever called — see guardrails.py
for why that matters for prompt-injection resistance.
"""
from __future__ import annotations

import re
import time
from functools import lru_cache

import httpx

from ..logging_config import logger
from .config import get_xictek_settings
from .embeddings import embed_query
from .guardrails import (
    INJECTION_REFUSAL_MESSAGE,
    exceeds_length_limit,
    looks_like_injection_or_extraction,
)
from .llm_client import get_llm_provider
from .schemas import IndexStatsResponse, SourceRef, XictekChatRequest, XictekChatResponse
from .vector_store import VectorStore

LENGTH_REFUSAL_MESSAGE = (
    "That message is a bit long for me to process here — could you shorten it or ask "
    "one question at a time?"
)

# Greetings/small talk short-circuit — same rationale as the HisabDo
# chatbot's service.py: avoids the "I don't have that in the knowledge
# base" fallback firing on plain "hi"/"assalam o alaikum"/"thanks", and
# skips a wasted embed + vector-store query for messages that don't need it.
_SMALL_TALK_REPLIES = {
    "salam": "Wa Alaikum Assalam! How can I help you with XICTEK Systems today?",
    "wellbeing": "I'm doing great, thanks for asking! What would you like to know about XICTEK Systems?",
    "thanks": "You're welcome! Let me know if there's anything else you'd like to know about XICTEK.",
    "farewell": "Thanks for stopping by — feel free to reach out anytime!",
    "greeting": "Hello! I'm the XICTEK Systems assistant — ask me about our services, technology, HisabDo, or careers.",
}


def _classify_small_talk(message: str) -> str | None:
    """Returns a small-talk category if the WHOLE message is a short
    greeting/pleasantry, else None — a real question that happens to
    start with "hi" still goes through normal retrieval instead of being
    swallowed here."""
    text = message.strip().lower()
    text = re.sub(r"[!?.,]+$", "", text).strip()
    if not text or len(text.split()) > 6:
        return None
    if re.search(r"assalam|salamu?\s*alaikum|\bsalam\b|\baoa\b", text):
        return "salam"
    if re.search(r"how\s*(are|r)\s*(you|u)\b|kaise\s*ho\b|kya\s*hal\s*hai\b", text):
        return "wellbeing"
    if re.search(r"\bthank(s| you)?\b|\bshukriya\b", text):
        return "thanks"
    if re.search(r"\b(bye|goodbye|good\s*night|see\s*you)\b", text):
        return "farewell"
    if re.search(r"\b(hi+|hello+|hey+|yo)\b|good\s*(morning|afternoon|evening)\b", text):
        return "greeting"
    return None


@lru_cache
def _load_store() -> VectorStore:
    # Cached for the process lifetime: the index only changes when
    # ingest.py is re-run (a deploy-time/offline step), not per-request.
    # If you re-run ingest.py against a live process, restart it (or call
    # `_load_store.cache_clear()`) to pick up the new index.
    return VectorStore.load()


LLM_UNAVAILABLE_MESSAGE = (
    "Sorry, I'm getting a lot of questions right now and couldn't finish that answer. "
    "Please try again in a moment, or reach the XICTEK team through the Contact page."
)

NO_GROUNDED_ANSWER_MESSAGE = (
    "I don't have a verified answer to that in XICTEK's public content yet. "
    "Please check the relevant page or contact XICTEK directly."
)

_PORTFOLIO_QUERY_RE = re.compile(
    r"\b(portfolio|case\s*stud(?:y|ies)|past\s+projects?|client\s+work|"
    r"client\s+(?:roi|results?|outcomes?|impact|metrics?)|"
    r"project\s+(?:outcomes?|results?|impact|metrics?)|"
    r"(?:outcomes?|results?|impact|metrics?)\s+(?:of|from|for)\s+(?:hisabdo|the\s+project))\b",
    re.IGNORECASE,
)
_PORTFOLIO_URL_PREFIX = "https://xicteksystems.com/portfolio"


def handle_chat(request: XictekChatRequest) -> XictekChatResponse:
    started = time.perf_counter()
    metrics = {
        "provider": "not_called",
        "provider_called": False,
        "query_outcome": "error",
        "query_success": False,
        "response_completed": False,
        "portfolio_query": False,
        "retrieved_chunks": 0,
        "tokens_used": None,
        "input_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
        "usage_basis": "unavailable",
        "retrieval_duration_ms": 0.0,
        "provider_duration_ms": 0.0,
        "total_duration_ms": 0.0,
        "error_category": None,
        "error_stage": "validation",
    }
    try:
        return _handle_chat(request, metrics)
    except Exception as exc:
        metrics["query_outcome"] = "error"
        stage = metrics["error_stage"]
        metrics["error_category"] = _error_category(
            exc, stage if isinstance(stage, str) else "request_processing"
        )
        raise
    finally:
        metrics["total_duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
        logger.info("xictek_query_metrics", extra=metrics)


def _error_category(exc: Exception, stage: str) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "provider_timeout" if stage.startswith("provider") else "request_timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 429:
            return "provider_rate_limited"
        if status >= 500:
            return "provider_unavailable"
        return "provider_http_error"
    if stage == "provider_setup":
        return "provider_configuration_error"
    if stage == "provider_call":
        return "provider_error"
    if stage == "retrieval":
        return "retrieval_error"
    return "request_processing_error"


def _handle_chat(
    request: XictekChatRequest, metrics: dict[str, object]
) -> XictekChatResponse:
    settings = get_xictek_settings()
    message = request.message

    if exceeds_length_limit(message, settings.max_message_chars):
        metrics.update(
            query_outcome="declined_out_of_scope",
            response_completed=True,
            error_stage=None,
        )
        return XictekChatResponse(
            reply=LENGTH_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_out_of_scope",
        )

    if looks_like_injection_or_extraction(message):
        # Deterministic refusal — never reaches the LLM.
        metrics.update(
            query_outcome="declined_prompt_injection",
            response_completed=True,
            error_stage=None,
        )
        return XictekChatResponse(
            reply=INJECTION_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_prompt_injection",
        )

    small_talk = _classify_small_talk(message)
    if small_talk:
        metrics.update(
            query_outcome="small_talk",
            response_completed=True,
            error_stage=None,
        )
        return XictekChatResponse(
            reply=_SMALL_TALK_REPLIES[small_talk],
            conversation_id=request.conversation_id,
            sources=[],
            intent="general",
            tokens_used=0,
        )

    portfolio_query = bool(_PORTFOLIO_QUERY_RE.search(message))
    metrics["portfolio_query"] = portfolio_query
    metrics["error_stage"] = "retrieval"
    retrieval_started = time.perf_counter()
    try:
        store = _load_store()
        matches = []
        if len(store) > 0:
            query_vector = embed_query(message)
            matches = store.query(
                query_vector,
                top_k=settings.portfolio_top_k if portfolio_query else settings.top_k,
                relevance_threshold=settings.relevance_threshold,
                url_prefix=_PORTFOLIO_URL_PREFIX if portfolio_query else None,
            )
    finally:
        metrics["retrieval_duration_ms"] = round(
            (time.perf_counter() - retrieval_started) * 1000, 2
        )
    metrics["retrieved_chunks"] = len(matches)

    # Never ask the model to answer from conversation history or prior
    # assumptions when retrieval found no supporting public source.
    if not matches:
        metrics.update(
            query_outcome="no_evidence",
            response_completed=True,
            error_stage=None,
        )
        return XictekChatResponse(
            reply=NO_GROUNDED_ANSWER_MESSAGE,
            conversation_id=request.conversation_id,
            sources=[],
            intent="general",
            tokens_used=0,
        )

    context = "\n\n---\n\n".join(m.chunk.text for m in matches) if matches else None
    # Portfolio answers must not inherit client-supplied or spoofed history.
    history = [] if portfolio_query else [h.model_dump() for h in request.history]

    metrics["error_stage"] = "provider_setup"
    provider = get_llm_provider()
    metrics["provider"] = getattr(
        provider, "provider_name", type(provider).__name__.lower()
    )
    metrics["provider_called"] = True
    metrics["error_stage"] = "provider_call"
    provider_started = time.perf_counter()
    try:
        reply, tokens = provider.generate_reply(message, context=context, history=history)
    except Exception as exc:  # rate limit (429), timeout, provider outage -- degrade, don't 500
        metrics["provider_duration_ms"] = round(
            (time.perf_counter() - provider_started) * 1000, 2
        )
        metrics.update(
            query_outcome="provider_error",
            error_category=_error_category(exc, "provider_call"),
            response_completed=True,
            error_stage="provider_call",
        )
        return XictekChatResponse(
            reply=LLM_UNAVAILABLE_MESSAGE,
            conversation_id=request.conversation_id,
            sources=[],
            intent="general",
            tokens_used=0,
        )

    metrics["provider_duration_ms"] = round(
        (time.perf_counter() - provider_started) * 1000, 2
    )
    metrics.update(
        query_outcome="answered",
        query_success=True,
        response_completed=True,
        tokens_used=tokens,
        error_stage=None,
    )
    metrics.update(getattr(provider, "usage_metrics", {}))
    sources = [
        SourceRef(title=m.chunk.title, url=m.chunk.url, score=round(m.score, 4))
        for m in matches
    ]
    return XictekChatResponse(
        reply=reply,
        conversation_id=request.conversation_id,
        sources=sources,
        intent="answered" if matches else "general",
        tokens_used=tokens,
    )


def get_index_stats() -> IndexStatsResponse:
    store = _load_store()
    settings = get_xictek_settings()
    return IndexStatsResponse(
        chunk_count=len(store),
        embedding_model=settings.embedding_model,
        index_built=len(store) > 0,
    )
