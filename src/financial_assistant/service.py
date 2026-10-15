
"""
HisabDo AI Financial Assistant service.

Routes user questions to the appropriate handler:
- Third-party financial data requests are refused.
- Greetings are handled without an LLM call.
- Personal financial figures come only from the backend financial API.
- Verified FAQ and product documentation questions use RAG.
- Unsupported product-specific questions receive a safe fallback.
- General questions can use the general LLM flow.
"""

import logging
import re

from ..integration.backend_client import get_backend_client
from ..schemas import ChatbotRequest, ChatbotResponse
from .llm_providers import get_llm_provider
from .faq_rag import get_retriever
from .rag_pipeline import prepare_context, format_context_block
from .intent_router import (
    classify_intent,
    extract_slots,
    get_missing_fields,
    build_follow_up,
)

logger = logging.getLogger("financial_assistant.service")


OWN_FINANCIAL_DATA_PATTERNS = [
    r"\bmy balance\b",
    r"\bmy expenses?\b",
    r"\bmy revenue\b",
    r"\bhow much (have i|did i) spen[dt]\b",
    r"\bmy outstanding\b",
    r"\bwhat('?s| is) my\b.*\b(balance|expense|revenue|outstanding)\b",
]

THIRD_PARTY_RELATIONSHIP_WORDS = re.compile(
    r"\b(his|her|their|its|someone else'?s|other user'?s|another user'?s|"
    r"other person'?s|another person'?s|friend'?s|colleague'?s|coworker'?s|"
    r"wife'?s|husband'?s|spouse'?s|partner'?s|boyfriend'?s|girlfriend'?s|"
    r"brother'?s|sister'?s|mother'?s|father'?s|mom'?s|dad'?s|boss'?s|"
    r"manager'?s|client'?s|customer'?s|employee'?s|roommate'?s|teammate'?s)\b",
    re.IGNORECASE,
)

THIRD_PARTY_ID_REFERENCE = re.compile(
    r"\b(user|account|customer|client)\s*#?\s*\d+\b",
    re.IGNORECASE,
)

_SAFE_POSSESSIVE_WORDS = {
    "my", "this", "that", "today's", "month's", "week's", "year's",
    "quarter's", "day's", "account's", "app's", "system's",
}

THIRD_PARTY_REFUSAL_MESSAGE = (
    "I'm sorry, but I can only provide information about your own account."
)

SMALL_TALK_REPLIES = {
    "salam": "Wa Alaikum Assalam! How can I help you with HisabDo today?",
    "wellbeing": "I'm doing well, thank you! How can I help you with HisabDo today?",
    "thanks": "You're welcome! Let me know if there's anything else I can help with.",
    "farewell": "Take care! Come back anytime you need help with HisabDo.",
    "greeting": "Hello! How can I help you with HisabDo today?",
}

FAQ_NO_MATCH_REPLY = (
    "I couldn't find relevant verified information in the HisabDo "
    "documentation or FAQs. Please contact HisabDo support for confirmation."
)

FAQ_RETRIEVAL_ERROR_REPLY = (
    "I couldn't search the HisabDo knowledge base right now. "
    "Please try again later."
)

PRODUCT_SPECIFIC_TERMS = re.compile(
    r"\bhisabdo\b|"
    r"\bin the app\b|"
    r"\bthis app\b|"
    r"\bapp feature\b|"
    r"\bpdf reports?\b|"
    r"\bfinancial reports?\b|"
    r"\bexport\b|"
    r"\bdownload\b|"
    r"\badd (?:a )?customer\b|"
    r"\bcustomer screen\b|"
    r"\bsettings\b|"
    r"\bdashboard\b|"
    r"\baccount setup\b|"
    r"\bhow do i use\b",
    re.IGNORECASE,
)


def _is_product_specific_query(message: str) -> bool:
    """Identify questions about HisabDo features and app-specific steps."""
    return bool(PRODUCT_SPECIFIC_TERMS.search(message))


def _no_verified_faq_response(
    request: ChatbotRequest,
) -> ChatbotResponse:
    """Avoid inventing answers to unsupported product-specific questions."""
    return ChatbotResponse(
        reply=FAQ_NO_MATCH_REPLY,
        conversation_id=request.conversation_id,
        intent="product_faq",
        tokens_used=0,
        source="rag_no_match",
    )


