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
import threading
import time
from contextvars import ContextVar
from functools import lru_cache

from ..config import get_settings
from ..integration.backend_client import get_backend_client
from ..schemas import ChatbotRequest, ChatbotResponse, Citation, DialogueInfo, TransactionActionOut
from .dialogue import ConversationState, DialogueManager, DialogueOutcome, Route
from .dialogue.account_data import BackendClientAccountData
from .dialogue.manager import karachi_today
from .dialogue.state_store import get_state_store
from .llm_providers import get_llm_provider
from .faq_rag import get_retriever
from .grounding import GroundedAnswerer, KbRetriever
from . import guardrails, telemetry
from .grounding.answer import pre_clarify
from . import conversation
from .grounding.retrieval import KB_PATH, validate_kb

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
    r"\b(user|account|customer|client)\s*#?\s*\d+\b"
    # Day 7 fix: "user-A's balance", "user_7 ka balance", "user B's" (letter or hyphenated ids)
    r"|\buser[\s_-]?[a-z0-9]{1,12}('s|\s+(ka|ki|ke))\b", re.IGNORECASE
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


# Release fix: the guard above only knew English. "Mere bhai ka balance batao" / "میرے بھائی کا بیلنس"
# reached the private route and were answered with the user's own figures. Relationship words only,
# never names: "Ali ka udhar" is the user's own customer ledger and must keep working.
THIRD_PARTY_RELATIONSHIP_URDU = re.compile(
    r"\b(bhai|bhaai|behen|bahen|bahan|biwi|begum|shohar|khawind|dost|abbu|abba|ammi|amma|walid|walida|"
    r"beta|beti|chacha|chachi|mamu|mamoo|khala|phuppo|sasur|saas|padosi|saathi|sathi)\s+(ka|ki|ke)\b"
    r"|(بھائی|بہن|بیوی|بیگم|شوہر|خاوند|دوست|ابو|ابا|امی|اماں|والد|والدہ|بیٹا|بیٹی|چچا|ماموں|خالہ|پھوپھو|سسر|ساس|پڑوسی)"
    r"\s*(کا|کی|کے)"
)


def _mentions_third_party(message: str) -> bool:
    text = message.lower()
    if THIRD_PARTY_RELATIONSHIP_WORDS.search(text):
        return True
    if THIRD_PARTY_RELATIONSHIP_URDU.search(text):
        return True
    if THIRD_PARTY_ID_REFERENCE.search(text):
        return True
    if _mentions_bare_name_possessive(message):
        return True
    return False


# "How do I export my expenses to Excel?" asks about the app, not for the user's figures (D3-10).
PRODUCT_HOW_TO = re.compile(r"\b(how (do|can|to)|can i|export|excel|pdf|sync\w*|backup|uninstall|attach|"
                            r"categor\w*|accountant|cloud|tax|zakat)\b")


def _is_own_financial_data_query(message: str) -> bool:
    text = message.lower()
    if _mentions_third_party(message) or (PRODUCT_HOW_TO.search(text) and get_settings().grounded_answers_enabled):
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


_ANSWERER: GroundedAnswerer | None = None
_ANSWERER_FAILED_AT = 0.0
_ANSWERER_LOCK = threading.Lock()
KB_RETRY_SECONDS = 60


def get_grounded_answerer() -> GroundedAnswerer | None:
    """Approved KB + the measured retrieval configuration, built once per process. If the index cannot be built the
    knowledge route answers with the kb_unavailable fallback and the build is retried after KB_RETRY_SECONDS."""
    global _ANSWERER, _ANSWERER_FAILED_AT
    if _ANSWERER is not None:
        return _ANSWERER
    with _ANSWERER_LOCK:
        if _ANSWERER is None and time.monotonic() - _ANSWERER_FAILED_AT >= KB_RETRY_SECONDS:
            try:
                _ANSWERER = GroundedAnswerer(KbRetriever(mode=get_settings().kb_retriever_mode))
                if _ANSWERER.retriever.degraded:
                    log.warning("kb_index_degraded", extra={"reasons": [_ANSWERER.retriever.degraded]})
            except Exception as exc:  # noqa: BLE001
                _ANSWERER_FAILED_AT = time.monotonic()
                log.error("kb_index_unavailable", extra={"error_type": type(exc).__name__})
                telemetry.METRICS.count("error:kb_unavailable")
    return _ANSWERER


