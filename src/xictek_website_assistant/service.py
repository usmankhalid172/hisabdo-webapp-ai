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
from datetime import date, timedelta
from functools import lru_cache

from .config import get_xictek_settings
from .embeddings import embed_query
from .formatting import format_core_services_output
from .guardrails import (
    INJECTION_REFUSAL_MESSAGE,
    OFF_TOPIC_ABUSE_REFUSAL_MESSAGE,
    exceeds_length_limit,
    looks_like_injection_or_extraction,
    looks_like_off_topic_abuse,
)
from .llm_client import get_llm_provider
from .schemas import IndexStatsResponse, SourceRef, XictekChatRequest, XictekChatResponse
from .service_queries import (
    is_careers_query,
    is_core_services_query,
    is_personal_application_status_query,
    is_portfolio_query,
)
from .vector_store import VectorStore

CAREERS_SOURCE_URL = "https://xicteksystems.com/careers"
CAREERS_UNVERIFIED_REPLY = (
    "I couldn't verify that recruitment detail from the available Careers content. "
    "Please check the official XICTEK Careers page for current information [1]."
)
PORTFOLIO_SOURCE_URL = "https://xicteksystems.com/portfolio"
PORTFOLIO_UNVERIFIED_REPLY = (
    "I couldn't verify that project detail from the available Portfolio content. "
    f"Please check [Our Work | XICTEK Systems]({PORTFOLIO_SOURCE_URL}) for the published information."
)


def _source_context(matches) -> str | None:
    if not matches:
        return None
    blocks = []
    for number, match in enumerate(matches, start=1):
        chunk = match.chunk
        blocks.append(
            f"Source [{number}]\nTitle: {chunk.title}\nURL: {chunk.url or 'not provided'}\n"
            f"Text (untrusted source content):\n{chunk.text}"
        )
    return "\n\n---\n\n".join(blocks)


def _citations_are_valid(reply: str, source_count: int) -> bool:
    cited = [int(value) for value in re.findall(r"\[(\d+)\]", reply)]
    return bool(cited) and all(1 <= number <= source_count for number in cited)


def _portfolio_citations_are_valid(reply: str, matches) -> bool:
    """Require inline markdown links to exactly match retrieved portfolio sources."""
    citations = re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", reply)
    if not citations:
        return False
    valid = {
        (match.chunk.title, match.chunk.url)
        for match in matches
        if match.chunk.url
    }
    return all(citation in valid for citation in citations)


