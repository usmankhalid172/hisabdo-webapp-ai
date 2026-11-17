"""Chunk size and overlap experiment for the HisabDo KB, per content type.

Re-chunks the cleaned, source-verified KB (data/kb/approved/kb_chunks.jsonl) in several ways and measures, on the
judged question sets (data/retrieval_eval), how much of the answering text reaches the top-2 context.

  answer coverage  for each answerable question: the share of a judged answering chunk's sentences present in the
                   top-2 retrieved pieces (max over its answering chunks); "hit" = coverage >= 0.5
  noise            share of context characters that come only from chunks judged unrelated to the question
  context          characters sent per question (cost for a real model)

Configurations keep FAQ answers whole (one question, one chunk) and change only sections:
  current      sections <= 1500 chars, no overlap (production)
  s800         sections split to <= 800 chars at paragraph boundaries
  s800_ov      <= 800 + the previous paragraph repeated as overlap
  s500_ov      <= 500 + overlap
  merge2000    consecutive sections of one page merged up to 2000 chars

    python scripts/chunking_experiment.py    -> data/retrieval_eval/results/chunking_experiment.json
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import retrieval_eval as R  # noqa: E402
from src.financial_assistant.grounding.retrieval import (BGE, BGE_QUERY_PREFIX, BM25, HYBRID_ALPHA,  # noqa: E402
                                                          bm25_unit, rewrite)


def content_type(c: dict) -> str:
    if "|---" in c["body"]:
        return "table"
    if c["category"] == "product_faq" or c["heading"].endswith("?"):
        return "faq"
    if c["category"] == "legal_policy":
        return "long_form_policy"
    return "workflow_guide" if c["category"] == "finance_guide" else "product_doc"


def paragraphs(body: str) -> list[str]:
    return [p for p in body.split("\n\n") if p.strip()]


def rechunk(chunks: list[dict], max_chars: int | None, overlap: bool, merge: int | None) -> list[dict]:
    pieces = []
    if merge:
        group: list[dict] = []
        for c in chunks + [None]:
            flush = c is None or (group and (c["source_id"] != group[0]["source_id"] or content_type(c) == "faq"
                                             or sum(len(g["body"]) for g in group) + len(c["body"]) > merge))
            if flush and group:
                pieces.append({"title": group[0]["title"], "heading": group[0]["heading"],
                               "body": "\n\n".join(f"### {g['heading']}\n\n{g['body']}" if i else g["body"]
                                                   for i, g in enumerate(group)),
                               "parents": [g["id"] for g in group], "ctype": content_type(group[0])})
                group = []
            if c is None:
                break
            if content_type(c) == "faq":
                pieces.append({"title": c["title"], "heading": c["heading"], "body": c["body"], "parents": [c["id"]],
                               "ctype": "faq"})
            else:
                group.append(c)
        return pieces
    for c in chunks:
        if content_type(c) == "faq" or max_chars is None or len(c["body"]) <= max_chars:
            pieces.append({"title": c["title"], "heading": c["heading"], "body": c["body"], "parents": [c["id"]],
                           "ctype": content_type(c)})
            continue
        cur, prev_last = [], None
        for p in paragraphs(c["body"]) + [None]:
            if p is None or (cur and sum(len(x) + 2 for x in cur) + len(p) > max_chars):
                if cur:
                    pieces.append({"title": c["title"], "heading": c["heading"], "body": "\n\n".join(cur),
                                   "parents": [c["id"]], "ctype": content_type(c)})
                    prev_last = cur[-1]
                cur = [prev_last] if (overlap and prev_last and p is not None) else []
            if p is not None:
                cur.append(p)
    return pieces


def sentences(text: str) -> list[str]:
    return [s.strip().lower() for s in re.split(r"(?<=[.!?])\s+|\n", re.sub(r"[#*]", "", text)) if len(s.strip()) > 15]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    from fastembed import TextEmbedding
    model = TextEmbedding(BGE)
    chunks = R.load_chunks()
    by_id = {c["id"]: c for c in chunks}
    qrels = R.load_qrels()
    queries = [q for f in ("queries_dev_day1.json", "queries_heldout.json") for q in R.load_queries(f)
               if R.expectation(q, qrels) == "answer"]
    configs = {"current": (None, False, None), "s800": (800, False, None), "s800_ov": (800, True, None),
               "s500_ov": (500, True, None), "merge2000": (None, False, 2000)}
    results = {}
    for name, (mx, ov, mg) in configs.items():
        pieces = rechunk(chunks, mx, ov, mg)
        texts = [f"{p['title']}. {p['heading']}.\n{p['body']}" for p in pieces]
        bm = BM25(texts)
        vec = np.array(list(model.embed(texts)))
        vec = vec / np.linalg.norm(vec, axis=1, keepdims=True)
        per_type, hits, noise, ctx = defaultdict(list), [], [], []
        for q in queries:
            judged = qrels.get(q["id"], {})
            answers = [cid for cid, g in judged.items() if g == 2]
            qt = rewrite(q["text"])
            qv = np.array(list(model.embed([BGE_QUERY_PREFIX + qt])))[0]
            s = HYBRID_ALPHA * (vec @ (qv / np.linalg.norm(qv))) + (1 - HYBRID_ALPHA) * bm25_unit(bm.scores(qt))
            top = [pieces[i] for i in np.argsort(-s)[:2]]
            context = " ".join(sentences(" ".join(p["body"] for p in top)))
            cov = max((sum(1 for x in sentences(by_id[a]["body"]) if x in context) /
                       max(1, len(sentences(by_id[a]["body"]))) for a in answers), default=0.0)
            hits.append(cov >= 0.5)
            unrelated = sum(len(p["body"]) for p in top if all(judged.get(pid, 0) == 0 for pid in p["parents"]))
            total = sum(len(p["body"]) for p in top)
            noise.append(unrelated / total if total else 0)
            ctx.append(total)
            per_type[content_type(by_id[answers[0]])].append(cov >= 0.5)
        lens = [len(p["body"]) for p in pieces]
        results[name] = {"pieces": len(pieces), "median_chars": statistics.median(lens), "max_chars": max(lens),
                         "answer_hit_rate": round(sum(hits) / len(hits), 3), "answerable_questions": len(hits),
                         "noise_share": round(statistics.mean(noise), 3), "context_chars_mean": round(statistics.mean(ctx)),
                         "hit_rate_by_content_type": {k: f"{sum(v)}/{len(v)}" for k, v in sorted(per_type.items())}}
        print(name, results[name], flush=True)
    out = ROOT / "data" / "retrieval_eval" / "results" / "chunking_experiment.json"
    out.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