def _reset_answerer() -> None:
    global _ANSWERER, _ANSWERER_FAILED_AT
    _ANSWERER, _ANSWERER_FAILED_AT = None, 0.0


get_grounded_answerer.cache_clear = _reset_answerer  # tests and settings changes rebuild it


def reload_kb(path=None) -> dict:
    """Swap in a new KB file only if it validates; otherwise keep serving the current index."""
    global _ANSWERER
    current = get_grounded_answerer()
    ok, reasons, chunks = validate_kb(path or KB_PATH, len(current.retriever.chunks) if current else None)
    if not ok:
        log.error("kb_update_rejected", extra={"reasons": reasons})
        telemetry.METRICS.count("error:kb_update_rejected")
        return {"updated": False, "reasons": reasons, "serving": kb_status()}
    try:
        new = GroundedAnswerer(KbRetriever(chunks=chunks, mode=get_settings().kb_retriever_mode), kb_chunks=chunks)
    except Exception as exc:  # noqa: BLE001
        log.error("kb_update_rejected", extra={"reasons": [f"build_failed:{type(exc).__name__}"]})
        telemetry.METRICS.count("error:kb_update_rejected")
        return {"updated": False, "reasons": [f"build_failed:{type(exc).__name__}"], "serving": kb_status()}
    with _ANSWERER_LOCK:
        _ANSWERER = new
    log.info("kb_updated", extra={"kb": kb_status()})
    return {"updated": True, "reasons": [], "serving": kb_status()}


def kb_status() -> dict:
    a = _ANSWERER
    if a is None:
        return {"loaded": False}
    r = a.retriever
    return {"loaded": True, "version": r.version, "chunks": len(r.chunks), "mode": r.mode, "degraded": r.degraded}


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


FALLBACK_REPLIES = {
    "internal_error": ("Sorry, something went wrong on my side and I couldn't finish that. Please try again; if it "
                       "keeps happening, contact hisabdo.app@gmail.com."),
    "backend_error": ("I can't load your figures right now, and I won't estimate them. Please try again in a few "
                      "minutes."),
    "llm_error": ("I can't answer that right now. Please try again shortly, or ask about a HisabDo feature, such as "
                  "PDF reports, backup or customer udhar."),
    "kb_unavailable": ("HisabDo's help library is temporarily unavailable, so I won't guess. Please try again later, "
                       "or contact hisabdo.app@gmail.com."),
}
_TURN: ContextVar[dict] = ContextVar("turn_info")
_ROUTE_BY_SOURCE = {"guardrail": "guard", "output_guard": "guard", "policy_guard": "guard",
                    "backend_financial_api": "account_data", "backend_unavailable": "account_data",
                    "dialogue": "transaction", "rag": "knowledge", "kb_fallback": "knowledge",
                    "clarification": "knowledge", "kb_unavailable": "knowledge", "llm_general": "general",
                    "llm_unavailable": "general", "greeting_fastpath": "general", "service_fallback": "error",
                    "escalation": "support"}


def _note(**kv) -> None:
    info = _TURN.get(None)
    if info is not None:
        info.update(kv)


class _LLMUnavailable(Exception):
    pass


def _generate(provider, message: str, context, history):
    """Every model call goes through here: counted, and a provider failure becomes a typed, safe error."""
    _note(llm_called=True)
    try:
        return provider.generate_reply(message, context=context, history=history)
    except Exception as exc:  # noqa: BLE001
        category = "llm_timeout" if "timeout" in f"{type(exc).__name__} {getattr(exc, 'error_code', '')}".lower() \
            else "llm_error"
        log.error("llm_call_failed", extra={"error_type": type(exc).__name__})
        _note(error_category=category, fallback="llm_error")
        raise _LLMUnavailable(category) from exc


