"""
Intent router accuracy on the labelled message sets.

    python scripts/evaluate_intent_router.py      (from the repo root)

data/intent_eval_cases.json          - used while writing the rules
data/intent_eval_cases_heldout.json  - written afterwards, NOT used for tuning (the honest number)
Also reports how many private questions (balance / report) were sent to a non-private route.
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.financial_assistant.dialogue.recognizer import RuleBasedIntentRecognizer  # noqa: E402

PRIVATE = {"report", "account_query"}


def run(name: str) -> None:
    cases = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))["cases"]
    recognizer, misses = RuleBasedIntentRecognizer(), []
    for c in cases:
        got = recognizer.recognize(c["text"], date(2026, 10, 14)).intent.value
        if got != c["intent"]:
            misses.append((c["text"], c["intent"], got))
    leaks = [m for m in misses if m[1] in PRIVATE and m[2] not in PRIVATE]
    correct = len(cases) - len(misses)
    print(f"\n{name}: {correct}/{len(cases)} correct ({correct / len(cases):.0%}) | "
          f"private questions sent to a non-private route: {len(leaks)}")
    for text, want, got in misses:
        print(f"  MISS  expected {want:20s} got {got:20s} | {text}")


if __name__ == "__main__":
    run("intent_eval_cases.json")
    run("intent_eval_cases_heldout.json")
