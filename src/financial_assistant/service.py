"""
chatbot_service — builds prompt/context, calls the configured LLM, and
post-processes the reply, per Day 15 §6.1.

Critical boundary (Day 15 §6.1, restated in Day 16 continuity plan §2):
exact user financial figures never come from RAG. If the message is asking
about the user's own numbers, this routes to the (mocked) backend financial
API instead of the knowledge base.
"""
import logging
import re
from functools import lru_cache

from ..config import get_settings
from ..integration.backend_client import get_backend_client
from ..schemas import ChatbotRequest, ChatbotResponse, DialogueInfo, SourceRef, TransactionActionOut
from .dialogue import ConversationState, DialogueManager, DialogueOutcome, Route
from .dialogue.account_data import BackendClientAccountData
from .dialogue.manager import karachi_today
from .dialogue.state_store import get_state_store
from .llm_providers import get_llm_provider
from .faq_rag import get_retriever
from .privacy_guard import mentions_third_party

# Deliberately simple keyword intent check — good enough for a POC boundary
# demonstration; a production version would use a real intent classifier.
OWN_FINANCIAL_DATA_PATTERNS = [
    r"\bmy balance\b", r"\bmy expenses?\b", r"\bmy revenue\b",
    r"\bhow much (have i|did i) spen[dt]\b", r"\bmy outstanding\b",
    r"\bwhat('?s| is) my\b.*\b(balance|expense|revenue|outstanding)\b",
    r"\bhow much money (do|have) i\b", r"\bmy (total )?spending\b",
]

# Security guard: any message that appears to ask about someone ELSE's
# financial data is refused deterministically in handle_chat(), before the
# router, backend, RAG or LLM are reached. English, Roman Urdu and Urdu
# detection lives in privacy_guard.py (Day-7 evaluation fix).
def _mentions_third_party(message: str) -> bool:
    return mentions_third_party(message)


# "How do I export my expenses?" is a product question, not a request for figures
# (Day-7 evaluation: the bare "my expenses" pattern sent it to the backend).
_PRODUCT_HOW_TO = re.compile(r"\b(how (do|can|to)|export|download|categori[sz]e|categorization|sorted|kaise|feature|"
                             r"pdf|csv|report of|shared|unsure|not sure)\b", re.I)


def _is_own_financial_data_query(message: str) -> bool:
    text = message.lower()
    if _mentions_third_party(message):
        return False
    if _PRODUCT_HOW_TO.search(text) and not re.search(r"\bhow much\b", text):
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


log = logging.getLogger("hisabdo.ai.dialogue")


@lru_cache
def get_dialogue_manager() -> DialogueManager:
    """Intent router + multi-turn slot filling. Private figures come from the
    same BackendClient seam as the single-turn path below."""
    return DialogueManager(
        account_data=BackendClientAccountData(today=karachi_today),
        default_currency=_account_currency,
    )


def _account_currency(user_id: str) -> str | None:
    """The user's own account currency, so a new entry doesn't need to ask.
    If the backend can't tell us, the dialogue asks (it never assumes)."""
    try:
        return get_backend_client().get_user_financial_summary(user_id).get("currency")
    except Exception:  # noqa: BLE001
        return None


def _run_dialogue(request: ChatbotRequest) -> tuple[DialogueOutcome | None, ConversationState | None]:
    """Never blocks the chat: if the router fails, the single-turn flow answers as before
    and the saved state is left unchanged."""
    if not get_settings().dialogue_enabled:
        return None, None
    store = get_state_store()
    state = store.load(request.user_id, request.conversation_id)
    try:
        return get_dialogue_manager().handle(request.user_id, request.message, state), state
    except Exception as exc:  # noqa: BLE001
        log.error("dialogue_failed", extra={"error_type": type(exc).__name__})
        return None, None


def _dialogue_info(outcome: DialogueOutcome, state: ConversationState) -> DialogueInfo:
    return DialogueInfo(
        status=outcome.status.value, route=outcome.route.value, awaiting=state.awaiting,
        missing_slots=outcome.missing_slots, collected=state.slots.filled() if state.active_intent else {},
    )


def _intent_name(outcome: DialogueOutcome) -> str:
    # Keep the existing name for "my balance" style questions (backend contract / tests).
    return "own_financial_data" if outcome.intent.value == "account_query" else outcome.intent.value


