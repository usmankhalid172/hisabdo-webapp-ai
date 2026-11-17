"""Verified example transcripts for the Department 3 Grounded Prompt & Response Rulebook.

Every scenario runs through the real code and is then checked automatically; a transcript is "verified" only when all
of its checks pass:
  status      the reply kind is the expected one (answered / conflict / clarify / no_source / out_of_scope)
  citations   every citation is a KB passage, with that passage's own link and title, and its [n] appears in the reply
  links       every link in the reply belongs to a cited source (or is the official support contact page)
  support     every sentence carrying [n] is supported by passage n (>= 50% of its content words, rule R4)
  sources     cited passages are among those judged correct for the question (when a judgment is given)
  forbidden   invented text from a scripted model draft does not reach the user

Sections A, C, D and E go through the full API (POST /api/v1/chatbot, grounded answers on, hybrid retriever, mock
model). Section B uses a scripted "real model" draft to show the citation checks; F uses a synthetic dated conflict to
show deterministic resolution (the live KB has no dated conflict).

    python scripts/grounded_transcripts.py   -> data/dept3_grounded/transcripts.json and docs/dept3-grounded-transcripts.md
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("INTERNAL_SERVICE_TOKEN", "transcript-token")
os.environ.setdefault("APP_ENV", "test")
os.environ["LLM_PROVIDER"] = "mock"
os.environ["GROUNDED_ANSWERS_ENABLED"] = "true"
os.environ["KB_RETRIEVER_MODE"] = "hybrid"

from fastapi.testclient import TestClient  # noqa: E402

from src.financial_assistant.grounding import GroundedAnswerer, KbRetriever  # noqa: E402
from src.financial_assistant.grounding.answer import URL, CONTACT_URL, support  # noqa: E402
from src.financial_assistant.grounding.retrieval import load_kb, to_passage  # noqa: E402
from src.main import app  # noqa: E402

OUT = ROOT / "data" / "dept3_grounded"
DOC = ROOT / "docs" / "dept3-grounded-transcripts.md"

API = [  # (section, id, message, expected status, judged-correct chunk prefixes or None)
    ("A Standard grounded answer", "A1", "Is HisabDo free to use?", "answered", ["off-01-002"]),
    ("A Standard grounded answer", "A2", "Can I export PDF reports?", "answered",
     ["off-01-013", "off-03-009", "blog-07-007"]),
    ("A Standard grounded answer", "A3", "What happens to my data if I uninstall the app?", "answered", ["off-01-023"]),
    ("A Standard grounded answer", "A4", "Does HisabDo work without the internet?", "answered",
     ["off-01-008", "blog-16-012", "blog-06-017"]),
    ("A Standard grounded answer", "A5", "What is the difference between fixed and variable expenses?", "answered",
     ["blog-04-003"]),
    ("A Standard grounded answer", "A6", "Does HisabDo share my financial data with third parties?", "answered",
     ["off-01-025", "off-06-"]),
    ("C Source conflict", "C1", "Which currencies does HisabDo support?", "conflict",
     ["off-01-019", "off-04-010", "off-02-010"]),
    ("D Ambiguity", "D1", "expenses", "clarify", None),
    ("D Ambiguity", "D2", "kharcha", "clarify", None),
    ("D Ambiguity", "D3", "how?", "clarify", None),
    ("D Ambiguity", "D4", "kaise?", "clarify", None),
    ("E No-answer fallback", "E1", "Can I connect HisabDo to my bank account?", "no_source|out_of_scope", None),
    ("E No-answer fallback", "E2", "How do I export my expenses to Excel?", "answered|no_source",
     ["off-03-009", "off-01-013", "blog-07-007"]),
    ("E No-answer fallback", "E3", "Can two staff members record expenses on the same account?",
     "no_source|out_of_scope", None),
    ("E No-answer fallback", "E4", "Can HisabDo file my FBR tax return?", "no_source|out_of_scope", None),
]


class ScriptedModel:
    """Stands in for a real model provider: returns a fixed draft for the answer checks to work on."""

    def __init__(self, draft: str):
        self.draft = draft

    def generate_reply(self, message, context=None, history=None):
        return self.draft, 0


MODEL = [  # (id, message, draft, expected status, judged prefixes, strings that must not reach the user)
    ("B1", "Is HisabDo free to use?",
     "HisabDo is free to download and use from Google Play [1]. Core features including PDF export and backup are "
     "available at no cost [1].", "answered", ["off-01-002"], []),
    ("B2", "Is HisabDo free to use?",
     "HisabDo is free to download and use from Google Play [2]. Premium unlocks unlimited exports for Rs. 499 a month "
     "[1]. See https://hisabdo.app/pricing-plans for details.", "answered", ["off-01-002"],
     ["Premium", "499", "pricing-plans"]),
    ("B3", "Is HisabDo free to use?",
     "HisabDo Gold costs Rs. 499 per month and includes a desktop version. Download it at https://hisabdo.example.com.",
     "no_source", None, ["Gold", "499", "hisabdo.example.com"]),
]


def check(ans: dict, expected: str, judged: list[str] | None, kb: dict, forbidden: list[str]) -> dict:
    reply = ans["reply"]
    body = reply.split("\n\nSources:")[0].split("\n\nذرائع:")[0]
    cites = ans["citations"]
    checks = {"status": ans["answer_status"] in expected.split("|")}
    checks["citations"] = all(c["chunk_id"] in kb and c["url"] == kb[c["chunk_id"]].source_url
                              and c.get("label", c.get("title")) == kb[c["chunk_id"]].label and f"[{c['n']}]" in body for c in cites)
    urls = {c["url"].rstrip("/") for c in cites} | {CONTACT_URL}
    checks["links"] = all(u.rstrip("/.") in urls for u in URL.findall(reply))
    sup = True
    by_n = {c["n"]: kb[c["chunk_id"]] for c in cites if c["chunk_id"] in kb}
    for s in re.split(r"(?<=[.!?\]])\s+|\n", body):
        for n in map(int, re.findall(r"\[(\d+)\]", s)):
            text = re.sub(r"^\[\d+\][^:]*:\s*", "", s)   # a conflict line starts "[n] Page › Section (date):"
            text = re.sub(r"^[^:]*says[^:]*:\s*|^I found this[^:]*:\s*", "", text)
            if n in by_n and support(text, by_n[n]) < 0.5:
                sup = False
    checks["support"] = sup
    checks["sources"] = judged is None or all(any(c["chunk_id"].startswith(j) for j in judged) for c in cites)
    checks["forbidden"] = not any(f in reply for f in forbidden)
    return checks


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    kb = {c["id"]: to_passage(c) for c in load_kb()}
    client = TestClient(app)
    headers = {"X-Internal-Token": os.environ["INTERNAL_SERVICE_TOKEN"]}
    rows = []
    for section, tid, msg, expected, judged in API:
        r = client.post("/api/v1/chatbot", headers=headers,
                        json={"user_id": "transcript-user", "message": msg, "conversation_id": f"t-{tid}"})
        r.raise_for_status()
        a = r.json()
        rows.append({"section": section, "id": tid, "path": "API /api/v1/chatbot (mock model)", "user": msg,
                     "assistant": a["reply"], "answer_status": a["answer_status"], "source": a["source"],
                     "needs_review": a.get("needs_review"), "citations": a["citations"],
                     "checks": check(a, expected, judged, kb, ["CSV", "Excel file", "export to Excel"])})

    answerer = GroundedAnswerer(KbRetriever(mode="hybrid"))
    for tid, msg, draft, expected, judged, forbidden in MODEL:
        g = answerer.answer(msg, provider=ScriptedModel(draft))
        a = {"reply": g.reply, "answer_status": g.status, "citations": [c.__dict__ for c in g.citations]}
        rows.append({"section": "B Citations (model draft checked)", "id": tid, "path": "GroundedAnswerer + scripted "
                     "model draft", "user": msg, "model_draft": draft, "assistant": g.reply, "answer_status": g.status,
                     "citations": a["citations"], "checks": check(a, expected, judged, kb, forbidden)})

    # F: deterministic resolution on a synthetic, dated conflict (FAQ newer than the feature page)
    chunks = [c for c in load_kb() if c["id"].startswith(("off-01-019", "off-04-010"))]
    dated = []
    for c in chunks:
        d = dict(c, status="needs_confirmation", notes=["synthetic: supported currencies"])
        d["last_updated"] = "2026-11-01" if c["id"].startswith("off-01-019") else "2026-06-01"
        dated.append(d)

    class Fixed:
        mode, version, chunks = "fixed", "synthetic", dated

        def retrieve(self, message, top_k=None):
            return [to_passage(d, 0.9) for d in dated]

    g = GroundedAnswerer(Fixed(), kb_chunks=dated).answer("Which currencies does HisabDo support?")
    kb_f = {**kb, **{d["id"]: to_passage(d) for d in dated}}
    a = {"reply": g.reply, "answer_status": g.status, "citations": [c.__dict__ for c in g.citations]}
    rows.append({"section": "F Conflict resolved deterministically (synthetic dates)", "id": "F1",
                 "path": "GroundedAnswerer, synthetic KB: FAQ dated 2026-11-01, feature page dated 2026-06-01",
                 "user": "Which currencies does HisabDo support?", "assistant": g.reply, "answer_status": g.status,
                 "needs_review": g.needs_review, "citations": a["citations"],
                 "checks": check(a, "answered", ["off-01-019", "off-04-010"], kb_f, [])})

    for r in rows:
        r["verified"] = all(r["checks"].values())
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"transcripts": len(rows), "verified": sum(r["verified"] for r in rows)}
    (OUT / "transcripts.json").write_text(json.dumps({**summary, "rows": rows}, indent=1, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    md = ["# Department 3 Grounded Answers: Verified Example Transcripts", "",
          "Generated by `scripts/grounded_transcripts.py` (do not edit by hand). "
          f"**{summary['verified']}/{summary['transcripts']} verified.** "
          "Checks: status, citations, links, support, sources, forbidden (see the script).", ""]
    section = None
    for r in rows:
        if r["section"] != section:
            section = r["section"]
            md += [f"## {section}", ""]
        mark = "✅ verified" if r["verified"] else "❌ " + ", ".join(k for k, v in r["checks"].items() if not v)
        md += [f"### {r['id']} · `{r['answer_status']}` · {mark}", "", f"*Path: {r['path']}*", "",
               f"**User:** {r['user']}", ""]
        if r.get("model_draft"):
            md += ["**Model draft (before checks):**", "", "> " + r["model_draft"], ""]
        md += ["**Assistant:**", "", "```text", r["assistant"], "```", ""]
    DOC.write_text("\n".join(md) + "\n", encoding="utf-8")
    for r in rows:
        print(r["id"], r["answer_status"], "OK" if r["verified"] else r["checks"])
    print(summary)
    return 0 if summary["verified"] == summary["transcripts"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
