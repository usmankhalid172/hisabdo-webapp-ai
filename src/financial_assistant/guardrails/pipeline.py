"""
Guardrail pipeline: pre-generation checks -> prompt guardrails -> generation ->
sentinel handling -> post-generation citation verification -> fallback routing.

`generate_fn(system_prompt, query, chunks, feedback) -> str` is any callable that
wraps the real LLM (OpenAI, Gemini, local model, ...). It is injected so the
pipeline is testable offline and independent of the provider.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .citation_verifier import Chunk, VerificationResult, verify_citations

_STOP = set("a an the of to in on for and or is are was were be do does did how what when "
            "where which who whom why can could should would i my me you your we our with "
            "at by from as about into".split())
_NUM = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)*)\s*(%|percent|pkr|rs\.?|usd|\$)?", re.I)


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9']+", text.lower()) if t not in _STOP and len(t) > 1}


def _numbers(text: str) -> set:
    out = set()
    for m in _NUM.finditer(text):
        try:
            out.add(float(m.group(1).replace(",", "")))
        except ValueError:
            pass
    return out


@dataclass
class GuardedAnswer:
    text: str
    route: str                 # answered | unanswerable | conflicting | ambiguous | citation_failure | empty_generation
    fallback_used: bool
    llm_called: bool
    regenerations: int = 0
    verification: Optional[VerificationResult] = None
    notes: List[str] = field(default_factory=list)


class GuardrailPipeline:
    def __init__(self, generate_fn: Callable[..., str], config: dict):
        self.generate = generate_fn
        self.cfg = config
        self.fb = config["fallbacks"]
        self.sent = config["prompt_guardrails"]["sentinels"]

    # ------------------------------------------------------ pre-generation
    def _is_unanswerable(self, chunks: List[Chunk]) -> bool:
        rg = self.cfg["retrieval_guardrails"]
        if len(chunks) < rg["min_chunks"]:
            return True
        return max(c.score for c in chunks) < rg["min_top_score"]

    def _find_conflict(self, chunks: List[Chunk]):
        cd = self.cfg["conflict_detection"]
        if not cd["enabled"]:
            return None
        tol = cd["numeric_tolerance_pct"] / 100.0
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                a, b = chunks[i], chunks[j]
                if a.url and a.url == b.url:
                    continue                      # same source, not a cross-source conflict
                ta, tb = _tokens(a.text), _tokens(b.text)
                if not ta or not tb:
                    continue
                overlap = len(ta & tb) / len(ta | tb)
                na, nb = _numbers(a.text), _numbers(b.text)
                if overlap >= cd["min_topic_overlap"] and na and nb:
                    agree = any(abs(x - y) <= tol * max(abs(x), abs(y), 1e-9) for x in na for y in nb)
                    if not agree:
                        return a, b
        return None

    def _ambiguity(self, query: str, chunks: List[Chunk]) -> Optional[str]:
        ad = self.cfg["ambiguity_detection"]
        if not ad["enabled"]:
            return None
        q = _tokens(query)
        raw = re.findall(r"[a-z0-9']+", query.lower())
        vague = set(ad["vague_terms"])
        if len(raw) < ad["min_query_tokens"] or not q:
            return "what exactly do you want to know (e.g. which feature, fee or account)?"
        if q <= vague or (set(raw) & vague and len(q - vague) <= 1):
            return "what does 'it'/'this' refer to?"
        # two near-equal top chunks that are about different topics
        top = sorted(chunks, key=lambda c: c.score, reverse=True)[:2]
        if len(top) == 2 and top[0].title and top[1].title \
                and abs(top[0].score - top[1].score) <= ad["score_gap"]:
            ta, tb = _tokens(top[0].title), _tokens(top[1].title)
            if ta and tb and len(ta & tb) / len(ta | tb) < 0.2:
                return f"do you mean '{top[0].title}' or '{top[1].title}'?"
        return None

    # ---------------------------------------------------------------- run
    def run(self, query: str, chunks: List[Chunk]) -> GuardedAnswer:
        if self._is_unanswerable(chunks):
            return GuardedAnswer(self.fb["unanswerable"], "unanswerable", True, False,
                                 notes=["retrieval below threshold"])
        conflict = self._find_conflict(chunks)
        if conflict:
            a, b = conflict
            srcs = f"[{a.title or a.id}]({a.url or a.id}) vs [{b.title or b.id}]({b.url or b.id})"
            return GuardedAnswer(self.fb["conflicting"].format(sources=srcs),
                                 "conflicting", True, False, notes=["pre-generation numeric conflict"])

        clar = self._ambiguity(query, chunks)
        if clar:
            return GuardedAnswer(self.fb["ambiguous"].format(clarification=clar),
                                 "ambiguous", True, False, notes=["pre-generation ambiguity"])
        cv = self.cfg["citation_verification"]
        system = self.cfg["prompt_guardrails"]["system_prompt"]
        feedback, regen = None, 0
        while True:
            text = (self.generate(system, query, chunks, feedback) or "").strip()
            if not text:
                return GuardedAnswer(self.fb["empty_generation"], "empty_generation", True, True, regen)
            # sentinel routing (model itself signalled)
            if text.startswith(self.sent["unanswerable"]):
                return GuardedAnswer(self.fb["unanswerable"], "unanswerable", True, True, regen,
                                     notes=["model returned INSUFFICIENT_CONTEXT"])
            if text.startswith(self.sent["conflict"]):
                detail = text[len(self.sent["conflict"]):].strip()
                return GuardedAnswer(self.fb["conflicting"].format(sources=detail),
                                     "conflicting", True, True, regen, notes=["model flagged conflict"])
            if text.startswith(self.sent["clarify"]):
                detail = text[len(self.sent["clarify"]):].strip()
                return GuardedAnswer(self.fb["ambiguous"].format(clarification=detail),
                                     "ambiguous", True, True, regen, notes=["model asked to clarify"])

            if not cv["enabled"]:
                return GuardedAnswer(text, "answered", False, True, regen)
            res = verify_citations(text, chunks, cv["title_match_threshold"],
                                   cv["allow_domain_only_match"], cv["index_base"])
            problems = [f"{c.kind} {c.raw!r}: {c.detail}" for c in res.unverified]
            if not res.has_citations and cv["require_citation_when_grounded"]:
                problems.append("answer contains no citations")
            if not problems:
                return GuardedAnswer(text, "answered", False, True, regen, res)
            if regen < cv["max_regenerations"]:
                regen += 1
                feedback = ("Your previous answer had unverifiable citations: "
                            + "; ".join(problems) + ". Cite ONLY exact URLs/titles from CONTEXT.")
                continue
            return GuardedAnswer(self.fb["citation_failure"], "citation_failure", True, True,
                                 regen, res, notes=problems)
