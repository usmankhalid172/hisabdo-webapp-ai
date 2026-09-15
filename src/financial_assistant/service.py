"""
chatbot_service — builds prompt/context, calls the configured LLM, and
post-processes the reply, per Day 15 §6.1.

Critical boundary (Day 15 §6.1, restated in Day 16 continuity plan §2):
exact user financial figures never come from RAG. If the message is asking
about the user's own numbers, this routes to the (mocked) backend financial
API instead of the knowledge base.
"""
import re

from ..integration.backend_client import get_backend_client
from ..schemas import ChatbotRequest, ChatbotResponse
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


def handle_chat(request: ChatbotRequest) -> ChatbotResponse:
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

    provider = get_llm_provider()

    if _is_own_financial_data_query(request.message):
        # Authoritative data path — never touches the RAG knowledge base.
        summary = get_backend_client().get_user_financial_summary(request.user_id)
        context = _format_financial_summary(summary)
        reply, tokens = provider.generate_reply(request.message, context=context, history=[h.model_dump() for h in request.history])
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="own_financial_data",
            tokens_used=tokens,
            source="backend_financial_api",
        )

    matches = get_retriever().retrieve(request.message, top_k=1)
    if matches:
        context = matches[0]["text"]
        reply, tokens = provider.generate_reply(request.message, context=context, history=[h.model_dump() for h in request.history])
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="product_faq",
            tokens_used=tokens,
            source="rag",
        )

    reply, tokens = provider.generate_reply(request.message, context=None, history=[h.model_dump() for h in request.history])
    return ChatbotResponse(
        reply=reply,
        conversation_id=request.conversation_id,
        intent="general",
        tokens_used=tokens,
        source="llm_general",
    )
