import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.financial_assistant.faq_rag import get_retriever
from src.financial_assistant.hybrid_retriever import HybridFaqRetriever


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "tests" / "evaluation_question_set.json"

cases = json.loads(DATASET.read_text(encoding="utf-8-sig"))

dense = get_retriever()
hybrid = HybridFaqRetriever()

dense_passed = 0
hybrid_passed = 0

print(f"Evaluation questions: {len(cases)}")
print("=" * 90)

for case in cases:
    question = case["question"]
    expected = case["expected_faq_ids"]

    dense_results = dense.retrieve(question, top_k=1)
    hybrid_results = hybrid.retrieve(question, top_k=3)

    dense_id = dense_results[0]["id"] if dense_results else None
    hybrid_id = hybrid_results[0]["id"] if hybrid_results else None

    dense_ok = dense_id in expected if expected else dense_id is None
    hybrid_ok = hybrid_id in expected if expected else hybrid_id is None

    dense_passed += int(dense_ok)
    hybrid_passed += int(hybrid_ok)

    print(f"\n{case['id']} | {question}")
    print(f"Expected: {expected or 'No match'}")
    print(f"TF-IDF: {dense_id or 'No match'} | {'PASS' if dense_ok else 'REVIEW'}")
    print(f"Hybrid: {hybrid_id or 'No match'} | {'PASS' if hybrid_ok else 'REVIEW'}")
    print(
        "Hybrid TOP 3:",
        [(x["id"], x["hybrid_score"], x["bm25_score"], x["tfidf_score"])
         for x in hybrid_results]
    )

print("\n" + "=" * 90)
print(f"TF-IDF baseline: {dense_passed}/{len(cases)}")
print(f"Hybrid retrieval: {hybrid_passed}/{len(cases)}")
print("Comparison complete.")