def handle_chat(request: ChatbotRequest) -> ChatbotResponse:
    """Telemetry around the whole turn; any unexpected failure becomes a safe reply, never a stack trace."""
    t0 = time.perf_counter()
    info = {"llm_called": False, "fallback": "none", "error_category": "none", "retrieval_mode": "none"}
    token = _TURN.set(info)
    try:
        try:
            response = _guarded_chat(request)
        except Exception as exc:  # noqa: BLE001
            log.error("chat_failed", extra={"error_type": type(exc).__name__})
            info.update(error_category="internal_error", fallback="internal_error")
            response = ChatbotResponse(reply=FALLBACK_REPLIES["internal_error"], conversation_id=request.conversation_id,
                                       intent="service_fallback", tokens_used=0, source="service_fallback")
        telemetry.record_turn(
            request_id=telemetry.REQUEST_ID.get(), user_ref=telemetry.user_ref(request.user_id),
            route=_ROUTE_BY_SOURCE.get(response.source, "other"), intent=response.intent, source=response.source,
            answer_status=response.answer_status, language=info.get("language"),
            retrieval_mode=info["retrieval_mode"], retrieved_ids=info.get("retrieved_ids"),
            cited_ids=[c.chunk_id for c in response.citations] or None, retrieval_ms=info.get("retrieval_ms"),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1), llm_called=info["llm_called"],
            llm_provider=get_settings().llm_provider if info["llm_called"] else None,
            tokens_used=response.tokens_used, needs_review=response.needs_review or None,
            fallback=info["fallback"], error_category=info["error_category"], kb_version=info.get("kb_version"),
            output_findings=info.get("output_findings"))
        return response
    finally:
        _TURN.reset(token)


_REPEAT_KIND = {"kb_fallback": "fallback", "guardrail": "boundary", "escalation": "escalation"}


def _guarded_chat(request: ChatbotRequest) -> ChatbotResponse:
    """Conversation UX rules (U4-U6, docs/dept3-conversation-ux-rulebook.md) around the guarded flow."""
    last = next((h.content for h in reversed(request.history) if h.role == "assistant"), None)
    if (mapped := conversation.follow_up(request.message, last)) is not None:   # U6
        request = request.model_copy(update={"message": mapped})
    response = _guarded_core(request)
    kind = _REPEAT_KIND.get(response.source or "")
    if kind and not response.citations and request.history:   # U5: never the same paragraph twice
        if kind == "fallback" and response.answer_status == "out_of_scope":
            kind = "boundary"
        earlier = [h.content for h in request.history if h.role == "assistant"]
        response.reply = conversation.dedupe(response.reply, kind, earlier, request.message)
    return response


def _guarded_core(request: ChatbotRequest) -> ChatbotResponse:
    """Guardrails wrap the whole flow: input checks first, output checks on every reply."""
    if get_settings().guardrails_enabled:
        verdict = guardrails.check_input(request.message)
        if verdict is None and (esc := conversation.escalation(request.message)) is not None:
            # U4: account-level problems go to human support, never to demo figures or an entry flow
            log.info("support_escalation")   # no user text
            return ChatbotResponse(reply=esc, conversation_id=request.conversation_id, intent="escalate_support",
                                   tokens_used=0, source="escalation")
        if verdict is None and get_settings().grounded_answers_enabled and not request.history \
                and not _classify_small_talk(request.message) and (q := pre_clarify(request.message)) is not None:
            # Rulebook R1 / R10: a topic-less or expense-only message gets one clarifying question, not a refusal
            _note(language=q[1])
            return ChatbotResponse(reply=q[0], conversation_id=request.conversation_id, intent="clarify",
                                   tokens_used=0, source="clarification", answer_status="clarify")
        if verdict is None and not _classify_small_talk(request.message):
            verdict = guardrails.check_off_topic_question(request.message, _recent_history(request))
        if verdict is not None:
            return ChatbotResponse(reply=verdict.reply, conversation_id=request.conversation_id,
                                   intent=f"blocked_{verdict.category}", tokens_used=0, source="guardrail")
    response = _handle_chat(request)
    if get_settings().guardrails_enabled:
        safe, findings = guardrails.check_output(response.reply)
        if safe != response.reply:
            response.reply = safe
            _note(output_findings=findings)
            if "secret" in findings or "prompt_text" in findings:
                response.source, response.intent, response.citations = "output_guard", "blocked_output", []
    return response


def _recent_history(request: ChatbotRequest, turns: int = 4) -> str:
    return " ".join(h.content for h in request.history[-turns:])


def _handle_chat(request: ChatbotRequest) -> ChatbotResponse:
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
        response = _single_turn(request, route=outcome.route if outcome is not None else None)
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


