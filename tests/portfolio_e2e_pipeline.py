"""
Offline, deterministic validation helpers for the XICTEK Portfolio & Case Studies E2E submission.

This package validates supplied production observations against an explicit reference
baseline. It does not call the production chatbot and does not claim deployment parity.
"""
from __future__ import annotations
from dataclasses import dataclass
from statistics import mean, median
from math import ceil, floor
from urllib.parse import urlparse
from typing import Iterable, Optional
import re

PORTFOLIO_URL = "https://xicteksystems.com/portfolio"
ABOUT_URL = "https://hisabdo.app/about"
EXPECTED_STACK = ("Flutter", "Supabase", "PostgreSQL")
EXPECTED_OUTCOME = ("expense tracking", "digital khata", "customer balances")
ALLOWED_HOSTS = {"xicteksystems.com", "www.xicteksystems.com", "hisabdo.app", "www.hisabdo.app"}

@dataclass(frozen=True)
class BenchmarkStats:
    count: int
    mean_ms: float
    median_ms: float
    p95_linear_ms: float
    p95_nearest_rank_ms: float
    minimum_ms: float
    maximum_ms: float

def percentile_linear(values: Iterable[float], percentile: float) -> float:
    data = sorted(float(x) for x in values)
    if not data:
        raise ValueError("percentile requires at least one value")
    if not 0 <= percentile <= 100:
        raise ValueError("percentile must be between 0 and 100")
    position = (len(data) - 1) * percentile / 100
    lower, upper = floor(position), ceil(position)
    fraction = position - lower
    return data[lower] + fraction * (data[upper] - data[lower])

def percentile_nearest_rank(values: Iterable[float], percentile: float) -> float:
    data = sorted(float(x) for x in values)
    if not data:
        raise ValueError("percentile requires at least one value")
    if not 0 < percentile <= 100:
        raise ValueError("nearest-rank percentile must be in (0, 100]")
    return data[ceil(percentile / 100 * len(data)) - 1]

def calculate_stats(values: Iterable[float]) -> BenchmarkStats:
    data = [float(x) for x in values]
    if not data:
        raise ValueError("at least one observation is required")
    return BenchmarkStats(
        count=len(data), mean_ms=mean(data), median_ms=median(data),
        p95_linear_ms=percentile_linear(data, 95),
        p95_nearest_rank_ms=percentile_nearest_rank(data, 95),
        minimum_ms=min(data), maximum_ms=max(data),
    )

def validate_https_url(url: str) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "URL could not be parsed"
    if parsed.scheme != "https":
        return False, "HTTPS is required"
    if not parsed.hostname:
        return False, "Hostname is missing"
    if parsed.username or parsed.password:
        return False, "Credentials embedded in URL are not allowed"
    return True, "Syntactically valid HTTPS URL"

def classify_source_for_claim(url: str, claim_type: str) -> bool:
    """Rule-based source/claim association; not semantic proof or reachability."""
    ok, _ = validate_https_url(url)
    if not ok:
        return False
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if claim_type in {"portfolio_stack", "portfolio_challenge", "portfolio_outcome", "project_identity"}:
        return parsed.hostname in {"xicteksystems.com", "www.xicteksystems.com"} and path == "/portfolio"
    if claim_type == "about_features":
        return parsed.hostname in {"hisabdo.app", "www.hisabdo.app"} and path == "/about"
    return False

def contains_expected_stack(text: str) -> bool:
    lowered = text.lower()
    return all(item.lower() in lowered for item in EXPECTED_STACK)

def contains_expected_outcome(text: str) -> bool:
    lowered = text.lower()
    return all(item in lowered for item in EXPECTED_OUTCOME)

def unsupported_metric_fallback(text: str) -> bool:
    lowered = text.lower()
    abstains = any(term in lowered for term in (
        "does not specify", "not specified", "cannot verify", "can't verify",
        "not available", "no verified", "not provided", "cannot confirm"
    ))
    avoids_number = not re.search(r"\b\d+(?:\.\d+)?\s*%", lowered)
    return abstains and avoids_number

def resolve_contextual_query(message: str, history: list[dict]) -> str:
    """Minimal deterministic entity-preservation proposal for offline tests.

    This is a test-harness strategy, NOT implemented in the supplied production
    service. It preserves explicit project identity when a follow-up uses pronouns.
    """
    if re.search(r"\b(it|its|they|them|that project|this project)\b", message, re.I):
        prior = " ".join(t.get("content", "") for t in history if t.get("role") == "user")
        if re.search(r"\bhisabdo\b", prior, re.I):
            return f"HisabDo {message}".strip()
    return message

def empty_retrieval_fallback(matches: list) -> str:
    if not matches:
        return ("I don't have verified information for that question in the available "
                "knowledge base. Please consult the relevant official page.")
    return ""

def safe_generation(generate, *args, **kwargs) -> tuple[str, str]:
    """Maps a provider exception to a deterministic service-unavailable response."""
    try:
        return generate(*args, **kwargs), "answered"
    except Exception:
        return ("Sorry, the assistant could not complete that answer. Please try again later.",
                "provider_error")

def is_outlier_iqr(values: Iterable[float], multiplier: float = 1.5) -> list[float]:
    data = sorted(float(x) for x in values)
    if len(data) < 4:
        return []
    q1 = percentile_linear(data, 25)
    q3 = percentile_linear(data, 75)
    upper = q3 + multiplier * (q3 - q1)
    lower = q1 - multiplier * (q3 - q1)
    return [x for x in data if x < lower or x > upper]
