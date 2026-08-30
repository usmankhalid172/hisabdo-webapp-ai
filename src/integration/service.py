"""Application-facing service adapter (capstone integration layer).

This module is the connection point between the HisabDo application/service
layer and the Chatbot/RAG POC engine:

    HisabDo App / Backend
        -> AssistantService.ask(question, reference_date)   (this module)
             -> FinancialAssistant pipeline                 (engine.py)
                  intent -> facts -> RAG -> response -> validation
        -> plain-dict payload back to the application

Why an adapter?
- The application layer should not import engine internals; it gets one
  stable entry point with validated inputs and structured outputs.
- Transaction data can come from three sources without changing callers:
  1. the default sample CSV (POC behaviour),
  2. a CSV file path supplied by the backend,
  3. injected records (list of dicts) - the shape the real HisabDo backend
     would serve once the production schema is approved.
- Every response includes a ``status`` field and latency so the app layer can
  monitor the flow end to end.

The FastAPI routes in :mod:`src.integration.app` expose this adapter through
the versioned endpoints ``GET /v1/assistant/health`` and
``POST /v1/assistant/query``.
"""

from __future__ import annotations

import datetime as dt
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from ..financial_assistant import engine as engine_mod
from ..financial_assistant import intents as intent_mod
from ..financial_assistant import knowledge_base as kb
from ..financial_assistant import llm as llm_mod
from ..financial_assistant import transactions as tr

SERVICE_NAME = "hisabdo-ai-assistant"
SERVICE_VERSION = "0.1.0"

# Accepted transaction sources: nothing (default CSV), a CSV path,
# or already-loaded records (dicts) handed over by the application backend.
TransactionSource = Union[None, str, Path, Sequence[Dict[str, Any]]]


class ServiceInputError(ValueError):
    """Raised when the application layer sends an invalid request."""


class AssistantService:
    """Stable application-facing facade over the assistant pipeline."""

    def __init__(self, transactions_source: TransactionSource = None):
        self._transactions_source = transactions_source
        self.transactions = self._load_transactions()
        self._knowledge = kb.load_knowledge_base()

    # ------------------------------------------------------------------ #
    # Data-source handling
    # ------------------------------------------------------------------ #
    def _load_transactions(self) -> list:
        """Load transactions from the configured source.

        Raises :class:`ServiceInputError` when injected records are malformed
        so the application gets a precise, actionable error instead of a
        deep traceback from inside the engine.
        """
        source = self._transactions_source
        if source is None:
            return tr.load_transactions()
        if isinstance(source, (str, Path)):
            return tr.load_transactions(path=source)
        rows: List[tr.Transaction] = []
        for index, record in enumerate(source):
            try:
                rows.append(tr.Transaction(
                    date=record["date"],
                    category=record["category"],
                    description=record.get("description", ""),
                    amount=float(record["amount"]),
                ))
            except (KeyError, TypeError, ValueError) as exc:
                raise ServiceInputError(
                    f"Invalid transaction record at index {index}: {record!r}"
                ) from exc
        return rows

    def _data_source_label(self) -> str:
        source = self._transactions_source
        if source is None:
            return "default_csv"
        if isinstance(source, (str, Path)):
            return f"csv:{Path(source).name}"
        return "injected_records"

    # ------------------------------------------------------------------ #
    # Public API (plain dicts -> easy consumption by any app backend)
    # ------------------------------------------------------------------ #
    def health(self) -> Dict[str, Any]:
        """Service status payload for the application health check."""
        return {
            "status": "ok",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "intents_supported": list(intent_mod.SUPPORTED_INTENTS),
            "knowledge_base_chunks": len(self._knowledge),
            "transactions_loaded": len(self.transactions),
            "llm_available": llm_mod.llm_available(),
            "data_source": self._data_source_label(),
        }

    def ask(self, question: str,
            reference_date: Optional[str] = None) -> Dict[str, Any]:
        """Run one chatbot turn and return an application-ready payload."""
        started = time.perf_counter()
        if question is None or not str(question).strip():
            raise ServiceInputError("question must be a non-empty string")
        reference = self._parse_reference_date(reference_date)

        # Per-request instance: shared state is never mutated (Bug C guard).
        assistant = engine_mod.FinancialAssistant(
            transactions=self.transactions,
            knowledge=self._knowledge,
            reference_date=reference,
        )
        result = assistant.ask(str(question).strip())
        latency_ms = round((time.perf_counter() - started) * 1000, 1)

        return {
            "status": "ok",
            "question": result.question,
            "intent": result.intent,
            "confidence": result.confidence,
            "response": result.response,
            "period": result.period,
            "category": result.category,
            "facts": result.facts,
            "retrieved": [
                {"title": rc.chunk.title, "score": rc.score,
                 "text": rc.chunk.text}
                for rc in result.retrieved
            ],
            "validation": result.validation,
            "validation_notes": result.validation_notes,
            "llm_used": result.llm_used,
            "matched": result.matched,
            "latency_ms": latency_ms,
        }

    # ------------------------------------------------------------------ #
    # Validation helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _parse_reference_date(reference_date):
        if reference_date is None:
            return dt.date.today()
        if not isinstance(reference_date, str):
            raise ServiceInputError("reference_date must be YYYY-MM-DD")
        try:
            return dt.date.fromisoformat(reference_date)
        except ValueError as exc:
            raise ServiceInputError(
                "reference_date must be YYYY-MM-DD"
            ) from exc

