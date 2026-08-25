"""Financial intent detection for the AI Financial Assistant.

Classifies a user question into one of the supported financial intents.
Detection is deliberately rule-based (keyword/pattern matching on normalised
text) so the assistant works reliably without an API key or a trained model.

Supported intents (current implementation):
- MONTHLY_EXPENSE     : total spending in a month/period
- HIGHEST_CATEGORY    : the highest spending category
- SPENDING_SUMMARY    : breakdown / summary of spending
- SAVING_TIP          : retrieve saving advice from the knowledge base
- GREETING            : hello / hi
- HELP                : what the assistant can do
- THANKS              : acknowledgement
- AMBIGUOUS           : financial question missing a required detail
- UNSUPPORTED         : out-of-scope or non-financial question

Each required use case maps to an intent so we can verify what works.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# Category keywords -> canonical category names (shared Smart Expense taxonomy).
_CATEGORY_ALIASES = {
    "groceries": "Groceries",
    "grocery": "Groceries",
    "dining": "Food",
    "dining out": "Food",
    "restaurant": "Food",
    "eating out": "Food",
    "food": "Food",
    "transport": "Transport",
    "transportation": "Transport",
    "fuel": "Transport",
    "petrol": "Transport",
    "commute": "Transport",
    "entertainment": "Entertainment",
    "movies": "Entertainment",
    "utilities": "Utilities",
    "utility": "Utilities",
    "electric": "Utilities",
    "electricity": "Utilities",
    "water": "Utilities",
    "gas": "Utilities",
    "health": "Healthcare",
    "healthcare": "Healthcare",
    "pharmacy": "Healthcare",
    "medical": "Healthcare",
}

# Month names -> zero-padded month number.
_MONTH_NAME_TO_NUM = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
}

# Strong anchors for the highest-category use case.
_HIGHEST_ANCHORS = (
    "highest spending category", "top spending category", "most spent on",
    "biggest expense", "biggest spending", "most spending category",
    "category do i spend the most", "largest expense category",
    "spend the most on", "biggest category",
)

# Anchor phrases for the monthly/period expense use case.
_PERIOD_ANCHORS = (
    "how much did i spend", "total spending", "total spent", "total expenses",
    "spent this month", "spending this month", "spent last month",
    "spending last month", "monthly expense", "monthly spending",
    "how much do i spend", "expenses for", "total for", "spend in",
    "spent in", "spent during",
)

# Anchor words for the summary use case.
_SUMMARY_ANCHORS = (
    "summary", "breakdown", "overview of my spending", "where did my money go",
    "where does my money go", "spending by category", "spend by category",
    "list my spending", "how did i spend",
)

# Anchor words for the saving-tip use case.
_SAVING_ANCHORS = (
    "saving", "save money", "save more", "reduce spending", "cut my spending",
    "spend less", "save tips", "money saving", "budget better",
    "reduce expenses", "ways to save", "how to save",
)

# Anchor words for knowledge-base help topics (e.g. recurring expenses).
# Checked AFTER the financial-intent anchors so a query like
# "how much did I spend on subscriptions this month?" still routes to
# MONTHLY_EXPENSE; these only catch questions that would otherwise be
# ambiguous/unsupported but match a known knowledge-base topic.
_KNOWLEDGE_ANCHORS = (
    "recurring expense", "recurring cost", "recurring payment", "recurring",
    "subscription", "monthly bill", "fixed expenses",
)


@dataclass
class IntentResult:
    """Result of intent detection for a single user message."""
    intent: str
    confidence: float = 0.0
    # Optional detected period filter, e.g. "2026-07".
    period: Optional[str] = None
    # Optional detected category filter, e.g. "Groceries".
    category: Optional[str] = None
    # Matched signals, useful for debugging and evidence output.
    matched: list = field(default_factory=list)


def _normalise(text: str) -> str:
    """Lowercase, drop some punctuation, and collapse whitespace."""
    cleaned = " ".join(str(text).lower().split())
    cleaned = re.sub(r"[.,!?;:()]+", " ", cleaned)
    return " ".join(cleaned.split())


def _looks_like_greeting(norm: str) -> bool:
    """True for simple greeting phrases (handles bare ``hi``)."""
    greetings = ("hello", "hey", "hi", "good morning", "good afternoon",
                 "good evening", "salutations")
    for word in greetings:
        if word in norm:
            # For short words like "hi" only accept whole-word matches so
            # words like "this"/"whose" are not treated as greetings.
            if len(word) <= 3:
                tokens = norm.split()
                if word in tokens or any(t.startswith(word + "'") for t in tokens):
                    return True
            else:
                return True
    return False


def detect_month(text_norm: str) -> Optional[str]:
    """Return an ISO ``YYYY-MM`` for an explicit month, if found.

    Handles patterns like ``july 2026`` or ``in august``. If a bare month name
    is present without a year, it is not resolvable to a period here and the
    caller may substitute the reference year instead.
    """
    month = None
    for name, num in _MONTH_NAME_TO_NUM.items():
        if name in text_norm:
            month = num
            break
    if month is None:
        return None
    tokens = text_norm.split()
    year = None
    for token in tokens:
        clean = re.sub(r"\D", "", token)  # strip any trailing punctuation
        if clean.isdigit() and len(clean) == 4 \
                and 2000 <= int(clean) <= 2100:
            year = clean
            break
    if year is None:
        return None
    return f"{year}-{month}"


def _has_period_phrase(text_norm: str) -> bool:
    """True if the question references a specific period phrase."""
    for name in _MONTH_NAME_TO_NUM:
        if f" {name}" in text_norm or text_norm.startswith(name):
            return True
    return any(w in text_norm for w in (" this month", "last month",
                                        "this week", "last week"))


def detect_category(text_norm: str) -> Optional[str]:
    """Return the canonical category name if the question mentions one."""
    for alias, canonical in _CATEGORY_ALIASES.items():
        if alias in text_norm:
            return canonical
    return None


def detect_intent(question: str) -> IntentResult:
    """Classify ``question`` into an IntentResult.

    Priority: greeting/help/thanks, then the specific financial intents,
    then ambiguous, then unsupported.
    """
    norm = _normalise(question)
    if not norm:
        return IntentResult(intent="UNSUPPORTED", confidence=0.9, matched=["empty"])

    if _looks_like_greeting(norm):
        return IntentResult(intent="GREETING", confidence=0.95, matched=["greeting"])
    if "help" in norm:
        return IntentResult(intent="HELP", confidence=0.9, matched=["help"])
    if any(w in norm for w in ("thank", "thanks", "thx")):
        return IntentResult(intent="THANKS", confidence=0.9, matched=["thanks"])

    # --- SAVING_TIP ---
    if any(anchor in norm for anchor in _SAVING_ANCHORS):
        return IntentResult(intent="SAVING_TIP", confidence=0.9,
                            matched=["saving anchor"])

    # --- HIGHEST_CATEGORY ---
    if any(anchor in norm for anchor in _HIGHEST_ANCHORS):
        category = detect_category(norm)
        return IntentResult(intent="HIGHEST_CATEGORY", confidence=0.85,
                            category=category,
                            matched=["highest anchor", f"category={category}"])

    # --- SPENDING_SUMMARY ---
    if any(anchor in norm for anchor in _SUMMARY_ANCHORS):
        category = detect_category(norm)
        return IntentResult(intent="SPENDING_SUMMARY", confidence=0.8,
                            category=category,
                            matched=["summary anchor", f"category={category}"])

        # --- MONTHLY_EXPENSE ---
    if any(anchor in norm for anchor in _PERIOD_ANCHORS):
        period = detect_month(norm)
        category = detect_category(norm)  # optional "how much did I spend on X in July?"
        return IntentResult(intent="MONTHLY_EXPENSE", confidence=0.75,
                            period=period, category=category,
                            matched=["period anchor", f"period={period}",
                                     f"category={category}"])

    # --- Category-scoped query (e.g. "What did I spend on groceries?") ---
    category = detect_category(norm)
    spend_marker = any(w in norm for w in ("spend", "spent", "expense",
                                           "expenses", "cost", "costs"))
    if category and spend_marker and "summary" not in norm \
            and "breakdown" not in norm and not any(
                a in norm for a in _HIGHEST_ANCHORS):
        period = detect_month(norm)
        return IntentResult(intent="MONTHLY_EXPENSE", confidence=0.7,
                            period=period, category=category,
                            matched=["category scoped", f"category={category}",
                                     f"period={period}"])

    # --- Knowledge-base help topics (e.g. "How do I manage recurring
    #     expenses?") -> route to the RAG-backed SAVING_TIP flow so the
    #     assistant fetches relevant help-document sections instead of
    #     answering with a clarification or out-of-scope fallback.
    if any(anchor in norm for anchor in _KNOWLEDGE_ANCHORS):
        return IntentResult(intent="SAVING_TIP", confidence=0.7,
                            matched=["knowledge anchor"])

    # --- AMBIGUOUS ---
    financial_marker = any(
        w in norm for w in ("spend", "spent", "expense", "expenses", "cost",
                            "budget", "transaction", "category", "money",
                            "balance", "income")
    )
    if financial_marker:
        return IntentResult(intent="AMBIGUOUS", confidence=0.6,
                            matched=["financial marker without clear intent"])

    # --- Default unsupported / out-of-scope ---
    return IntentResult(intent="UNSUPPORTED", confidence=0.5, matched=["no match"])


# Intents that map to a currently supported use case (for the evidence matrix).
SUPPORTED_INTENTS = (
    "MONTHLY_EXPENSE",
    "HIGHEST_CATEGORY",
    "SPENDING_SUMMARY",
    "SAVING_TIP",
)