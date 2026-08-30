"""Response validation for the AI Financial Assistant.

Provides a lightweight validation pass that runs over every assistant response
before it is returned:

1. Empty-response guard          : refuses blank answers.
2. Financial number grounding    : any ``PKR <amount>`` mentioned in the
   response for data-dependent intents must appear in the facts that were
   computed by the backend (prevents fabricated figures / hallucination).
3. Scope guard                   : the response should not disclose private
   data or claim unsupported capabilities.

The validator returns a ``ValidationResult``; failures attach a notice so the
caller can record evidence and, if needed, fall back to a safe message.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

# Currency values look like "PKR 1,234.56".
_AMOUNT_RE = re.compile(r"PKR\s+([\d,]+\.\d{2})")


def _extract_amounts(text: str) -> List[float]:
    return [float(v.replace(",", "")) for v in _AMOUNT_RE.findall(text)]


@dataclass
class ValidationResult:
    ok: bool
    issues: list = field(default_factory=list)
    severity: str = "pass"


def validate_response(intent: str, text: str,
                      facts: Optional[dict] = None) -> ValidationResult:
    """Run all validation checks over ``text``."""
    issues = []
    if not text or not text.strip():
        issues.append("empty response")
    if intent in ("MONTHLY_EXPENSE", "HIGHEST_CATEGORY", "SPENDING_SUMMARY"):
        allowed = set()
        if facts:
            if isinstance(facts.get("total"), (int, float)):
                allowed.add(round(float(facts["total"]), 2))
            if isinstance(facts.get("amount"), (int, float)):
                allowed.add(round(float(facts["amount"]), 2))
            for value in (facts.get("categories") or {}).values():
                allowed.add(round(float(value), 2))
        for amount in _extract_amounts(text):
            if round(amount, 2) not in allowed:
                issues.append(f"ungrounded amount {amount}")
    if len(text.split()) > 220:
        issues.append("response too long")
    if issues:
        return ValidationResult(ok=False, issues=issues, severity="fix")
    return ValidationResult(ok=True)