def _mentions_bare_name_possessive(message: str) -> bool:
    """Detect references such as 'Ali's balance'."""
    words = message.split()

    for index, word in enumerate(words):
        if index == 0:
            continue

        stripped = word.rstrip(",.?!")

        if re.fullmatch(r"[A-Z][a-zA-Z]*'s", stripped):
            if stripped.lower() not in _SAFE_POSSESSIVE_WORDS:
                return True

    return False


def _mentions_third_party(message: str) -> bool:
    if THIRD_PARTY_RELATIONSHIP_WORDS.search(message):
        return True

    if THIRD_PARTY_ID_REFERENCE.search(message):
        return True

    return _mentions_bare_name_possessive(message)


def _is_own_financial_data_query(message: str) -> bool:
    if _mentions_third_party(message):
        return False

    text = message.lower()

    return any(
        re.search(pattern, text)
        for pattern in OWN_FINANCIAL_DATA_PATTERNS
    )


def _format_financial_summary(summary: dict) -> str:
    return (
        f"Balance: {summary['balance']} {summary['currency']}. "
        f"Expenses this month: {summary['total_expenses_this_month']} "
        f"{summary['currency']}. "
        f"Revenue this month: {summary['total_revenue_this_month']} "
        f"{summary['currency']}. "
        f"Outstanding receivables: {summary['outstanding_receivables']} "
        f"{summary['currency']}."
    )


def _classify_small_talk(message: str) -> str | None:
    """Classify short greetings and pleasantries."""
    text = message.strip().lower()
    text = re.sub(r"[!?.,]+$", "", text).strip()

    if not text or len(text.split()) > 6:
        return None

    if re.search(
        r"assalam|salamu?\s*alaikum|\bsalam\b|\baoa\b",
        text,
    ):
        return "salam"

    if re.search(
        r"how\s*(are|r)\s*(you|u)\b|kaise\s*ho\b|kya\s*hal\s*hai\b",
        text,
    ):
        return "wellbeing"

    if re.search(r"\bthank(s| you)?\b|\bshukriya\b", text):
        return "thanks"

    if re.search(r"\b(bye|goodbye|good\s*night|see\s*you)\b", text):
        return "farewell"

    if re.search(
        r"\b(hi+|hello+|hey+|yo)\b|good\s*(morning|afternoon|evening)\b",
        text,
    ):
        return "greeting"

    return None


def _general_response(
    request: ChatbotRequest,
    provider,
    history: list[dict],
) -> ChatbotResponse:
    """Use the general LLM flow for non-product queries without a FAQ match."""
    reply, tokens = provider.generate_reply(
        request.message,
        context=None,
        history=history,
    )

    return ChatbotResponse(
        reply=reply,
        conversation_id=request.conversation_id,
        intent="general",
        tokens_used=tokens,
        source="llm_general",
    )


def _pending_transaction_intent(history: list[dict]) -> str | None:
    """Recover an expense/income intent when the assistant asked a follow-up."""
    last_assistant = None
    last_assistant_index = -1

    for index in range(len(history) - 1, -1, -1):
        if history[index].get("role") == "assistant":
            last_assistant = history[index].get("content", "").lower()
            last_assistant_index = index
            break

    if not last_assistant:
        return None

    is_follow_up = any(
        phrase in last_assistant
        for phrase in (
            "what was the amount?",
            "please describe the transaction.",
            "please provide the transaction amount and description.",
        )
    )

    if not is_follow_up:
        return None

    for turn in reversed(history[:last_assistant_index]):
        if turn.get("role") != "user":
            continue

        intent = classify_intent(turn.get("content", ""))

        if intent in {"expense", "income"}:
            return intent

    return None