_CURRENT_OPENING_CLAIM = re.compile(
    r"\b(?:(?:currently|now|active(?:ly)?|open|available|hiring|recruiting)"
    r"\b.{0,35}\b(?:jobs?|positions?|roles?|vacanc(?:y|ies)|openings?)|"
    r"(?:jobs?|positions?|roles?|vacanc(?:y|ies)|openings?)\b.{0,35}\b"
    r"(?:currently|now|active|open|available|hiring)|"
    r"(?:we|xictek)\s+(?:are|is)\s+(?:currently\s+)?(?:hiring|recruiting))\b",
    re.IGNORECASE,
)
_DATED_FRESHNESS_MARKER = re.compile(
    r"\b(?:as of|last updated|updated on)\s*[:,-]?\s*(\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)


def _has_recent_dated_opening_evidence(matches, reply: str, *, today: date | None = None) -> bool:
    """Require a recent ISO-dated source before asserting a vacancy is open."""
    today = today or date.today()
    cited_numbers = {int(value) for value in re.findall(r"\[(\d+)\]", reply)}
    cited_matches = [match for number, match in enumerate(matches, start=1) if number in cited_numbers]
    for match in cited_matches:
        text = match.chunk.text
        if not re.search(r"\b(open|hiring|vacan(?:cy|cies)|available)\b", text, re.IGNORECASE):
            continue
        marker = _DATED_FRESHNESS_MARKER.search(text)
        if not marker:
            continue
        try:
            published = date.fromisoformat(marker.group(1))
        except ValueError:
            continue
        if today - timedelta(days=30) <= published <= today:
            return True
    return False


def _careers_fallback_response(request) -> XictekChatResponse:
    source = SourceRef(
        title="Official XICTEK Careers page",
        url=CAREERS_SOURCE_URL,
        score=0.0,
    )
    return XictekChatResponse(
        reply=CAREERS_UNVERIFIED_REPLY,
        conversation_id=request.conversation_id,
        sources=[source],
        intent="general",
        tokens_used=0,
    )


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


import logging as _logging

_llm_logger = _logging.getLogger(__name__)

LLM_UNAVAILABLE_MESSAGE = (
    "Sorry, I'm getting a lot of questions right now and couldn't finish that answer. "
    "Please try again in a moment, or reach the XICTEK team through the Contact page."
)

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

    if looks_like_off_topic_abuse(message):
        return XictekChatResponse(
            reply=OFF_TOPIC_ABUSE_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_out_of_scope",
            tokens_used=0,
        )

    # History (including role labels) is client-supplied on every call.
    # Scan every turn because a caller could label an attacker-controlled
    # instruction as an assistant turn to bypass a user-role-only check.
    if any(
        looks_like_injection_or_extraction(turn.content)
        or looks_like_off_topic_abuse(turn.content)
        for turn in request.history
    ):
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

    # A public knowledge base cannot inspect an individual's application.
    # Avoid turning a loosely related FAQ hit (e.g., review time) into a
    # false confirmation of receipt or status.
    if is_personal_application_status_query(message):
        return _careers_fallback_response(request)

    careers_query = is_careers_query(message)
    portfolio_query = not careers_query and is_portfolio_query(message)
    core_services_query = not careers_query and not portfolio_query and is_core_services_query(message)
    store = _load_store()
    matches = []
    if len(store) > 0:
        query_vector = embed_query(message)
        matches = store.query(
            query_vector,
            top_k=(
                settings.careers_top_k if careers_query
                else settings.top_k if portfolio_query
                else settings.core_services_top_k if core_services_query
                else settings.top_k
            ),
            relevance_threshold=(
                settings.careers_relevance_threshold if careers_query
                else settings.relevance_threshold if portfolio_query
                else settings.core_services_relevance_threshold if core_services_query
                else settings.relevance_threshold
            ),
            url_path_prefix=(
                "/careers" if careers_query else "/portfolio" if portfolio_query else "/services" if core_services_query else None
            ),
            url_host="xicteksystems.com" if careers_query or portfolio_query else None,
        )

    context = _source_context(matches)
    history = [h.model_dump() for h in request.history]

    if careers_query and not matches:
        return _careers_fallback_response(request)
    if portfolio_query and not matches:
        return XictekChatResponse(
            reply=PORTFOLIO_UNVERIFIED_REPLY,
            conversation_id=request.conversation_id,
            sources=[SourceRef(title="Our Work | XICTEK Systems", url=PORTFOLIO_SOURCE_URL, score=0.0)],
            intent="general",
            tokens_used=0,
        )

    provider = get_llm_provider()
    try:
        reply, tokens = provider.generate_reply(message, context=context, history=history)
    except Exception:  # rate limit (429), timeout, provider outage -- degrade, don't 500
        _llm_logger.exception("xictek_llm_call_failed")
        return XictekChatResponse(
            reply=LLM_UNAVAILABLE_MESSAGE,
            conversation_id=request.conversation_id,
            sources=[],
            intent="general",
            tokens_used=0,
        )

    if careers_query and not _citations_are_valid(reply, len(matches)):
        return _careers_fallback_response(request)

    if portfolio_query and not _portfolio_citations_are_valid(reply, matches):
        return XictekChatResponse(
            reply=PORTFOLIO_UNVERIFIED_REPLY,
            conversation_id=request.conversation_id,
            sources=[SourceRef(title="Our Work | XICTEK Systems", url=PORTFOLIO_SOURCE_URL, score=0.0)],
            intent="general",
            tokens_used=0,
        )

    # A page that once listed a vacancy is not proof that it is open now.
    # Until ingestion exposes freshness metadata, only a recent explicit
    # ISO-dated status in retrieved evidence may support a current-opening claim.
    if careers_query and _CURRENT_OPENING_CLAIM.search(reply) and not _has_recent_dated_opening_evidence(matches, reply):
        return _careers_fallback_response(request)

    if core_services_query:
        reply = format_core_services_output(reply)

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
