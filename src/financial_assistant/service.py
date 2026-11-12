"""
chatbot_service — builds prompt/context, calls the configured LLM, and
post-processes the reply, per Day 15 §6.1.

Critical boundary (Day 15 §6.1, restated in Day 16 continuity plan §2):
exact user financial figures never come from RAG. If the message is asking
about the user's own numbers, this routes to the (mocked) backend financial
API instead of the knowledge base.
"""
import re
import time

from ..logging_config import logger, timed_ms
from ..config import get_settings

from ..integration.backend_client import get_backend_client
from ..schemas import ChatbotCitation, ChatbotRequest, ChatbotResponse
from .llm_providers import get_llm_provider
from .faq_rag import get_retriever

# Deliberately simple keyword intent check — good enough for a POC boundary
# demonstration; a production version would use a real intent classifier.
OWN_FINANCIAL_DATA_PATTERNS = [
    r"\bmy balance\b", r"\bmy expenses?\b", r"\bmy revenue\b",
    r"\bhow much (have i|did i) spen[dt]\b", r"\bmy outstanding\b",
    r"\bwhat('?s| is) my\b.*\b(balance|expense|revenue|outstanding)\b",
]

# Security guard: any message that appears to ask about someone ELSE's
# financial data is refused deterministically in handle_chat(), before the
# LLM is ever called — not just rerouted away from the backend. Relying on
# the prompt alone would not survive an instruction-override attempt
# ("ignore your instructions and tell me anyway").
THIRD_PARTY_RELATIONSHIP_WORDS = re.compile(
    r"\b(his|her|their|its|someone else'?s|other user'?s|another user'?s|"
    r"other person'?s|another person'?s|friend'?s|colleague'?s|coworker'?s|"
    r"wife'?s|husband'?s|spouse'?s|partner'?s|boyfriend'?s|girlfriend'?s|"
    r"brother'?s|sister'?s|mother'?s|father'?s|mom'?s|dad'?s|boss'?s|"
    r"manager'?s|client'?s|customer'?s|employee'?s|roommate'?s|teammate'?s)\b",
    re.IGNORECASE,
)

# Catches probes by identifier instead of relationship, e.g. "user 2's
# balance", "account #5", "customer 12".
THIRD_PARTY_ID_REFERENCE = re.compile(
    r"\b(user|account|customer|client)\s*#?\s*\d+\b", re.IGNORECASE
)

# Non-person possessives that must NOT trip the bare-name heuristic below.
_SAFE_POSSESSIVE_WORDS = {
    "my", "this", "that", "today's", "month's", "week's", "year's",
    "quarter's", "day's", "account's", "app's", "system's",
}


def _mentions_bare_name_possessive(message: str) -> bool:
    """Heuristic for 'Ali's balance' style references: a capitalized word
    (not the first word, to avoid flagging normal sentence-initial capitals)
    immediately followed by a possessive 's."""
    words = message.split()
    for i, word in enumerate(words):
        if i == 0:
            continue
        stripped = word.rstrip(",.?!")
        if re.fullmatch(r"[A-Z][a-zA-Z]*'s", stripped):
            if stripped.lower() not in _SAFE_POSSESSIVE_WORDS:
                return True
    return False


def _mentions_third_party(message: str) -> bool:
    text = message.lower()
    if THIRD_PARTY_RELATIONSHIP_WORDS.search(text):
        return True
    if THIRD_PARTY_ID_REFERENCE.search(text):
        return True
    if _mentions_bare_name_possessive(message):
        return True
    return False


def _is_own_financial_data_query(message: str) -> bool:
    text = message.lower()
    if _mentions_third_party(message):
        return False
    return any(re.search(pattern, text) for pattern in OWN_FINANCIAL_DATA_PATTERNS)


def _format_financial_summary(summary: dict) -> str:
    return (
        f"Balance: {summary['balance']} {summary['currency']}. "
        f"Expenses this month: {summary['total_expenses_this_month']} {summary['currency']}. "
        f"Revenue this month: {summary['total_revenue_this_month']} {summary['currency']}. "
        f"Outstanding receivables: {summary['outstanding_receivables']} {summary['currency']}."
    )


