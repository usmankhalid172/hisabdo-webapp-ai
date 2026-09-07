"""
chatbot_service — builds prompt/context, calls the configured LLM, and
post-processes the reply, per Day 15 §6.1.

Critical boundary (Day 15 §6.1, restated in Day 16 continuity plan §2):
exact user financial figures never come from RAG. If the message is asking
about the user's own numbers, this routes to the (mocked) backend financial
API instead of the knowledge base.

Error handling (Task 26 - RAG backend integration):
The service layer is the last line of defence against backend crashes. Every
external dependency - document-context (RAG) retrieval, the application
backend financial API, and the LLM provider - is wrapped so that a failure in
any one of them degrades gracefully to a user-safe fallback reply instead of
propagating an exception up to the HTTP layer (which would surface as a 500).
Fallbacks are surfaced with a distinct ``source`` so callers can tell them
apart from a real answer, and failures are logged internally (never leaked to
the client).
"""
import logging
import re

from ..integration.backend_client import get_backend_client
from ..schemas import ChatbotRequest, ChatbotResponse
from .llm_providers import get_llm_provider
from .rag import get_retriever

# Module logger - quieter than the shared request logger; used for
# dependency-failure diagnostics that should not appear on every request.
logger = logging.getLogger("financial_assistant.service")

FALLBACK_REPLY = (
    "I'm having trouble connecting to one of my data sources right now. "
    "Please try again in a moment, or contact support if the problem persists."
)

# Deliberately simple keyword intent check — good enough for a POC boundary
# demonstration; a production version would use a real intent classifier.
OWN_FINANCIAL_DATA_PATTERNS = [
    r"\bmy balance\b", r"\bmy expenses?\b", r"\bmy revenue\b",
    r"\bhow much (have i|did i) spen[dt]\b", r"\bmy outstanding\b",
    r"\bwhat('?s| is) my\b.*\b(balance|expense|revenue|outstanding)\b",
]


def _is_own_financial_data_query(message: str) -> bool:
    text = message.lower()
    return any(re.search(pattern, text) for pattern in OWN_FINANCIAL_DATA_PATTERNS)


def _format_financial_summary(summary: dict) -> str:
    return (
        f"Balance: {summary['balance']} {summary['currency']}. "
        f"Expenses this month: {summary['total_expenses_this_month']} {summary['currency']}. "
        f"Revenue this month: {summary['total_revenue_this_month']} {summary['currency']}. "
        f"Outstanding receivables: {summary['outstanding_receivables']} {summary['currency']}."
    )


def _safe_llm_reply(provider, message: str, context: str | None) -> tuple[str, int | None]:
    """Generate a reply, degrading to a user-safe fallback instead of crashing.

    Returns ``(reply, tokens)``. On LLM provider failure the fallback message
    is returned; the failure is logged internally so it is observable without
    leaking any internal detail to the client.
    """
    try:
        return provider.generate_reply(message, context=context)
    except Exception as exc:  # noqa: BLE001 - provider is an external boundary
        logger.warning("LLM provider failed (context=%s): %s",
                       bool(context), exc)
        return FALLBACK_REPLY, None


def handle_chat(request: ChatbotRequest) -> ChatbotResponse:
    provider = get_llm_provider()

    # Common payload that makes the reply self-describing for the caller:
    # user_id (session identity), model (which provider answered). These are
    # filled in on every path; ``matched_context`` is only set for RAG.
    def base(intent: str, source: str, reply: str,
             tokens: int | None, context_title: str | None = None) -> ChatbotResponse:
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            intent=intent,
            tokens_used=tokens,
            # model is optional metadata; be resilient to stub/failing providers.
            model=getattr(provider, "model_name", None),
            matched_context=context_title,
            source=source,
        )

    if _is_own_financial_data_query(request.message):
        # Authoritative data path — never touches the RAG knowledge base.
        # If the backend financial API is unavailable, degrade gracefully
        # instead of crashing the chatbot endpoint with a 500.
        try:
            summary = get_backend_client().get_user_financial_summary(
                request.user_id)
            context = _format_financial_summary(summary)
        except Exception as exc:  # noqa: BLE001 - backend is an external boundary
            logger.warning("Backend financial API unavailable for user %s: %s",
                           request.user_id, exc)
            reply, tokens = _safe_llm_reply(
                provider, request.message, context=None)
            return base("own_financial_data", "backend_unavailable",
                        reply, tokens)
        reply, tokens = _safe_llm_reply(provider, request.message, context=context)
        return base("own_financial_data", "backend_financial_api",
                    reply, tokens)

    # Document-context (RAG) fetch. A failure to read the knowledge base,
    # or a retrieve() error, must never crash the backend: on any retrieval
    # problem we fall through to the general reply path.
    try:
        matches = get_retriever().retrieve(request.message, top_k=1)
    except Exception as exc:  # noqa: BLE001 - retriever is an external boundary
        logger.warning("Document-context retrieval failed for query: %s", exc)
        matches = []

    if matches:
        context = matches[0]["text"]
        reply, tokens = _safe_llm_reply(provider, request.message, context=context)
        return base("product_faq", "rag", reply, tokens,
                    context_title=matches[0].get("title"))

    reply, tokens = _safe_llm_reply(provider, request.message, context=None)
    return base("general", "llm_general", reply, tokens)
