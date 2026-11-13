
"""
HisabDo AI Financial Assistant service.

Routes user questions to the appropriate handler:

- Third-party financial data requests are refused.
- Greetings are handled without an LLM call.
- Personal financial figures come only from the backend financial API.
- Verified FAQ and product documentation questions use RAG.
- PDF requests receive transparent product guidance.
- Unsupported product-specific questions receive a safe fallback.
- General questions can use the general LLM flow.
"""

import logging
import re
from decimal import Decimal, InvalidOperation

from src.errors import ServiceError

from ..integration.backend_client import get_backend_client
from ..schemas import ChatbotCitation, ChatbotRequest, ChatbotResponse
from .llm_providers import get_llm_provider
from .guardrails import (
    get_input_guardrail,
    get_history_guardrail,
    history_has_prompt_injection,
    contains_sensitive_output,
    wrap_untrusted_context,
    INJECTION_REPLY,
    UNSAFE_REPLY,
    OUT_OF_SCOPE_REPLY,
    INVALID_INPUT_REPLY,
    SENSITIVE_OUTPUT_REPLY,
)
from .faq_rag import get_retriever
from .rag_pipeline import prepare_context, format_context_block
from .monitoring import (
    start_timer,
    elapsed_ms,
    safe_log_event,
    monitoring_counters,
)
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
    "documentation or FAQs, so I can't confirm this detail. "
    "This chat does not have a verified support contact or ticket handoff, "
    "so I can't submit a request. Please ask the HisabDo product owner "
    "for the approved support route."
)

FAQ_RETRIEVAL_ERROR_REPLY = (
    "I couldn't search the HisabDo knowledge base right now. "
    "Please try again later."
)

PDF_GUIDANCE_REPLY = (
    "HisabDo supports PDF reports for supported records. "
    "Open Report in the app and select a period such as This Week, "
    "This Month, This Year, or All Time. In the tested app flow, "
    "the PDF action opened WhatsApp sharing instead of a PDF preview. "
    "This chatbot cannot currently generate or attach a PDF file directly."
)

# Recognize requests specifically about PDF report generation or downloading.
PDF_REQUEST_TERMS = re.compile(
    r"\bpdf\b|"
    r"\b(download|export|generate|create|share|open|send)\b.{0,50}\b(report|statement)\b|"
    r"\b(report|statement)\b.{0,50}\b(download|export|generate|create|pdf|share)\b|"
    r"\u067e\u06cc\s*\u0688\s*\u06cc\s*\u0627\u06cc\u0641|"
    r"\u0631\u067e\u0648\u0631\u0679\s*(\u0688\u0627\u0624\u0646\s*\u0644\u0648\u0688|\u0628\u0646\u0627|\u0686\u0627\u06c1\u06cc\u06d2|\u0686\u0627\u06c1\u06cc\u0626\u06d2|\u0628\u06be\u06cc\u062c)",
    re.IGNORECASE,
)

ACCOUNT_SUPPORT_PATTERN = re.compile(
    r"\b("
    r"can't log in|cant log in|cannot log in|cannot login|can't login|"
    r"login problem|login issue|unable to log in|"
    r"locked out|account locked|account is locked|locked account|"
    r"account disabled|account suspended|"
    r"reset my password|password reset|forgot my password|"
    r"change my email|change email address|change my phone|"
    r"change phone number|change account details|"
    r"delete my account|close my account|"
    r"account access|access my account|"
    r"verification code|account verification"
    r")\b",
    re.IGNORECASE,
)

PRODUCT_SPECIFIC_TERMS = re.compile(
    r"\bhisabdo\b|"
    r"\bin the app\b|"
    r"\bthis app\b|"
    r"\bapp feature\b|"
    r"\bpdf reports?\b|"
    r"\bfinancial reports?\b|"
    r"\bexpenses?\b|"
    r"\bincome\b|"
    r"\bexport\b|"
    r"\bdownload\b|"
    r"\badd (?:a )?customer\b|"
    r"\bcustomer screen\b|"
    r"\bsettings\b|"
    r"\bdashboard\b|"
    r"\u062e\u0631\u0686|"
    r"\u0622\u0645\u062f\u0646|"
    r"\u0627\u062f\u06be\u0627\u0631|"
    r"\u06a9\u06be\u0627\u062a\u06c1|"
    r"\u062a\u0641\u0635\u06cc\u0644|\u06a9\u06cc\u0633\u06d2|\u062f\u06cc\u06a9\u06be\u0648\u06ba|\u0627\u0633\u062a\u0639\u0645\u0627\u0644|"
    r"\bkhata\b|"
    r"\budhar\b",
    re.IGNORECASE,
)


