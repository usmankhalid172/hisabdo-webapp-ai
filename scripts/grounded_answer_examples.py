"""Produce the examples in docs/grounded-answer-rules.md from the running code (not written by hand).

Sends each question through POST /api/v1/chatbot with grounded answers on, and runs two model drafts through the
citation check. Output: data/retrieval_eval/results/grounded_answer_examples.json

    python scripts/grounded_answer_examples.py [--mode hybrid|lexical]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EXAMPLES = {
    "citation": ["Is HisabDo free to use?", "Does HisabDo work without the internet?",
                 "Kya HisabDo iPhone par chalta hai?", "Does HisabDo use cookies for advertising?",
                 "Can I use HisabDo on two phones at once?"],
    "fallback": ["Does HisabDo have a desktop app for Mac?", "Can HisabDo file my income tax return?",
                 "Write a short poem about the sea."],
    "clarification": ["how?", "backup", "kaise?"],
    "conflict": ["Which currencies does HisabDo support?", "Kya HisabDo AED currency support karta hai?"],
    "known_limits": ["Can I connect HisabDo to my bank account?", "Does HisabDo have a web version?",
                     "Should I register my shop for sales tax?"],
}
DRAFTS = [
    ("Is HisabDo free to use?",
     "HisabDo is free to download and use from Google Play. [2] Tap the Premium button in Settings to unlock "
     "unlimited exports. [1]"),
    ("Is HisabDo free to use?", "Yes, HisabDo Gold costs Rs. 499 per month and includes a desktop version."),
]


class Draft:
    def __init__(self, text):
        self.text = text

    def generate_reply(self, message, context=None, history=None):
        return self.text, 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="hybrid")
    mode = ap.parse_args().mode
    # Same local setup as the test suite (tests/conftest.py): test environment, mock model, local token.
    os.environ.update({"GROUNDED_ANSWERS_ENABLED": "true", "KB_RETRIEVER_MODE": mode, "APP_ENV": "test",
                       "LLM_PROVIDER": "mock",
                       "INTERNAL_SERVICE_TOKEN": os.environ.get("INTERNAL_SERVICE_TOKEN", "examples-local-token")})
    from fastapi.testclient import TestClient
    from src.config import get_settings
    from src.financial_assistant import service
    from src.main import app
    get_settings.cache_clear()
    client = TestClient(app)
    headers = {"X-Internal-Token": os.environ["INTERNAL_SERVICE_TOKEN"]}
    out = {"mode": mode, "endpoint": {}, "model_drafts": []}
    for kind, questions in EXAMPLES.items():
        out["endpoint"][kind] = []
        for n, q in enumerate(questions):
            r = client.post("/api/v1/chatbot", headers=headers,
                            json={"user_id": "examples", "message": q, "conversation_id": f"{kind}-{n}"}).json()
            out["endpoint"][kind].append({k: r.get(k) for k in ("reply", "answer_status", "source", "needs_review",
                                                                "citations", "intent")} | {"question": q})
    answerer = service.get_grounded_answerer()
    for q, text in DRAFTS:
        a = answerer.answer(q, provider=Draft(text))
        out["model_drafts"].append({"question": q, "draft": text, "status": a.status, "reply": a.reply})
    path = ROOT / "data" / "retrieval_eval" / "results" / "grounded_answer_examples.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    for kind, rows in out["endpoint"].items():
        for r in rows:
            print(f"### [{kind}] {r['question']}  ->  {r['answer_status']} / {r['source']} / review={r['needs_review']}")
            print(r["reply"], "\n")
    for d in out["model_drafts"]:
        print(f"### [draft] {d['draft']}\n  -> {d['status']}\n{d['reply']}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