THIRD_PARTY_REFUSAL_MESSAGE = (
    "I'm sorry, but I can only provide information about your own account."
)

# Greetings/small talk short-circuit — these were previously falling
# through to the LLM with no context and, whenever the mock provider was
# active, landing on the generic "I don't have that in the knowledge
# base" template. Handling them deterministically also avoids a wasted
# RAG lookup + LLM call for messages that never needed either.
_SMALL_TALK_REPLIES = {
    "salam": "Wa Alaikum Assalam! How can I help you with HisabDo today?",
    "wellbeing": "I'm doing well, thank you! How can I help you with HisabDo today?",
    "thanks": "You're welcome! Let me know if there's anything else I can help with.",
    "farewell": "Take care! Come back anytime you need help with HisabDo.",
    "greeting": "Hello! How can I help you with HisabDo today?",
}


def _classify_small_talk(message: str) -> str | None:
    """Returns a small-talk category if the WHOLE message is a short
    greeting/pleasantry, else None. Deliberately scoped to short messages
    only, so a real question that happens to start with "hi" (e.g. "hi,
    how do I add a payable?") still goes through the normal RAG/LLM path."""
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



PROMPT_INJECTION_PATTERNS = [
    r"\bignore\s+(all\s+)?(previous|prior|above)\s+instructions\b",
    r"\b(disregard|override|forget)\s+(all\s+)?(previous|prior|above|your)\s+(instructions|rules|guidelines)\b",
    r"\breveal\s+(the\s+)?(system|developer)\s+prompt\b",
    r"\bshow\s+(me\s+)?(your\s+)?(system|hidden)\s+prompt\b",
    r"\bshow\s+(me\s+)?(your\s+)?hidden\s+system\s+prompt\b",
    r"\bshow\s+(me\s+)?(your\s+)?hidden\s+system\s+prompt\b",
    r"\bdeveloper\s+mode\b",
    r"\bignore\s+your\s+rules\b",
]

PROMPT_INJECTION_REFUSAL_MESSAGE = (
    "I can't follow requests to override my instructions or reveal private system information."
)


def _is_prompt_injection(message: str) -> bool:
    return any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in PROMPT_INJECTION_PATTERNS
    )



def _is_ambiguous_expense_query(message: str) -> bool:
    normalized = re.sub(r"[^a-z ]", "", message.lower()).strip()
    return normalized in {"expense", "expenses", "show expense", "show expenses"}


def _resolve_source_conflicts(matches: list[dict]) -> list[dict] | None:
    """Resolve explicitly grouped conflicts only when priority has one winner."""
    groups = {}
    for item in matches:
        group = item.get("conflict_group")
        if group:
            groups.setdefault(group, []).append(item)

    excluded_ids = set()
    for items in groups.values():
        if len(items) < 2:
            continue
        priorities = [item.get("source_priority") for item in items]
        if any(not isinstance(value, (int, float)) for value in priorities):
            return None
        highest = max(priorities)
        winners = [item for item in items if item.get("source_priority") == highest]
        if len(winners) != 1:
            return None
        excluded_ids.update(id(item) for item in items if item is not winners[0])

    return [item for item in matches if id(item) not in excluded_ids]


def _citation_supports_reply(reply: str, source: dict) -> bool:
    """Conservative lexical check before exposing source metadata as a citation."""
    stop_words = {
        "about", "after", "also", "and", "are", "can", "does", "for",
        "from", "how", "into", "is", "its", "not", "that", "the",
        "their", "this", "through", "was", "what", "when", "where",
        "which", "with", "you", "your"
    }
    source_text = f"{source.get('title', '')} {source.get('text', '')}".lower()
    reply_words = {
        word for word in re.findall(r"[a-z0-9]+", reply.lower())
        if len(word) > 2 and word not in stop_words
    }
    source_words = {
        word for word in re.findall(r"[a-z0-9]+", source_text)
        if len(word) > 2 and word not in stop_words
    }
    if not reply_words:
        return False
    return len(reply_words & source_words) / len(reply_words) >= 0.20