def _is_pdf_request(message: str) -> bool:
    """Identify explicit PDF report and document requests."""
    return bool(PDF_REQUEST_TERMS.search(message))


def _is_product_specific_query(message: str) -> bool:
    """Identify questions about HisabDo features and app-specific steps."""
    return bool(PRODUCT_SPECIFIC_TERMS.search(message))


# Detect short follow-up questions that depend on the previous product question.
FAQ_FOLLOW_UP_PATTERN = re.compile(
    r"^\s*(?:"
    r"what about|how about|and what about|"
    r"what if|how does that work|"
    r"can i do that|does it also|"
    r"what about that|and this|"
    r"what about this|"
    r"how about this"
    r")\b",
    re.IGNORECASE,
)


def _build_faq_retrieval_query(
    message: str,
    history: list[dict],
) -> str:
    """
    Resolve short product follow-ups using the latest relevant user question.

    Previous assistant replies are never used as retrieval evidence.
    """
    current_message = message.strip()

    if not FAQ_FOLLOW_UP_PATTERN.search(current_message):
        return current_message

    previous_user_message = next(
        (
            turn.get("content", "").strip()
            for turn in reversed(history)
            if (
                turn.get("role") == "user"
                and isinstance(turn.get("content"), str)
                and turn.get("content", "").strip()
            )
        ),
        "",
    )

    if not previous_user_message:
        return current_message

    # Do not carry forward third-party financial requests.
    if _mentions_third_party(previous_user_message):
        return current_message

    # Do not use personal financial questions as product FAQ context.
    if _is_own_financial_data_query(previous_user_message):
        return current_message

    # Reuse context only when the previous user question was product-specific.
    if not _is_product_specific_query(previous_user_message):
        return current_message

    return (
        f"{previous_user_message}\n"
        f"Follow-up: {current_message}"
    )


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


def _guard_generated_reply(reply: str) -> str:
    if contains_sensitive_output(reply):
        logger.warning("Generated response blocked by sensitive-output guardrail.")
        return SENSITIVE_OUTPUT_REPLY
    return reply


def _filter_inline_citations(
    reply: str,
    matches: list,
    allowed_document_ids: set[str] | None = None,
) -> str:
    """Keep inline citations only when exact labels exist in verified context."""
    allowed_labels = set()

    for match in matches:
        if not isinstance(match, dict):
            continue
        if match.get("verified") is not True:
            continue

        document_id = match.get("id")
        if allowed_document_ids is not None and document_id not in allowed_document_ids:
            continue

        content = match.get("text")
        title = match.get("title")
        section = match.get("section")

        if not isinstance(content, str) or not content.strip():
            continue
        if not isinstance(title, str) or not title.strip():
            continue

        title = title.strip()
        if isinstance(section, str) and section.strip():
            allowed_labels.add(f"{title} ? {section.strip()}")
        else:
            allowed_labels.add(title)

    citation_pattern = re.compile(r"\[Source:\s*([^\]]+?)\s*\]")

    def keep_only_verified_label(match):
        label = match.group(1).strip()
        if label in allowed_labels:
            return f"[Source: {label}]"
        logger.warning("Unsupported inline citation label removed.")
        return ""

    return citation_pattern.sub(keep_only_verified_label, reply)


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
    reply = _guard_generated_reply(reply)

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


