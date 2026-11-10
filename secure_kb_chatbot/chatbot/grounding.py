"""Post-generation checks that the answer stays inside the supplied context.

The prompt asks the model not to invent anything; this module verifies the
parts of that which can be checked mechanically:

1. Every cited record ID (in the citations list or inline as ``[C-001]``) must
   be one the context builder actually included this turn. Unknown IDs are
   stripped from the answer and reported.
2. Every monetary amount in the answer must appear somewhere in the context
   (record values or precomputed totals). Unsupported amounts are flagged.
3. An answer that claims to be "grounded" but cites nothing is downgraded.

Failures downgrade ``grounding`` and add ``warnings`` that the UI shows; they
don't silently rewrite the answer beyond removing fabricated citations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_INLINE_CITATION = re.compile(r"\[([A-Z]{1,2}-\d{3,})\]")  # [C-001] records and [KB-012] knowledge base
# Accepts western (85,000) and South Asian (1,50,000) digit grouping.
_MONEY = re.compile(
    r"(?:[$€£₨]|\b(?:USD|PKR|EUR|GBP|Rs\.?)\s?)\s?(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s?([kKmM])?\b"
)
_NUMBER = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")


@dataclass
class GroundedAnswer:
    answer: str
    citations: list[str]
    grounding: str  # grounded | partial | insufficient_data | refused | error
    missing_information: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate(raw: dict, source_ids: set[str], context_text: str) -> GroundedAnswer:
    answer = str(raw.get("answer", "")).strip()
    grounding = raw.get("grounding", "partial")
    missing = [str(m) for m in raw.get("missing_information", [])]
    warnings: list[str] = []

    inline = _INLINE_CITATION.findall(answer)
    claimed = list(dict.fromkeys([*map(str, raw.get("citations", [])), *inline]))
    valid = [c for c in claimed if c in source_ids]
    invalid = [c for c in claimed if c not in source_ids]

    if invalid:
        warnings.append(
            "Removed citations to records that were not in the provided context: " + ", ".join(invalid)
        )
        for bad in invalid:
            answer = answer.replace(f"[{bad}]", "")
        answer = re.sub(r"[ \t]{2,}", " ", answer).replace(" .", ".")
        grounding = "partial" if grounding == "grounded" else grounding

    known_amounts = {_to_float(n) for n in _NUMBER.findall(context_text)}
    unsupported = [m.group(0).strip() for m in _MONEY.finditer(answer) if not _amount_known(m, known_amounts)]
    if unsupported:
        warnings.append("Amounts not found in the business data: " + ", ".join(dict.fromkeys(unsupported)))
        grounding = "partial" if grounding == "grounded" else grounding

    if grounding == "grounded" and not valid:
        warnings.append("Answer was marked grounded but cites no records.")
        grounding = "partial"

    return GroundedAnswer(
        answer=answer,
        citations=valid,
        grounding=grounding,
        missing_information=missing,
        warnings=warnings,
    )


def _to_float(text: str) -> float:
    return float(text.replace(",", ""))


def _amount_known(match: re.Match, known: set[float]) -> bool:
    value = _to_float(match.group(1))
    suffix = (match.group(2) or "").lower()
    if suffix == "k":
        value *= 1_000
    elif suffix == "m":
        value *= 1_000_000
    # Rounded mentions ("$12.5k" for 12,480.00) are tolerated within 1%.
    return any(abs(value - k) <= max(0.01, 0.01 * abs(k)) for k in known) if suffix else value in known
