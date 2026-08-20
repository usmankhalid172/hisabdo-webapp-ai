"""Assistant engine: end-to-end chatbot flow.

Flow per request:
1. INTENT DETECTION  : classify the question (rule-based).
2. FACTS             : compute deterministic financial facts in the backend.
3. RETRIEVAL (RAG)   : retrieve knowledge-base chunks for SAVING_TIP (and as
   optional grounding context for other intents when available).
4. RESPONSE          : build a grounded response from the facts/context.
5. VALIDATION        : validate the response (no empty / ungrounded numbers).
6. Optional LLM pass : if configured, polish through the LLM using the same
                       grounded facts/context; on any failure, keep the
                       deterministic answer.

The whole pipeline runs offline when no API key is present, so the required
use cases are verified without external services.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from . import intents as intent_mod
from . import knowledge_base as kb
from . import llm as llm_mod
from . import prompts as prompt_mod
from . import responders
from . import response_validator as validator
from . import retriever
from . import transactions as tr
from .intents import IntentResult


@dataclass
class AssistantResult:
    """Complete result of one chatbot turn."""
    question: str
    intent: str
    confidence: float
    response: str
    facts: dict = field(default_factory=dict)
    retrieved: list = field(default_factory=list)
    validation: str = "pass"
    validation_notes: list = field(default_factory=list)
    llm_used: bool = False
    matched: list = field(default_factory=list)
    period: Optional[str] = None
    category: Optional[str] = None


class FinancialAssistant:
    """The HisabDo AI Financial Assistant engine."""

    def __init__(self, transactions=None, knowledge=None,
                 reference_date: Optional[dt.date] = None,
                 use_llm: bool = False):
        self.transactions = transactions if transactions is not None \
            else tr.load_transactions()
        self.knowledge = knowledge if knowledge is not None \
            else kb.load_knowledge_base()
        self.reference_date = reference_date or dt.date.today()
        self.use_llm = use_llm and llm_mod.llm_available()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def ask(self, question: str) -> AssistantResult:
        """Run the full assistant flow for ``question``."""
        detected = intent_mod.detect_intent(question)
        turn = AssistantResult(
            question=question,
            intent=detected.intent,
            confidence=round(detected.confidence, 2),
            response="",
            matched=detected.matched,
            period=detected.period,
            category=detected.category,
        )
        self._enrich_period(detected, turn)

        # RAG retrieval for the intents that benefit from retrieval context.
        if turn.intent in ("SAVING_TIP", "MONTHLY_EXPENSE", "SPENDING_SUMMARY",
                           "HIGHEST_CATEGORY"):
            turn.retrieved = retriever.retrieve(question, self.knowledge, top_k=2)
        if turn.intent == "MONTHLY_EXPENSE":
            self._handle_monthly(turn)
        elif turn.intent == "HIGHEST_CATEGORY":
            self._handle_highest(turn)
        elif turn.intent == "SPENDING_SUMMARY":
            self._handle_summary(turn)
        elif turn.intent == "SAVING_TIP":
            self._handle_saving_tip(turn)
        elif turn.intent == "GREETING":
            turn.response = responders.respond_greeting()
        elif turn.intent == "HELP":
            turn.response = responders.respond_help()
        elif turn.intent == "THANKS":
            turn.response = responders.respond_thanks()
        elif turn.intent == "AMBIGUOUS":
            turn.response = responders.respond_ambiguous(question)
        else:  # UNSUPPORTED / default
            turn.response = responders.respond_unsupported()

        result = validator.validate_response(
            turn.intent, turn.response, facts=turn.facts
        )
        turn.validation = "pass" if result.ok else "fail"
        turn.validation_notes = result.issues

        if self.use_llm and turn.intent in intent_mod.SUPPORTED_INTENTS:
            turn = self._apply_llm_polish(question, turn)

        return turn

    # ------------------------------------------------------------------ #
    # Intent handlers
    # ------------------------------------------------------------------ #
    def _handle_monthly(self, turn: AssistantResult) -> None:
        period, resolved = self._resolved_period(turn.period)
        if period is None:
            turn.response = responders.respond_ambiguous(turn.question)
            return
        summary = tr.summary_for_period(self.transactions, period)
        turn.period = period
        turn.facts = summary
        if not summary["categories"]:
            turn.response = (
                f"I could not find any transactions for {responders._fmt_month(period)}. "
                "Try another month."
            )
            return
        turn.response = responders.respond_monthly_expense(summary)

    def _handle_highest(self, turn: AssistantResult) -> None:
        period, resolved = self._resolved_period(turn.period)
        top = tr.highest_category_for_period(self.transactions, period)
        turn.period = period
        facts = dict(top or {})
        if period:
            facts["period"] = period
        turn.facts = facts
        turn.response = responders.respond_highest_category(facts)

    def _handle_summary(self, turn: AssistantResult) -> None:
        period, resolved = self._resolved_period(turn.period)
        if period is None:
            resolved_period = self._current_month_prefix()
            summary = tr.summary_for_period(self.transactions, resolved_period)
            turn.period = resolved_period
            turn.facts = summary
            turn.response = responders.respond_spending_summary(summary)
            return
        summary = tr.summary_for_period(self.transactions, period)
        turn.period = period
        turn.facts = summary
        turn.response = responders.respond_spending_summary(summary)

    def _handle_saving_tip(self, turn: AssistantResult) -> None:
        if not turn.retrieved:
            turn.response = responders.respond_saving_tip([], turn.question)
            return
        turn.facts = {"source": "data/saving_tips.md",
                      "retrieved": [rc.chunk.title for rc in turn.retrieved]}
        turn.response = responders.respond_saving_tip(turn.retrieved, turn.question)
# ------------------------------------------------------------------ #
    # Period helpers
    # ------------------------------------------------------------------ #
    def _current_month_prefix(self) -> str:
        return self.reference_date.strftime("%Y-%m")

    def _last_month_prefix(self) -> str:
        year, month = self.reference_date.year, self.reference_date.month
        if month == 1:
            year, month = year - 1, 12
        else:
            month -= 1
        return dt.date(year, month, 1).strftime("%Y-%m")

    def _resolved_period(self, detected_period: Optional[str]):
        """Return (period, resolved_source) for a detected period.

        Explicit periods like ``2026-07`` pass through unchanged and are
        returned as explicit. ``None`` means no period was resolved.
        """
        if detected_period:
            return detected_period, "explicit"
        return None, "unknown"

    def _enrich_period(self, detected: IntentResult, turn: AssistantResult) -> None:
        """Resolve relative phrases to a concrete month prefix.

        Handles 'this month' / 'last month' against the configured reference
        date, and bare month names (e.g. "in july") using the
        reference year.
        """
        norm = intent_mod._normalise(turn.question)
        period = detected.period
        if period is None and "last month" in norm:
            period = self._last_month_prefix()
        elif period is None and ("this month" in norm or "monthly" in norm):
            period = self._current_month_prefix()
        elif period is None and intent_mod._has_period_phrase(norm):
            for name, num in intent_mod._MONTH_NAME_TO_NUM.items():
                if name in norm:
                    period = f"{self.reference_date.year}-{num}"
                    break
        turn.period = period

    # ------------------------------------------------------------------ #
    # Optional LLM polish
    # ------------------------------------------------------------------ #
    def _apply_llm_polish(self, question: str, turn: AssistantResult) -> AssistantResult:
        facts_text = str(turn.facts)
        context_text = ""
        if turn.retrieved:
            context_text = "\n".join(rc.chunk.text for rc in turn.retrieved)
        try:
            polished = llm_mod.complete_with_llm(
                question,
                prompt_mod.build_system_prompt(),
                prompt_mod.build_user_prompt(question, facts_text, context_text),
            )
            if validator.validate_response(turn.intent, polished, facts=turn.facts).ok:
                turn.response = polished
                turn.llm_used = True
        except llm_mod.LLMUnavailableError:
            pass  # deterministic response retained on no key
        except Exception:
            pass  # any network/model error -> deterministic response retained
        return turn