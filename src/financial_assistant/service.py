"""
chatbot_service — builds prompt/context, calls the configured LLM, and
post-processes the reply, per Day 15 §6.1.

Critical boundary (Day 15 §6.1, restated in Day 16 continuity plan §2):
exact user financial figures never come from RAG. If the message is asking
about the user's own numbers, this routes to the (mocked) backend financial
API instead of the knowledge base.
"""
import re

from .intent_router import ConversationState, handle_turn

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

    # Resume slot filling only when the latest assistant message
    # is one of our known follow-up questions.
    follow_up_prompts = {
        "What was the amount?",
        "Please describe the transaction.",
        "Which category should I use?",
        "Which period should the report cover?",
    }

    state = ConversationState(
        user_id=request.user_id,
        conversation_id=request.conversation_id,
    )

    if (
        request.history
        and request.history[-1].role == "assistant"
        and request.history[-1].content.strip() in follow_up_prompts
    ):
        for turn in request.history:
            if turn.role == "user":
                handle_turn(turn.content, state)

    intent_result = handle_turn(request.message, state)

    is_faq_style = bool(re.search(
        r"\\b(how does|how do i|what is|what are|does hisabdo|"
        r"help me understand)\\b",
        request.message,
        re.IGNORECASE,
    ))

    if (
        not request.message.strip().lower().startswith((
            "how does ", "how do i ", "what is ", "what are ",
            "does hisabdo ", "help me understand ",
        ))
        and intent_result.intent in {
            "expense", "income", "categorization", "correction", "report"
        }
    ):
        if not intent_result.ready:
            reply = intent_result.follow_up or "Please provide more details."
        else:
            reply = (
                f"I identified your {intent_result.intent} request and "
                f"collected these details: {intent_result.slots}. "
                "This intent-routing step has not saved or changed any "
                "financial records."
            )

        return ChatbotResponse(
            reply=reply,
            conversation_id=request.conversation_id,
            intent=intent_result.intent,
            tokens_used=0,
            source="intent_router",
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