def handle_chat(request: ChatbotRequest) -> ChatbotResponse:
    """
    1. third-party guard (deterministic refusal, unchanged)
    2. intent router: transaction flows (expense / income / correction / categorize)
       and private figures (balance / report) are answered here with fixed templates
    3. everything else (FAQ, small talk, general) goes through the single-turn flow
       below, with a reminder appended if an entry is still unfinished
    """
    if _mentions_third_party(request.message):
        return _single_turn(request)

    outcome, state = _run_dialogue(request)
    if outcome is not None and outcome.reply is not None:
        response = ChatbotResponse(
            reply=outcome.reply,
            conversation_id=request.conversation_id,
            intent=_intent_name(outcome),
            tokens_used=0,
            source="backend_financial_api" if outcome.route == Route.ACCOUNT_DATA else "dialogue",
            dialogue=_dialogue_info(outcome, state),
            action=TransactionActionOut(**outcome.action.model_dump(exclude={"created_at"})) if outcome.action else None,
        )
    else:
        response = _single_turn(request, product_question=outcome is not None and outcome.route == Route.KNOWLEDGE)
        if outcome is not None:
            if outcome.pending_reminder:
                response.reply = f"{response.reply}\n\n{outcome.pending_reminder}"
            response.dialogue = _dialogue_info(outcome, state)

    if outcome is not None:
        get_state_store().save(request.user_id, request.conversation_id, state)
        log.info("dialogue_turn", extra={   # names and statuses only - never amounts, categories or text
            "intent": outcome.intent.value, "route": outcome.route.value, "status": outcome.status.value,
            "missing_slots": outcome.missing_slots, "action_type": outcome.action.type if outcome.action else None,
        })
    return response


_NO_ANSWER_EN = ("I don't have verified HisabDo information about that yet, so I won't guess. "
                 "Please check the app or contact the HisabDo team.")
_NO_ANSWER_RU = ("Is baare mein mere paas HisabDo ki verified maloomat nahi hai, is liye main andaza nahi lagaunga. "
                 "Meharbani karke app check karein ya HisabDo team se rabta karein.")


def _no_verified_answer(message: str) -> str:
    from .dialogue.extract import detect_language
    from .dialogue.models import Language
    return _NO_ANSWER_RU if detect_language(message) == Language.ROMAN_URDU else _NO_ANSWER_EN


def _single_turn(request: ChatbotRequest, product_question: bool = False) -> ChatbotResponse:
    """The original single-message flow (unchanged)."""
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


    if _is_own_financial_data_query(request.message):
        # Authoritative data path — never touches the RAG knowledge base.
        summary = get_backend_client().get_user_financial_summary(request.user_id)
        context = _format_financial_summary(summary)
        reply, tokens = get_llm_provider().generate_reply(request.message, context=context, history=[h.model_dump() for h in request.history])
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="own_financial_data",
            tokens_used=tokens,
            source="backend_financial_api",
        )

    matches = get_retriever().retrieve(request.message, top_k=1)
    if matches:
        best = matches[0]
        # The source label travels with the context so the model can cite it (prompts.py rule 11).
        context = f"[Source: {best['title']}]\n{best['text']}"
        reply, tokens = get_llm_provider().generate_reply(request.message, context=context, history=[h.model_dump() for h in request.history])
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="product_faq",
            tokens_used=tokens,
            source="rag",
            sources=[SourceRef(id=m["id"], title=m["title"], score=m["score"]) for m in matches],
        )

    if product_question:
        # A HisabDo product question with no verified source: say so instead of letting the
        # LLM fill the gap (Day-7 evaluation: unanswerable product questions got either an
        # unrelated document or an invented answer).
        return ChatbotResponse(
            reply=_no_verified_answer(request.message),
            conversation_id=request.conversation_id,
            intent="product_faq",
            tokens_used=0,
            source="kb_fallback",
        )

    reply, tokens = get_llm_provider().generate_reply(request.message, context=None, history=[h.model_dump() for h in request.history])
    return ChatbotResponse(
        reply=reply,
        conversation_id=request.conversation_id,
        intent="general",
        tokens_used=tokens,
        source="llm_general",
    )
