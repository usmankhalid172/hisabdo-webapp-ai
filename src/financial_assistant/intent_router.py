
"""Intent recognition and multi-turn conversation state for HisabDo."""

from dataclasses import dataclass, field
import re
from typing import Any


@dataclass
class IntentResult:
    intent: str
    slots: dict[str, Any] = field(default_factory=dict)
    missing_slots: list[str] = field(default_factory=list)
    follow_up: str | None = None
    ready: bool = False


@dataclass
class ConversationState:
    """State explicitly scoped to one user and conversation."""

    user_id: str
    conversation_id: str
    pending_intent: str | None = None
    slots: dict[str, Any] = field(default_factory=dict)
    missing_slots: list[str] = field(default_factory=list)


def _extract_amount(text: str) -> float | None:
    match = re.search(
        r"(?<!\w)(?:rs\.?|pkr|rupees?)?\s*"
        r"(\d[\d,]*(?:\.\d{1,2})?)\s*(?:pkr|rupees?)?(?!\w)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    try:
        amount = float(match.group(1).replace(",", ""))
    except ValueError:
        return None
    return amount if amount > 0 else None


def _extract_period(text: str) -> str | None:
    text = text.lower()
    for period in (
        "today", "yesterday", "this week", "this month",
        "last month", "this year",
    ):
        if period in text:
            return period
    return None


def classify_intent(message: str) -> IntentResult:
    """Classify common financial actions with deterministic rules."""
    text = message.strip().lower()

    if not text:
        return IntentResult("general", ready=True)

    if re.search(
        r"\b(his|her|their|someone else's|another user's|"
        r"friend's|colleague's|wife's|husband's)\b",
        text,
    ) and re.search(
        r"\b(balance|expenses?|income|transactions?|financial report)\b",
        text,
    ):
        return IntentResult("account_query", ready=True)

    if re.search(
        r"\b(correct|change|update|edit|fix)\b.*"
        r"\b(expense|income|transaction|amount|category)\b"
        r"|\b(change|correct|update)\s+(that|it)\b",
        text,
    ):
        intent = "correction"
    elif re.search(
        r"\b(report|statement|summary|analytics|breakdown)\b", text
    ):
        intent = "report"
    elif re.search(
        r"\b(categorize|categorise|category|categorization|"
        r"categorisation|classify)\b", text
    ):
        intent = "categorization"
    elif re.search(
        r"\b(income|earned|earn|salary received|received payment|"
        r"money received|record income)\b", text
    ):
        intent = "income"
    elif re.search(
        r"\b(add|record|log|track|save|spent|spend|paid|"
        r"expense|bought|purchase)\b", text
    ):
        intent = "expense"
    elif re.search(
        r"\b(my balance|my expenses?|my income|my revenue|"
        r"how much did i spend|my outstanding)\b", text
    ):
        intent = "account_query"
    elif re.search(
        r"\b(how does|how do i|what is|what are|"
        r"does hisabdo|help me understand)\b", text
    ):
        intent = "faq"
    else:
        return IntentResult("general", ready=True)

    slots: dict[str, Any] = {}

    amount = _extract_amount(text)
    if amount is not None:
        slots["amount"] = amount

    period = _extract_period(text)
    if period:
        slots["period"] = period

    match = re.search(
        r"\b(?:for|on|at)\s+(.+?)(?:\s+\b(?:for|on)\s+"
        r"(?:today|yesterday|this month|this week)\b)?$",
        text,
    )
    if match:
        description = match.group(1).strip(" .,!?")
        if description and _extract_amount(description) is None:
            slots["description"] = description

    required_slots = {
        "expense": ["amount", "description"],
        "income": ["amount", "description"],
        "categorization": ["description"],
        "correction": ["description"],
        "report": [],
    }.get(intent, [])

    missing = [slot for slot in required_slots if slot not in slots]

    questions = {
        "amount": "What was the amount?",
        "description": "Please describe the transaction.",
        "category": "Which category should I use?",
        "period": "Which period should the report cover?",
    }

    return IntentResult(
        intent=intent,
        slots=slots,
        missing_slots=missing,
        follow_up=questions[missing[0]] if missing else None,
        ready=not missing,
    )


def handle_turn(message: str, state: ConversationState) -> IntentResult:
    """Fill missing slots over multiple turns."""
    if state.pending_intent is None:
        result = classify_intent(message)

        if result.missing_slots:
            state.pending_intent = result.intent
            state.slots = dict(result.slots)
            state.missing_slots = list(result.missing_slots)

        return result

    updated = dict(state.slots)
    amount = _extract_amount(message)

    if amount is not None and "amount" in state.missing_slots:
        updated["amount"] = amount
    elif "description" in state.missing_slots and message.strip():
        updated["description"] = message.strip()
    elif "category" in state.missing_slots and message.strip():
        updated["category"] = message.strip()
    elif "period" in state.missing_slots and message.strip():
        updated["period"] = message.strip()

    state.slots = updated
    state.missing_slots = [
        slot for slot in state.missing_slots if slot not in updated
    ]

    if state.missing_slots:
        questions = {
            "amount": "What was the amount?",
            "description": "Please describe the transaction.",
            "category": "Which category should I use?",
            "period": "Which period should the report cover?",
        }
        return IntentResult(
            intent=state.pending_intent,
            slots=dict(state.slots),
            missing_slots=list(state.missing_slots),
            follow_up=questions[state.missing_slots[0]],
            ready=False,
        )

    result = IntentResult(
        intent=state.pending_intent,
        slots=dict(state.slots),
        ready=True,
    )
    state.pending_intent = None
    state.slots = {}
    state.missing_slots = []
    return result