def _build_verified_citations(
    matches: list,
    allowed_document_ids: set[str] | None = None,
) -> list[ChatbotCitation]:
    """
    Build citations only from retrieved documents with usable source URLs.

    URLs and section names are taken from retrieval metadata; they are never
    constructed or guessed by the chatbot service.
    """
    citations = []
    seen_citations = set()

    for match in matches:
        if not isinstance(match, dict):
            continue

        # Only explicitly verified documents may provide citations.
        if match.get("verified") is not True:
            continue

        document_id = match.get("id")
        if allowed_document_ids is not None:
            if not isinstance(document_id, str) or document_id not in allowed_document_ids:
                continue

        content = match.get("text")
        if not isinstance(content, str) or not content.strip():
            continue

        title = match.get("title") or match.get("source")
        if not isinstance(title, str) or not title.strip():
            continue

        source_url = match.get("source_url") or match.get("url")
        section = match.get("section")

        # Do not invent or expose a URL that was not provided by retrieval.
        if not isinstance(source_url, str) or not source_url.strip():
            continue

        source_url = source_url.strip()

        from urllib.parse import urlparse

        parsed_url = urlparse(source_url)
        if (
            parsed_url.scheme not in ("https", "http")
            or not parsed_url.netloc
            or any(character.isspace() for character in source_url)
        ):
            continue

        section = (
            section.strip()
            if isinstance(section, str) and section.strip()
            else None
        )

        citation_key = (source_url, section)

        if citation_key in seen_citations:
            continue

        seen_citations.add(citation_key)

        citations.append(
            ChatbotCitation(
                title=title,
                source_url=source_url,
                section=section,
            )
        )

    return citations


def _find_verified_source_conflicts(matches: list) -> tuple[str, list] | None:
    """Detect conflicts only when verified entries share an explicit conflict key."""
    grouped = {}

    for match in matches:
        if not isinstance(match, dict) or match.get("verified") is not True:
            continue

        key = match.get("conflict_key")
        value = match.get("conflict_value")

        if not isinstance(key, str) or not key.strip():
            continue
        if not isinstance(value, str) or not value.strip():
            continue

        normalized_key = key.strip().casefold()
        grouped.setdefault(normalized_key, []).append(match)

    for key in sorted(grouped):
        entries = grouped[key]
        distinct_values = {
            entry["conflict_value"].strip()
            for entry in entries
        }
        if len(distinct_values) > 1:
            return key, sorted(
                entries,
                key=lambda item: (
                    str(item.get("title") or item.get("source") or ""),
                    str(item.get("id") or ""),
                ),
            )

    return None


def _ambiguous_expense_statement(message: str) -> bool:
    """Identify first-person expense statements that need intent clarification."""
    normalized = " ".join(message.lower().split())
    patterns = (
        r"\b(?:i|we)\s+(?:just\s+)?(?:spent|paid|bought|purchased)\b",
        r"\b(?:maine|humne)\b.*\b(?:kharch|kharcha|ada|kharida)\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _expense_clarification_response(
    conversation_id: str,
) -> ChatbotResponse:
    return ChatbotResponse(
        reply=(
            "Are you asking me to record this as an expense, "
            "or are you just mentioning it?"
        ),
        conversation_id=conversation_id,
        intent="expense_clarification",
        tokens_used=0,
        source="intent_router",
    )