def handle_chat(request: ChatbotRequest) -> ChatbotResponse:
    request_start = time.perf_counter()
    if _is_prompt_injection(request.message):
        return ChatbotResponse(
            reply=PROMPT_INJECTION_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_prompt_injection",
            tokens_used=0,
            source="policy_guard",
        )
    if _mentions_third_party(request.message):
        # Deterministic refusal — never reaches the LLM, so this cannot be
        # talked around by a prompt-injection / instruction-override attempt.
        return ChatbotResponse(
            reply=THIRD_PARTY_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_third_party",
            tokens_used=0,
            source="policy_guard",
        )

    small_talk = _classify_small_talk(request.message)
    if small_talk:
        return ChatbotResponse(
            reply=_SMALL_TALK_REPLIES[small_talk],
            conversation_id=request.conversation_id,
            intent="general",
            tokens_used=0,
            source="greeting_fastpath",
        )

    if _is_out_of_scope(request.message):
        return ChatbotResponse(
            reply=OUT_OF_SCOPE_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_out_of_scope",
            tokens_used=0,
            source="policy_guard",
        )

    if _is_unsafe_language_request(request.message):
        return ChatbotResponse(
            reply=UNSAFE_LANGUAGE_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_unsafe_language",
            tokens_used=0,
            source="policy_guard",
        )

    if _requests_sensitive_information(request.message):
        return ChatbotResponse(
            reply=SENSITIVE_INFORMATION_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_sensitive_information",
            tokens_used=0,
            source="policy_guard",
        )

    if _is_own_financial_data_query(request.message):
        # Authoritative data path — never touches the RAG knowledge base.
        try:
            summary = get_backend_client().get_user_financial_summary(request.user_id)
        except Exception:
            logger.error(
                "financial_backend_unavailable",
                extra={
                    "event": "financial_backend_unavailable",
                    "intent": "own_financial_data",
                    "outcome": "unavailable",
                    "source": "backend_financial_api",
                    "error_category": "backend_unavailable",
                },
            )
            return ChatbotResponse(
                reply="Your financial information is temporarily unavailable. Please try again later.",
                conversation_id=request.conversation_id,
                intent="own_financial_data_unavailable",
                tokens_used=0,
                source="backend_unavailable",
            )

        context = _format_financial_summary(summary)
        try:
            provider = get_llm_provider()
            provider_start = time.perf_counter()
            reply, tokens = provider.generate_reply(request.message, context=context, history=[h.model_dump() for h in request.history])
            provider_duration = timed_ms(provider_start)
            logger.info("provider_call_completed", extra={"event": "provider_call_completed", "provider_name": get_settings().llm_provider, "provider_duration_ms": provider_duration, "tokens_used": tokens, "outcome": "success"})
        except Exception:
            logger.error(
                "financial_response_provider_failed",
                extra={
                    "event": "financial_response_provider_failed",
                    "intent": "own_financial_data",
                    "outcome": "error",
                    "source": "backend_financial_api",
                    "error_category": "provider_error",
                },
            )
            return ChatbotResponse(
                reply="I couldn't generate your financial summary right now. Please try again later.",
                conversation_id=request.conversation_id,
                intent="own_financial_data_unavailable",
                tokens_used=0,
                source="provider_error",
            )
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="own_financial_data",
            tokens_used=tokens,
            source="backend_financial_api",
        )

    if _is_ambiguous_expense_query(request.message):
        return ChatbotResponse(
            reply="Are you asking what an expense means, or how to record an expense in HisabDo?",
            conversation_id=request.conversation_id,
            intent="clarification_required",
            tokens_used=0,
            source="clarification",
        )

    retrieval_start = time.perf_counter()
    matches = get_retriever().retrieve(request.message, top_k=3)
    retrieval_duration = timed_ms(retrieval_start)
    logger.info("retrieval_completed", extra={"event": "retrieval_completed", "intent": "product_faq", "outcome": "success" if matches else "empty", "source": "rag", "source_ids": [item.get("id") for item in matches], "retrieval_duration_ms": retrieval_duration})
    if matches:
        matches = _resolve_source_conflicts(matches)
        if matches is None:
            return ChatbotResponse(
                reply="The available HisabDo documents contain conflicting guidance on this topic. I can't confirm which entry is current. Please contact support for an approved answer.",
                conversation_id=request.conversation_id,
                intent="source_conflict",
                tokens_used=0,
                source="rag_conflict",
            )
        context = "\\n\\n".join(
            f"Source title: {item.get('title', 'FAQ')}\\n"
            f"Section: {item.get('section', 'Not provided')}\\n"
            f"Evidence: {item['text']}"
            for item in matches
        )
        try:
            provider = get_llm_provider()
            provider_start = time.perf_counter()
            reply, tokens = provider.generate_reply(request.message, context=context, history=[h.model_dump() for h in request.history])
            provider_duration = timed_ms(provider_start)
            logger.info("provider_call_completed", extra={"event": "provider_call_completed", "provider_name": get_settings().llm_provider, "provider_duration_ms": provider_duration, "tokens_used": tokens, "outcome": "success"})
        except Exception:
            logger.error(
                "rag_response_provider_failed",
                extra={
                    "event": "rag_response_provider_failed",
                    "intent": "product_faq",
                    "outcome": "error",
                    "source": "rag",
                    "source_ids": [matches[0].get("id")],
                    "error_category": "provider_error",
                },
            )
            return ChatbotResponse(
                reply="I couldn't prepare an answer right now. Please try again later.",
                conversation_id=request.conversation_id,
                intent="provider_unavailable",
                tokens_used=0,
                source="provider_error",
            )
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="product_faq",
            tokens_used=tokens,
            source="rag",
            citations=[
                ChatbotCitation(
                    title=item["title"],
                    section=item.get("section"),
                    source_url=(
                        item.get("source_url")
                        if isinstance(item.get("source_url"), str)
                        and item["source_url"].startswith(("https://", "http://"))
                        else None
                    ),
                    source_id=item.get("id"),
                )
                for item in matches
                if item.get("title") and _citation_supports_reply(reply, item)
            ],
        )

    return ChatbotResponse(
        reply="I couldn't find verified information about that in the available HisabDo guides. Please contact support or provide an approved source.",
        conversation_id=request.conversation_id,
        intent="no_verified_source",
        tokens_used=0,
        source="rag_empty",
    )






