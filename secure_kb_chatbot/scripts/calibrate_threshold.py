"""Pick the relevance threshold from evidence instead of guessing.

    python scripts/calibrate_threshold.py kb/eval_questions.json

The file lists test questions and what each SHOULD retrieve:

    [{"question": "How do I record an expense?", "expect": "KB-001"},
     {"question": "Give me a biryani recipe",     "expect": null}]

"expect": null means the KB must NOT answer it. The script scores every question
against the live KB version and suggests the threshold that best separates the
two groups. Needs GEMINI_API_KEY.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatbot.config import Settings  # noqa: E402
from chatbot.embeddings import Embedder, GeminiEmbedder  # noqa: E402
from chatbot.repository import Repository  # noqa: E402
from chatbot.vector_store import VectorStore  # noqa: E402


def score_questions(store: VectorStore, embedder: Embedder, questions: list[dict]) -> list[dict]:
    rows = []
    for q in questions:
        hits = store.search(embedder.embed_query(q["question"]), 1)
        top_id, score = (hits[0][0].entry_id, hits[0][1]) if hits else (None, 0.0)
        rows.append({"question": q["question"], "expect": q.get("expect"), "top": top_id, "score": score})
    return rows


def evaluate(rows: list[dict], threshold: float) -> dict:
    """How the chatbot would behave at this threshold."""
    correct = wrong_source = missed = false_answer = 0
    for r in rows:
        answered = r["score"] >= threshold
        if r["expect"] is None:
            false_answer += answered  # answered something it should have refused
            correct += not answered
        elif not answered:
            missed += 1  # had the answer but said "I don't know"
        elif r["top"] == r["expect"]:
            correct += 1
        else:
            wrong_source += 1  # answered from the wrong entry
    return {"threshold": round(threshold, 3), "correct": correct, "total": len(rows), "missed": missed,
            "false_answers": false_answer, "wrong_source": wrong_source}


def suggest(rows: list[dict]) -> dict:
    """Try every candidate threshold; prefer fewer false answers, then more correct."""
    candidates = sorted({round(r["score"], 3) for r in rows} | {0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8})
    results = [evaluate(rows, t) for t in candidates]
    return max(results, key=lambda r: (-r["false_answers"], r["correct"], r["threshold"]))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    questions = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    settings = Settings.from_env()
    store = VectorStore(Repository(os.environ.get("CHATBOT_DB", ROOT / "data" / "app.db")))
    if store.active_version() is None:
        print("ERROR: no live KB version. Run scripts/build_kb_index.py kb/v1 --activate first.")
        return 1
    rows = score_questions(store, GeminiEmbedder(settings.embedding_model, settings.embedding_dim), questions)

    print(f"{'score':>6}  {'expected':9} {'top hit':9} question")
    for r in sorted(rows, key=lambda r: -r["score"]):
        print(f"{r['score']:6.3f}  {str(r['expect']):9} {str(r['top']):9} {r['question'][:70]}")
    now, best = evaluate(rows, settings.kb_threshold), suggest(rows)
    print(f"\nCurrent  KB_THRESHOLD={now['threshold']}: {now['correct']}/{now['total']} correct, "
          f"{now['false_answers']} false answers, {now['missed']} missed, {now['wrong_source']} wrong source")
    print(f"Suggested KB_THRESHOLD={best['threshold']}: {best['correct']}/{best['total']} correct, "
          f"{best['false_answers']} false answers, {best['missed']} missed, {best['wrong_source']} wrong source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