def _handle_chat_impl(request: ChatbotRequest) -> ChatbotResponse:
    """Handle a chatbot request while preserving financial data boundaries."""

    # 0. Validate input and bounded conversation history before any provider call.
    history = [item.model_dump() for item in request.history]

    if not get_history_guardrail(history):
        return ChatbotResponse(
            reply=INVALID_INPUT_REPLY,
            conversation_id=request.conversation_id,
            intent="invalid_history",
            tokens_used=0,
            source="policy_guard",
        )

    if history_has_prompt_injection(history):
        logger.warning("Conversation history blocked by prompt-injection guardrail")
        return ChatbotResponse(
            reply=INJECTION_REPLY,
            conversation_id=request.conversation_id,
            intent="prompt_injection",
            tokens_used=0,
            source="policy_guard",
        )

    guardrail = get_input_guardrail(request.message)
    refusal_messages = {
        "invalid_input": INVALID_INPUT_REPLY,
        "prompt_injection": INJECTION_REPLY,
        "unsafe_request": UNSAFE_REPLY,
        "out_of_scope": OUT_OF_SCOPE_REPLY,
    }
    if guardrail:
        logger.warning("Input blocked by guardrail: %s", guardrail)
        return ChatbotResponse(
            reply=refusal_messages[guardrail],
            conversation_id=request.conversation_id,
            intent=guardrail,
            tokens_used=0,
            source="policy_guard",
        )

    # 1. Refuse requests for another person's financial data.
    if _mentions_third_party(request.message):
        return ChatbotResponse(
            reply=THIRD_PARTY_REFUSAL_MESSAGE,
            conversation_id=request.conversation_id,
            intent="declined_third_party",
            tokens_used=0,
            source="policy_guard",
        )

    # 2. Account-level intervention requires an authorized human review.
    # No verified support channel or ticket handoff is configured here.
    if ACCOUNT_SUPPORT_PATTERN.search(request.message):
        return ChatbotResponse(
            reply=(
                "This account issue needs an authorized HisabDo support "
                "review. I can't access or change account settings, submit "
                "a support ticket, or connect you to a human agent from "
                "this chat. A verified support contact or handoff is not "
                "configured here, so please ask the HisabDo product owner "
                "for the approved support route. Never share your password, "
                "PIN, or OTP in this chat."
            ),
            conversation_id=request.conversation_id,
            intent="account_support",
            tokens_used=0,
            source="support_handoff_unavailable",
        )

    # 3. Handle greetings without retrieval or LLM calls.
    small_talk = _classify_small_talk(request.message)

    if small_talk:
        return ChatbotResponse(
            reply=SMALL_TALK_REPLIES[small_talk],
            conversation_id=request.conversation_id,
            intent="general",
            tokens_used=0,
            source="greeting_fastpath",
        )

    # 3. Explicit PDF report requests get transparent product guidance.
    # This does not create or attach an actual PDF file.
    if _is_pdf_request(request.message):
        return ChatbotResponse(
            reply=PDF_GUIDANCE_REPLY,
            conversation_id=request.conversation_id,
            intent="pdf_report",
            tokens_used=0,
            source="verified_product_guidance",
        )

    provider = get_llm_provider()

    # 4. Recognize expense/income requests and continue pending follow-ups.
    transaction_response = _handle_transaction_intent(
        request.message,
        history,
        request.conversation_id,
    )

    if transaction_response:
        return transaction_response

    # Confirm intent before treating a first-person expense statement as a transaction.
    if _ambiguous_expense_statement(request.message):
        return _expense_clarification_response(request.conversation_id)

    # 5. Personal financial figures must come from the backend API.
    if _is_own_financial_data_query(request.message):
        try:
            summary = get_backend_client().get_user_financial_summary(
                request.user_id
            )
        except ServiceError:
            raise
        except Exception:
            logger.error("Financial backend is unavailable; details withheld from logs.")

            return ChatbotResponse(
                reply=(
                    "I can't access your financial data right now "
                    "because the financial service is unavailable. "
                    "Please try again later."
                ),
                conversation_id=request.conversation_id,
                intent="own_financial_data",
                tokens_used=0,
                source="backend_unavailable",
            )

        context = wrap_untrusted_context(_format_financial_summary(summary))
        reply, tokens = provider.generate_reply(
            request.message,
            context=context,
            history=history,
        )
        reply = _guard_generated_reply(reply)

        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="own_financial_data",
            tokens_used=tokens,
            source="backend_financial_api",
        )

    # 6. Retrieve FAQ and product documentation.
    # Short product follow-ups may reuse the latest relevant user question.
    # Previous assistant responses are never used to construct retrieval evidence.
    faq_query = _build_faq_retrieval_query(
        request.message,
        history,
    )

    try:
        matches = get_retriever().retrieve(
            faq_query,
            top_k=3,
        )
    except Exception:
        logger.error("FAQ semantic retrieval failed; details withheld from logs.")

        # Product-specific questions must not receive unsupported LLM answers.
        if _is_product_specific_query(faq_query):
            return ChatbotResponse(
                reply=FAQ_RETRIEVAL_ERROR_REPLY,
                conversation_id=request.conversation_id,
                intent="product_faq",
                tokens_used=0,
                source="rag_error",
            )

        # General questions can safely continue through the general LLM flow.
        return _general_response(request, provider, history)

    # 7. No retrieved matches: avoid guessing about product-specific features.
    if not matches:
        if _is_product_specific_query(faq_query):
            return _no_verified_faq_response(request)

        return _general_response(request, provider, history)

    # Surface conflicts only when verified entries explicitly share a conflict key.
    conflict = _find_verified_source_conflicts(matches)
    if conflict:
        conflict_key, conflict_entries = conflict
        conflict_values = sorted({
            entry["conflict_value"].strip()
            for entry in conflict_entries
        })
        source_titles = sorted({
            str(entry.get("title") or entry.get("source") or "Untitled source")
            for entry in conflict_entries
        })
        conflict_ids = {
            entry.get("id")
            for entry in conflict_entries
            if entry.get("id")
        }
        reply = (
            f"The verified sources contain conflicting entries for "
            f"'{conflict_key}'. Recorded values: "
            f"{'; '.join(conflict_values)}. Sources: "
            f"{'; '.join(source_titles)}. I can't determine which value "
            f"is current. This chat has no verified support contact or "
            f"ticket handoff, so I can't submit a request. Please ask the "
            f"HisabDo product owner for the approved support route."
        )
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="product_faq",
            tokens_used=0,
            source="rag_conflict",
            citations=_build_verified_citations(matches, conflict_ids),
        )

    # 8. Normalize retrieved documents and build source-labelled context.
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
                "id": match.get("id"),
                "title": title,
                "source": match.get("source") or title,
                "score": match.get("score"),
                "source_url": match.get("source_url") or match.get("url"),
                "section": match.get("section"),
                "verified": match.get("verified") is True,
            }
        )

    prepared_context = prepare_context(context_chunks)
    context = wrap_untrusted_context(format_context_block(prepared_context))

    # 9. Invalid or empty retrieved content must not trigger invented instructions.
    if not context:
        if _is_product_specific_query(faq_query):
            return _no_verified_faq_response(request)

        return _general_response(request, provider, history)

    # 10. Generate an answer using retrieved context.
    # Keep the actual current user message unchanged for the answer generation.
    reply, tokens = provider.generate_reply(
        request.message,
        context=context,
        history=history,
    )
    reply = _guard_generated_reply(reply)

    # Remove inline citation labels that do not exactly match verified context.
    allowed_document_ids = {
        chunk.document_id
        for chunk in prepared_context
        if chunk.verified is True and chunk.document_id
    }
    reply = _filter_inline_citations(
        reply,
        matches,
        allowed_document_ids,
    )

    # 11. Return only citations backed by retrieved source metadata.
    allowed_document_ids = {
        chunk.document_id
        for chunk in prepared_context
        if chunk.verified is True and chunk.document_id
    }
    citations = _build_verified_citations(matches, allowed_document_ids)

    return ChatbotResponse(
        reply=reply,
        conversation_id=request.conversation_id,
        intent="product_faq",
        tokens_used=tokens,
        source="rag",
        citations=citations,
    )


