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
from functools import lru_cache

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


def handle_chat(request: XictekChatRequest) -> XictekChatResponse:
    settings = get_xictek_settings()
    message = request.message

    if exceeds_length_limit(message, settings.max_message_chars):
        return XictekChatResponse(
            reply=LENGTH_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_out_of_scope",
        )

    if looks_like_injection_or_extraction(message):
        # Deterministic refusal — never reaches the LLM.
        return XictekChatResponse(
            reply=INJECTION_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_prompt_injection",
        )

    small_talk = _classify_small_talk(message)
    if small_talk:
        return XictekChatResponse(
            reply=_SMALL_TALK_REPLIES[small_talk],
            conversation_id=request.conversation_id,
            sources=[],
            intent="general",
            tokens_used=0,
        )

    store = _load_store()
    matches = []
    if len(store) > 0:
        query_vector = embed_query(message)
        matches = store.query(query_vector, top_k=settings.top_k, relevance_threshold=settings.relevance_threshold)

    context = "\n\n---\n\n".join(m.chunk.text for m in matches) if matches else None
    history = [h.model_dump() for h in request.history]

    provider = get_llm_provider()
    reply, tokens = provider.generate_reply(message, context=context, history=history)

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
