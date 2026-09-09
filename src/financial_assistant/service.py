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


def handle_chat(request: ChatbotRequest) -> ChatbotResponse:
    provider = get_llm_provider()

    if _is_own_financial_data_query(request.message):
        # Authoritative data path — never touches the RAG knowledge base.
        summary = get_backend_client().get_user_financial_summary(request.user_id)
        context = _format_financial_summary(summary)
        reply, tokens = provider.generate_reply(request.message, context=context)
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
        reply, tokens = provider.generate_reply(request.message, context=context)
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="product_faq",
            tokens_used=tokens,
            source="rag",
        )

    reply, tokens = provider.generate_reply(request.message, context=None)
    return ChatbotResponse(
        reply=reply,
        conversation_id=request.conversation_id,
        intent="general",
        tokens_used=tokens,
        source="llm_general",
    )