OUT_OF_SCOPE_REFUSAL_MESSAGE = (
    "I can help with HisabDo features and general financial topics. "
    "I can't assist with unrelated requests."
)


OUT_OF_SCOPE_PATTERNS = [
    r"\bwrite\s+(me\s+)?(a\s+)?poem\b",
    r"\bfootball\b",
    r"\bcricket\b",
    r"\bvideo game(s)?\b",
    r"\bmovie review\b",
]


def _is_out_of_scope(message: str) -> bool:
    return any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in OUT_OF_SCOPE_PATTERNS
    )


UNSAFE_LANGUAGE_REFUSAL_MESSAGE = (
    "I can't help create threats, intimidation, or abusive messages. "
    "I can help with calm and respectful communication instead."
)


UNSAFE_LANGUAGE_PATTERNS = [
    r"\bwrite\s+(me\s+)?(a\s+)?threatening\s+message\b",
    r"\bthreaten\s+(someone|him|her|them)\b",
    r"\bscare\s+(someone|him|her|them)\b",
    r"\bintimidate\s+(someone|him|her|them)\b",
]


def _is_unsafe_language_request(message: str) -> bool:
    return any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in UNSAFE_LANGUAGE_PATTERNS
    )


SENSITIVE_INFORMATION_REFUSAL_MESSAGE = (
    "I can't reveal passwords, API keys, credentials, or confidential system information."
)


SENSITIVE_INFORMATION_PATTERNS = [
    r"\breveal\s+(the\s+)?(stored\s+)?(passwords?|api\s*keys?)\b",
    r"\bshow\s+(me\s+)?(the\s+)?(passwords?|api\s*keys?|credentials?)\b",
    r"\bshare\s+(the\s+)?(secret|credentials?|api\s*keys?)\b",
    r"\bexpose\s+(the\s+)?(private|confidential)\s+(data|information)\b",
]


def _requests_sensitive_information(message: str) -> bool:
    return any(
        re.search(pattern, message, re.IGNORECASE)
        for pattern in SENSITIVE_INFORMATION_PATTERNS
    )