def handle_chat(request: ChatbotRequest) -> ChatbotResponse:
    """Monitor the complete Department 3 request without logging user data."""

    started_at = start_timer()
    monitoring_counters.increment("requests")

    try:
        response = _handle_chat_impl(request)

        if response.source in {
            "rag_error",
            "rag_no_match",
            "rag_conflict",
            "backend_unavailable",
        }:
            outcome = "fallback"
            monitoring_counters.increment("fallback")
        elif response.source == "policy_guard":
            outcome = "blocked"
            monitoring_counters.increment("blocked")
        else:
            outcome = "success"
            monitoring_counters.increment("success")

        safe_log_event(
            "chat_request",
            component="chat",
            outcome=outcome,
            latency_ms=elapsed_ms(started_at),
        )
        return response

    except ServiceError:
        monitoring_counters.increment("errors")
        monitoring_counters.increment("backend_failures")
        safe_log_event(
            "chat_request",
            component="backend",
            outcome="error",
            latency_ms=elapsed_ms(started_at),
            error_category="backend",
        )
        raise

    except Exception:
        monitoring_counters.increment("errors")
        safe_log_event(
            "chat_request",
            component="chat",
            outcome="error",
            latency_ms=elapsed_ms(started_at),
            error_category="unknown",
        )
        logger.error("Department 3 request failed; details withheld from logs.")
        raise
