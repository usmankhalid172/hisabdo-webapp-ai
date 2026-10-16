"""Multilingual coverage of the chatbot's intent router (English, Urdu script, Roman Urdu).

Runs every case in data/multilingual_product_test_cases.json through the team's
intent recognizer (src/financial_assistant/dialogue) and reports, per language
and per product area, how many were understood and routed correctly.

The most important number is SAFETY: a private question ("how much do I owe?")
must never be sent to a non-private route, where the knowledge base or the AI
model could answer it with made-up figures.

Usage (from the repository root):
    python scripts/evaluate_multilingual_coverage.py
    python scripts/evaluate_multilingual_coverage.py --markdown docs/out.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.financial_assistant.dialogue.models import PRIVATE_INTENTS, TRANSACTION_INTENTS, Intent, Route  # noqa: E402
from src.financial_assistant.dialogue.recognizer import RuleBasedIntentRecognizer  # noqa: E402

CASES_FILE = ROOT / "data" / "multilingual_product_test_cases.json"
HELDOUT_FILE = ROOT / "data" / "multilingual_product_test_cases_heldout.json"
TODAY = date(2026, 10, 16)
LANGUAGE_NAMES = {"en": "English", "ur": "Urdu script", "roman_ur": "Roman Urdu"}


def route_of(intent: Intent) -> Route:
    if intent in PRIVATE_INTENTS:
        return Route.ACCOUNT_DATA
    if intent in TRANSACTION_INTENTS:
        return Route.TRANSACTION
    if intent == Intent.FAQ:
        return Route.KNOWLEDGE
    return Route.GENERAL


def evaluate(cases: list[dict]) -> list[dict]:
    recognizer = RuleBasedIntentRecognizer()
    rows = []
    for case in cases:
        result = recognizer.recognize(case["text"], TODAY)
        expected = Intent(case["expect_intent"])
        rows.append({
            **case,
            "got_intent": result.intent.value,
            "expected_route": route_of(expected).value,
            "got_route": route_of(result.intent).value,
            "detected_language": result.language.value,
            "intent_ok": result.intent == expected,
            "route_ok": route_of(result.intent) == route_of(expected),
            # A private question answered anywhere but the private route is a data-safety failure.
            "private_leak": expected in PRIVATE_INTENTS and result.intent not in PRIVATE_INTENTS,
            # A product question that starts an entry flow is a usability failure (asks "kitne ka?").
            "faq_into_flow": expected == Intent.FAQ and result.intent in TRANSACTION_INTENTS,
        })
    return rows


def summarise(rows: list[dict]) -> dict:
    by = lambda key: defaultdict(list, {})  # noqa: E731
    groups = {"language": by("language"), "area": by("area")}
    for r in rows:
        groups["language"][r["language"]].append(r)
        groups["area"][r["area"]].append(r)
    return groups


def to_markdown(rows: list[dict]) -> str:
    groups = summarise(rows)
    total, ok = len(rows), sum(r["route_ok"] for r in rows)
    lines = [
        f"**Overall: {ok}/{total} routed correctly ({ok / total:.0%}); intent exact match "
        f"{sum(r['intent_ok'] for r in rows)}/{total}.**",
        "",
        f"- Private questions sent to a non-private route (data-safety failures): "
        f"**{sum(r['private_leak'] for r in rows)}**",
        f"- Product questions that wrongly started an entry flow: **{sum(r['faq_into_flow'] for r in rows)}**",
        "",
        "| Language | Routed correctly |",
        "|---|---|",
    ]
    for lang in ("en", "roman_ur", "ur"):
        rs = groups["language"][lang]
        lines.append(f"| {LANGUAGE_NAMES[lang]} | {sum(r['route_ok'] for r in rs)}/{len(rs)} |")
    lines += ["", "| Area | Routed correctly |", "|---|---|"]
    for area, rs in groups["area"].items():
        lines.append(f"| {area} | {sum(r['route_ok'] for r in rs)}/{len(rs)} |")
    misses = [r for r in rows if not r["route_ok"]]
    if misses:
        lines += ["", "| Case | Message | Expected | Got | Why it matters |", "|---|---|---|---|---|"]
        for r in misses:
            why = ("private question on a public route" if r["private_leak"]
                   else "product question starts an entry flow" if r["faq_into_flow"] else "wrong route")
            lines.append(f"| {r['id']} | {r['text']} | {r['expect_intent']} ({r['expected_route']}) | "
                         f"{r['got_intent']} ({r['got_route']}) | {why} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--markdown", help="also write the summary to this file")
    ap.add_argument("--heldout", action="store_true", help="use the held-out set (never used for tuning)")
    args = ap.parse_args()
    source = HELDOUT_FILE if args.heldout else CASES_FILE
    cases = json.loads(source.read_text(encoding="utf-8"))["cases"]
    rows = evaluate(cases)
    for r in rows:
        mark = "OK  " if r["route_ok"] else ("LEAK" if r["private_leak"] else "MISS")
        print(f"{mark} {r['id']:9} expect {r['expect_intent']:13} got {r['got_intent']:19} "
              f"lang={r['detected_language']:8} {r['text']}")
    report = to_markdown(rows)
    print("\n" + report)
    if args.markdown:
        Path(args.markdown).write_text(report, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
