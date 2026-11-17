"""Safe logs and metrics for chatbot turns (docs/dept3-monitoring-runbook.md, "Safe logging fields").

Only fields named in SAFE_FIELDS are ever written. Message text, reply text, amounts, names, phone numbers, user
ids, tokens and keys are never fields; any string value that still looks like a secret or a personal identifier is
replaced by "[redacted]" and counted. The user is identified only by a salted hash (user_ref) so turns of one user can
be grouped without storing who they are.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import threading
from collections import Counter, deque
from contextvars import ContextVar

log = logging.getLogger("hisabdo.ai.telemetry")
REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)

SAFE_FIELDS: dict[str, str] = {
    "request_id": "id of the HTTP request (also in the access log)",
    "user_ref": "salted HMAC of the user id, 12 hex characters; not reversible without TELEMETRY_SALT",
    "route": "router decision: knowledge | transaction | account_data | general | guard",
    "intent": "intent or block category, e.g. product_faq, add_expense, blocked_prompt_injection",
    "source": "what produced the reply: rag | kb_fallback | clarification | backend_financial_api | dialogue | "
              "guardrail | output_guard | policy_guard | llm_general | greeting_fastpath | backend_unavailable | "
              "llm_unavailable | kb_unavailable | service_fallback",
    "answer_status": "answered | conflict | no_source | out_of_scope | clarify (knowledge route only)",
    "language": "en | roman_ur | ur",
    "retrieval_mode": "hybrid | lexical | none",
    "retrieved_ids": "KB chunk ids that passed the retrieval threshold (public KB content, no user data)",
    "cited_ids": "KB chunk ids cited in the reply",
    "retrieval_ms": "retrieval time in ms",
    "latency_ms": "end-to-end handling time in ms",
    "llm_called": "true when a model provider was called",
    "llm_provider": "mock | groq | openai | anthropic | gemini",
    "tokens_used": "tokens reported by the provider (0 for deterministic replies)",
    "needs_review": "true when official sources conflict",
    "fallback": "which safe fallback answered: none | no_source | kb_unavailable | llm_error | backend_error | internal_error",
    "error_category": "none | llm_error | llm_timeout | backend_error | kb_unavailable | kb_update_rejected | internal_error",
    "kb_version": "first 12 hex of the KB file's sha256",
    "output_findings": "what the output guard removed: secret | prompt_text | contact_or_identifier_removed",
}

_SCRUB = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"            # e-mail
    r"|(?:\+92[\s-]?|0)3\d{2}[\s-]?\d{7}\b"                         # Pakistani mobile
    r"|\b\d{5}-\d{7}-\d\b"                                          # CNIC
    r"|\b(sk-[A-Za-z0-9]{16,}|AIza[0-9A-Za-z_-]{30,}|gsk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,})"
    r"|\b(?:rs\.?|pkr|usd)\s?\d[\d,]*", re.I)                       # money amounts
_SALT = (os.environ.get("TELEMETRY_SALT") or secrets.token_hex(16)).encode()


def user_ref(user_id: str) -> str:
    return hmac.new(_SALT, user_id.encode(), hashlib.sha256).hexdigest()[:12]


def _secret_values() -> list[str]:
    return [v for k, v in os.environ.items() if re.search(r"TOKEN|KEY|SECRET|PASSWORD|SALT", k) and len(v) >= 8]


def _clean(value):
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value][:10]
    if isinstance(value, str):
        if any(s in value for s in _secret_values()) or _SCRUB.search(value):
            METRICS.count("telemetry_redactions")
            return "[redacted]"
        return value[:80]
    return value


def safe_event(**fields) -> dict:
    """Keep only allowlisted fields; scrub what remains."""
    dropped = [k for k in fields if k not in SAFE_FIELDS]
    if dropped:
        METRICS.count("telemetry_dropped_fields", len(dropped))
    return {k: _clean(v) for k, v in fields.items() if k in SAFE_FIELDS and v is not None}


class Metrics:
    """In-process counters and latency windows; read through GET /api/v1/metrics."""

    def __init__(self, window: int = 2000):
        self._lock = threading.Lock()
        self.counters: Counter = Counter()
        self.latency: dict[str, deque] = {}
        self.window = window

    def count(self, name: str, n: int = 1) -> None:
        with self._lock:
            self.counters[name] += n

    def observe(self, route: str, ms: float) -> None:
        with self._lock:
            self.latency.setdefault(route, deque(maxlen=self.window)).append(ms)

    def snapshot(self) -> dict:
        with self._lock:
            lat = {}
            for route, xs in self.latency.items():
                s = sorted(xs)
                q = lambda p: round(s[min(len(s) - 1, int(round(p * (len(s) - 1))))], 1)  # noqa: E731
                lat[route] = {"n": len(s), "p50_ms": q(0.5), "p95_ms": q(0.95), "max_ms": round(s[-1], 1)}
            return {"counters": dict(self.counters), "latency": lat}

    def reset(self) -> None:
        with self._lock:
            self.counters.clear()
            self.latency.clear()


METRICS = Metrics()


def record_turn(**fields) -> dict:
    event = safe_event(**fields)
    METRICS.count("turns")
    METRICS.count(f"source:{event.get('source', 'unknown')}")
    if event.get("answer_status"):
        METRICS.count(f"answer_status:{event['answer_status']}")
    if event.get("error_category", "none") != "none":
        METRICS.count(f"error:{event['error_category']}")
    if event.get("fallback", "none") != "none":
        METRICS.count(f"fallback:{event['fallback']}")
    if "latency_ms" in event:
        METRICS.observe(event.get("route", "unknown"), event["latency_ms"])
    log.info("chat_turn", extra={"turn": event})
    return event