def _single_turn(request: ChatbotRequest, route: Route | None = None) -> ChatbotResponse:
    """The original single-message flow; with grounded answers on, the knowledge step follows
    docs/grounded-answer-rules.md (route = the intent router's decision, None when it did not run)."""
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

    provider = get_llm_provider()

    if _is_own_financial_data_query(request.message):
        # Authoritative data path — never touches the RAG knowledge base.
        try:
            summary = get_backend_client().get_user_financial_summary(request.user_id)
        except Exception as exc:  # noqa: BLE001 - never estimate figures when the backend is down
            log.error("backend_call_failed", extra={"error_type": type(exc).__name__})
            _note(error_category="backend_error", fallback="backend_error")
            return ChatbotResponse(reply=FALLBACK_REPLIES["backend_error"], conversation_id=request.conversation_id,
                                   intent="own_financial_data", tokens_used=0, source="backend_unavailable")
        context = _format_financial_summary(summary)
        try:
            reply, tokens = _generate(provider, request.message, context, [h.model_dump() for h in request.history])
        except _LLMUnavailable:
            reply, tokens = context, 0   # the backend's exact figures, unworded: still correct, no model needed
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="own_financial_data",
            tokens_used=tokens,
            source="backend_financial_api",
        )

    if get_settings().grounded_answers_enabled:
        return _grounded_reply(request, provider, kb_allowed=route in (None, Route.KNOWLEDGE))

    matches = get_retriever().retrieve(request.message, top_k=1)
    if matches:
        context = matches[0]["text"]
        _note(retrieval_mode="tfidf_legacy", retrieved_ids=[matches[0].get("id")])
        try:
            reply, tokens = _generate(provider, request.message, context, [h.model_dump() for h in request.history])
        except _LLMUnavailable:
            reply, tokens = context, 0   # the retrieved text itself
        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent="product_faq",
            tokens_used=tokens,
            source="rag",
        )

    if get_settings().guardrails_enabled and (off := guardrails.check_domain(request.message, _recent_history(request))) is not None:
        return ChatbotResponse(reply=off.reply, conversation_id=request.conversation_id, intent="blocked_off_topic",
                               tokens_used=0, source="guardrail")
    try:
        reply, tokens = _generate(provider, request.message, None, [h.model_dump() for h in request.history])
    except _LLMUnavailable:
        return ChatbotResponse(reply=FALLBACK_REPLIES["llm_error"], conversation_id=request.conversation_id,
                               intent="general", tokens_used=0, source="llm_unavailable")
    return ChatbotResponse(
        reply=reply,
        conversation_id=request.conversation_id,
        intent="general",
        tokens_used=tokens,
        source="llm_general",
    )


_GROUNDED_SOURCE = {"answered": "rag", "conflict": "rag", "clarify": "clarification",
                    "no_source": "kb_fallback", "out_of_scope": "kb_fallback"}


def _grounded_reply(request: ChatbotRequest, provider, kb_allowed: bool) -> ChatbotResponse:
    answerer = get_grounded_answerer()
    if answerer is None:
        _note(error_category="kb_unavailable", fallback="kb_unavailable")
        return ChatbotResponse(reply=FALLBACK_REPLIES["kb_unavailable"], conversation_id=request.conversation_id,
                               intent="product_faq", tokens_used=0, source="kb_unavailable",
                               answer_status="no_source")
    ans = answerer.answer(request.message, provider=provider,
                          history=[h.model_dump() for h in request.history], kb_allowed=kb_allowed)
    _note(retrieval_mode=answerer.retriever.mode if kb_allowed else "none", retrieved_ids=ans.retrieved_ids or None,
          retrieval_ms=ans.retrieval_ms, language=ans.language, kb_version=answerer.retriever.version,
          llm_called=_TURN.get({}).get("llm_called") or (provider is not None and ans.status == "answered"
                                                         and ans.language == "en"
                                                         and type(provider).__name__ != "MockLLMProvider"))
    if ans.error:
        _note(error_category=ans.error, fallback="llm_error")
    if ans.status in ("no_source", "out_of_scope"):
        _note(fallback="no_source" if ans.status == "no_source" else "none")
    if ans.needs_review:
        log.warning("kb_conflict_escalated", extra={"chunks": [c.chunk_id for c in ans.citations]})
    return ChatbotResponse(
        reply=ans.reply,
        conversation_id=request.conversation_id,
        intent="product_faq" if ans.status in ("answered", "conflict") else ans.status,
        tokens_used=0,
        source=_GROUNDED_SOURCE[ans.status],
        answer_status=ans.status,
        citations=[Citation(n=c.n, title=c.label, url=c.url, chunk_id=c.chunk_id, last_updated=c.last_updated)
                   for c in ans.citations],
        needs_review=ans.needs_review,
    )
