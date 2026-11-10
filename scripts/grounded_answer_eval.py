"""Measure the grounded answer rules on the judged question sets.

Runs every Day 1 and held-out question through router gate -> KbRetriever -> GroundedAnswerer (extractive, as with
the mock provider) and grades each reply with the relevance judgments in data/retrieval_eval/qrels.json:

  correct_answer   answerable question, every cited passage judged relevant, at least one judged as answering it
  safe_no_answer   answerable question, but the reply clarifies or falls back (no unsupported facts)
  wrong_citation   a cited passage was judged unrelated (or a "must be empty" question got a cited answer)
  correct_refusal  "must be empty" / unanswerable question that gets a fallback, clarification or conflict notice

    python scripts/grounded_answer_eval.py [--mode lexical|hybrid]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from src.financial_assistant.dialogue.recognizer import RuleBasedIntentRecognizer  # noqa: E402
from src.financial_assistant.grounding import GroundedAnswerer, KbRetriever  # noqa: E402
import retrieval_eval as R  # noqa: E402


def grade(q: dict, exp: str, ans, qrels: dict) -> str:
    grades = [qrels.get(q["id"], {}).get(c.chunk_id, 0) for c in ans.citations]
    if ans.status == "conflict":
        return "correct_answer" if exp == "answer" and 2 in grades else "correct_refusal" if exp != "answer" else "safe_no_answer"
    if ans.status != "answered":
        return "safe_no_answer" if exp == "answer" else "correct_refusal"
    if exp == "none" or 0 in grades:
        return "wrong_citation"
    if exp == "answer" and 2 in grades:
        return "correct_answer"
    return "safe_no_answer" if exp == "answer" else "correct_refusal"  # only background passages cited


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="hybrid", choices=["lexical", "hybrid"])
    a = ap.parse_args()
    router = RuleBasedIntentRecognizer()
    answerer = GroundedAnswerer(KbRetriever(mode=a.mode))
    qrels = R.load_qrels()
    rows, by = [], {}
    for name in ("queries_dev_day1.json", "queries_heldout.json"):
        for q in R.load_queries(name):
            exp = R.expectation(q, qrels)
            intent = router.recognize(q["text"], date(2026, 10, 28)).intent.value
            if intent in ("faq", "general"):
                ans = answerer.answer(q["text"], kb_allowed=intent == "faq")
                status = ans.status
            else:   # transactions, reports, own figures, other people's accounts: other routes, no KB reply
                ans, status = None, f"routed:{intent}"
            g = grade(q, exp, ans, qrels) if ans else ("correct_refusal" if exp != "answer" else "safe_no_answer")
            rows.append({"id": q["id"], "set": name.split("_")[1], "lang": q["lang"], "expect": exp, "status": status,
                         "grade": g, "cited": [c.chunk_id for c in ans.citations] if ans else []})
            by.setdefault(name.split("_")[1], Counter())[g] += 1
    langs = Counter((r["lang"], r["grade"]) for r in rows if r["expect"] == "answer")
    out = {"mode": a.mode, "totals": {k: dict(v) for k, v in by.items()},
           "answerable_by_language": {f"{l}:{g}": n for (l, g), n in sorted(langs.items())},
           "statuses": dict(Counter(r["status"] for r in rows)), "rows": rows}
    path = R.EVAL / "results" / f"grounded_answers_{a.mode}.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("mode", "totals", "answerable_by_language", "statuses")}, indent=1))
    for r in rows:
        if r["grade"] == "wrong_citation":
            print("WRONG", r["id"], r["status"], r["cited"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
