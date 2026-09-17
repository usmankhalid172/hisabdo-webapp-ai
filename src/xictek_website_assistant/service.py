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
