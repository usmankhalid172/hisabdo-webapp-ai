"""Privacy-safe monitoring helpers for the Department 3 financial assistant."""

import logging
import math
import re
import time
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger("financial_assistant.monitoring")

ALLOWED_EVENTS = {
    "chat_request",
    "retrieval",
    "provider_call",
    "backend_call",
    "index_update",
}

ALLOWED_COMPONENTS = {
    "chat",
    "retrieval",
    "provider",
    "backend",
    "index",
}

ALLOWED_PROVIDERS = {
    "mock",
    "anthropic",
    "openai",
    "gemini",
    "groq",
}

ALLOWED_MODELS = {
    "claude-sonnet-4-6",
    "gpt-4o-mini",
    "gemini-2.5-flash",
    "openai/gpt-oss-120b",
}

ALLOWED_OUTCOMES = {"success", "fallback", "blocked", "error"}

ALLOWED_ERROR_CATEGORIES = {
    "validation",
    "guardrail",
    "retrieval",
    "index_update",
    "backend",
    "provider",
    "unknown",
}


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(started_at: float) -> float:
    return round(max(0.0, time.perf_counter() - started_at) * 1000, 2)


def safe_log_event(
    event: str,
    *,
    outcome: str,
    latency_ms: float | None = None,
    component: str = "chat",
    provider: str | None = None,
    model: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    retrieved_source_ids: list[str] | None = None,
    error_category: str | None = None,
) -> None:
    """Log allowlisted operational metadata only."""

    safe_sources = [
        source_id
        for source_id in (retrieved_source_ids or [])
        if isinstance(source_id, str)
        and re.fullmatch(
            r"(faq|finance)[_-][A-Za-z0-9_-]{1,64}",
            source_id,
        )
    ]

    metadata = {
        "event": event if isinstance(event, str) and event in ALLOWED_EVENTS else "chat_request",
        "component": component if isinstance(component, str) and component in ALLOWED_COMPONENTS else "chat",
        "outcome": outcome if isinstance(outcome, str) and outcome in ALLOWED_OUTCOMES else "error",
        "latency_ms": (
            round(max(0.0, float(latency_ms)), 2)
            if isinstance(latency_ms, (int, float))
            and not isinstance(latency_ms, bool)
            and math.isfinite(latency_ms)
            else None
        ),
        "provider": provider if isinstance(provider, str) and provider in ALLOWED_PROVIDERS else None,
        "model": model if isinstance(model, str) and model in ALLOWED_MODELS else None,
        "input_tokens": (
            max(0, input_tokens)
            if isinstance(input_tokens, int) and not isinstance(input_tokens, bool)
            else None
        ),
        "output_tokens": (
            max(0, output_tokens)
            if isinstance(output_tokens, int) and not isinstance(output_tokens, bool)
            else None
        ),
        "retrieved_source_ids": safe_sources,
        "error_category": (
            error_category
            if isinstance(error_category, str) and error_category in ALLOWED_ERROR_CATEGORIES
            else None
        ),
    }

    logger.info("monitoring_event %s", metadata)


@dataclass
class MonitoringCounters:
    """In-process counters; values reset when the process restarts."""

    _counts: dict[str, int] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)

    ALLOWED_COUNTERS = {
        "requests",
        "success",
        "fallback",
        "blocked",
        "errors",
        "retrieval_empty",
        "retrieval_success",
        "index_update_failures",
        "provider_failures",
        "backend_failures",
    }

    def increment(self, name: str, amount: int = 1) -> None:
        if name not in self.ALLOWED_COUNTERS:
            return
        if not isinstance(amount, int) or isinstance(amount, bool):
            return

        with self._lock:
            self._counts[name] = self._counts.get(name, 0) + max(0, amount)

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counts)


monitoring_counters = MonitoringCounters()

def record_provider_failure(
    provider: str,
    model: str,
    started_at: float,
) -> None:
    """Record provider failures without logging exception or request contents."""

    monitoring_counters.increment("provider_failures")
    monitoring_counters.increment("errors")

    safe_log_event(
        "provider_call",
        component="provider",
        outcome="error",
        provider=provider,
        model=model,
        latency_ms=elapsed_ms(started_at),
        error_category="provider",
    )
