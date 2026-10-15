from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import json
from src.financial_assistant.faq_rag import get_retriever

path = PROJECT_ROOT / "tests" / "evaluation_question_set.json"
cases = json.loads(path.read_text(encoding="utf-8-sig"))
retriever = get_retriever()
passed = 0

print(f"Evaluation questions: {len(cases)}")
print("-" * 72)

for case in cases:
    matches = retriever.retrieve(case["question"], top_k=1)
    actual = matches[0]["id"] if matches else None
    expected = case["expected_faq_ids"]

    if expected:
        ok = actual in expected
    else:
        ok = actual is None

    status = "PASS" if ok else "REVIEW"
    passed += int(ok)

    print(f'[{status}] {case["id"]} | {case["type"]}')
    print(f'  Question: {case["question"]}')
    print(f'  Expected FAQ: {expected or "No match / safe clarification"}')
    print(f'  Actual FAQ: {actual or "No match"}')

    if not ok and case.get("expected_behavior"):
        print(f'  Review: {case["expected_behavior"]}')

print("-" * 72)
print(f"Retrieval checks passed: {passed}/{len(cases)}")
print(f"Needs review: {len(cases) - passed}")
