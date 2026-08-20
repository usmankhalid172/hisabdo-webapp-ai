"""Core NLP / LLM request-processing logic for the AI Financial Assistant.

Day 16 deliverable: this module exposes the *request-processing* stage of the
chatbot flow as a clean, modular pipeline that can later be swapped for an
LLM-based NLU classifier. It currently uses deterministic NLU (normalise ->
intent detection -> entity extraction -> period resolution) but returns the
same structured ``ParsedRequest`` object an LLM NLU layer would produce, so
``engine.py`` does not care which backend produced it.

Processing steps
----------------
1. ``extract_entities``   - period, category, personal-account flag, money flag
                            from the question.
2. ``resolve_period``     - turn a detected month name/number/relative phrase
                            into a concrete ``YYYY-MM`` against a reference date.
3. ``process_question``   - normalise -> intent -> entities -> resolved period.

The classifier stays the rule-based intent detector until an LLM NLU backend
is added (see ``research/rag-approach.md``). This mirrors the team guidance:
keep the initial implementation simple and evaluate before adding advanced
techniques.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from . import intents as intent_mod
from .intents import IntentResult, _MONTH_NAME_TO_NUM, _normalise

# Words that usually indicate the user is talking about their own finances.
_PERSONAL_PRONOUNS = ("i", "me", "my", "mine", "we", "our")


@dataclass
class ParsedRequest:
    """Structured output of the NLP request-processing step."""
    question: str
    normalised: str
    intent: str
    confidence: float
    period: Optional[str] = None
    category: Optional[str] = None
    entities: dict = field(default_factory=dict)
    matched: list = field(default_factory=list)


def extract_entities(normalised: str, detected: IntentResult) -> dict:
    """Extract structured entities from a normalised question.

    Returns a dict with ``period``, ``category``, ``personal`` and
    ``has_money`` keys. This is the reference input that later entity
    extraction (regex-based or LLM-based) should reproduce.
    """
    tokens = normalised.split()
    return {
        "period": detected.period,
        "category": detected.category,
        "personal": any(p in tokens for p in _PERSONAL_PRONOUNS),
        "has_money": any(c in normalised for c in ("$", "rs", "rupees", "pk")),
    }


def resolve_period(raw_period: Optional[str], reference_date: dt.date) -> Optional[str]:
    """Resolve a detected period string to a concrete ``YYYY-MM``.

    Accepts an explicit ``YYYY-MM`` / ``YYYY-MM-DD`` value, a bare month
    number (e.g. ``07``), or a month name (e.g. ``july``), resolved against
    ``reference_date.year``.
    """
    if not raw_period:
        return None
    raw = str(raw_period).strip()
    # A bare month number (e.g. "07") -> YYYY-MM against the reference year.
    if raw.isdigit() and 1 <= int(raw) <= 12:
        return f"{reference_date.year}-{int(raw):02d}"
    if len(raw) >= 7 and raw[:4].isdigit() and raw[4] == "-" \
            and raw[5:7].isdigit():
        return raw[:7]
    # A bare month name -> resolve against the reference year.
    for name, num in _MONTH_NAME_TO_NUM.items():
        if name in raw.lower():
            return f"{reference_date.year}-{num}"
    return None


def _has_relative_period(normalised: str) -> bool:
    return ("this month" in normalised or "last month" in normalised
            or "monthly" in normalised)


def resolve_relative_period(normalised: str, reference_date: dt.date) -> str:
    """Resolve ``this month`` / ``last month`` against a reference date."""
    if "last month" in normalised:
        year, month = reference_date.year, reference_date.month
        if month == 1:
            year, month = year - 1, 12
        else:
            month -= 1
        return dt.date(year, month, 1).strftime("%Y-%m")
    # this month / monthly
    return reference_date.strftime("%Y-%m")


def build_parsed_request(question: str, detected: IntentResult,
                         reference_date: dt.date) -> ParsedRequest:
    """Turn a raw question + detected intent into a structured request."""
    normalised = _normalise(question)
    entities = extract_entities(normalised, detected)
    raw_period = entities["period"] or detected.period
    period = resolve_period(raw_period, reference_date)
    if period is None:
        # A bare month name in the question (e.g. "in July") is resolved to the
        # reference year, mirroring the engine's "_has_period_phrase" fallback.
        for name, num in _MONTH_NAME_TO_NUM.items():
            if name in normalised:
                period = f"{reference_date.year}-{num}"
                break
    if period is None and _has_relative_period(normalised):
        period = resolve_relative_period(normalised, reference_date)
    return ParsedRequest(
        question=question,
        normalised=normalised,
        intent=detected.intent,
        confidence=round(detected.confidence, 2),
        period=period,
        category=detected.category,
        entities=entities,
        matched=list(detected.matched),
    )


def process_question(question: str, reference_date: dt.date) -> ParsedRequest:
    """Run the full request-processing step for a user question."""
    detected = intent_mod.detect_intent(question)
    return build_parsed_request(question, detected, reference_date)