def _handle_transaction_intent(
    message: str,
    history: list[dict],
    conversation_id: str,
) -> ChatbotResponse | None:
    """Collect transaction details without pretending to save a transaction."""
    intent = classify_intent(message)
    pending_intent = _pending_transaction_intent(history)

    if intent not in {"expense", "income"}:
        if pending_intent is None:
            return None
        intent = pending_intent

    slots = {}

    # Reuse details from the earlier user turn when answering a follow-up.
    if pending_intent == intent:
        for turn in reversed(history):
            if turn.get("role") == "user":
                previous_intent = classify_intent(turn.get("content", ""))

                if previous_intent == intent:
                    slots.update(extract_slots(turn["content"]))
                    break

    current_slots = extract_slots(message)
    slots.update(current_slots)

    last_assistant = next(
        (
            turn.get("content", "").lower()
            for turn in reversed(history)
            if turn.get("role") == "assistant"
        ),
        "",
    )

    if pending_intent == intent and "what was the amount?" in last_assistant:
        if "amount" not in current_slots:
            from decimal import Decimal, InvalidOperation

            bare_amount = re.fullmatch(
                r"\s*(\d[\d,]*(?:\.\d{1,2})?)\s*",
                message,
            )

            if bare_amount:
                try:
                    value = Decimal(bare_amount.group(1).replace(",", ""))

                    if value > 0:
                        slots["amount"] = str(value)

                except InvalidOperation:
                    pass

    if (
        pending_intent == intent
        and "please describe the transaction." in last_assistant
        and not current_slots.get("description")
    ):
        slots["description"] = message.strip(" .,")

    missing = get_missing_fields(intent, slots)

    if missing:
        reply = build_follow_up(intent, missing)
    else:
        amount = slots["amount"]
        description = slots["description"]
        reply = (
            f"I have the {intent} details: {amount} PKR for {description}. "
            "This is not saved yet; transaction saving is not enabled "
            "in this chatbot flow."
        )

    return ChatbotResponse(
        reply=reply,
        conversation_id=conversation_id,
        intent=intent,
        tokens_used=0,
        source="intent_router",
    )


def handle_chat(request: ChatbotRequest) -> ChatbotResponse:
    """Handle a chatbot request while preserving financial data boundaries."""

    # 1. Refuse requests for another person's financial data.
    if _mentions_third_party(request.message):
        return ChatbotResponse(
            reply=THIRD_PARTY_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_third_party",
            tokens_used=0,
            source="policy_guard",
        )

    # 2. Handle greetings without retrieval or LLM calls.
    small_talk = _classify_small_talk(request.message)

    if small_talk:
        return ChatbotResponse(
            reply=SMALL_TALK_REPLIES[small_talk],
            conversation_id=request.conversation_id,
            intent="general",
            tokens_used=0,
            source="greeting_fastpath",
        )

    provider = get_llm_provider()
    history = [item.model_dump() for item in request.history]

    # 3. Recognize expense/income requests and continue pending follow-ups.
    transaction_response = _handle_transaction_intent(
        request.message,
        history,
        request.conversation_id,
    )

    if transaction_response:
        return transaction_response

    # 4. Personal financial figures must come from the backend API.
    if _is_own_financial_data_query(request.message):
        summary = get_backend_client().get_user_financial_summary(
            request.user_id
        )

        context = _format_financial_summary(summary)

        reply, tokens = provider.generate_reply(
            request.message,
            context=context,
            history=history,
        )

        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="own_financial_data",
            tokens_used=tokens,
            source="backend_financial_api",
        )

    # 5. Retrieve verified FAQ and product documentation.
    try:
        matches = get_retriever().retrieve(
            request.message,
            top_k=3,
        )
    except Exception:
        logger.exception("FAQ semantic retrieval failed.")

        return ChatbotResponse(
            reply=FAQ_RETRIEVAL_ERROR_REPLY,
            conversation_id=request.conversation_id,
            intent="product_faq",
            tokens_used=0,
            source="rag_error",
        )

    # 6. No verified match: avoid guessing about product-specific features.
    if not matches:
        if _is_product_specific_query(request.message):
            return _no_verified_faq_response(request)

        return _general_response(request, provider, history)

    # 7. Normalize retrieved documents and build source-labelled context.
    context_chunks = []

    for match in matches:
        if not isinstance(match, dict):
            continue

        title = match.get("title") or "HisabDo Knowledge Base"
        content = match.get("text")

        if not isinstance(content, str) or not content.strip():
            continue

        context_chunks.append(
            {
                "text": content,
                "source": match.get("source") or title,
                "score": match.get("score"),
            }
        )

    prepared_context = prepare_context(context_chunks)
    context = format_context_block(prepared_context)

    # 8. Invalid or empty retrieved content must not trigger invented instructions.
    if not context:
        if _is_product_specific_query(request.message):
            return _no_verified_faq_response(request)

        return _general_response(request, provider, history)

    # 9. Generate an answer using retrieved context.
    reply, tokens = provider.generate_reply(
        request.message,
        context=context,
        history=history,
    )

    return ChatbotResponse(
        reply=reply,
        conversation_id=request.conversation_id,
        intent="product_faq",
        tokens_used=tokens,
        source="rag",
    )
