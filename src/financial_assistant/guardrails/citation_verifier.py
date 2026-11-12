"""
Citation Verification Script
----------------------------
Post-generation check: every URL / title / numeric reference cited in an LLM
answer must exist in the retrieved context chunks that were given to the model.

Usable as a library or CLI:
    python -m financial_assistant.guardrails.citation_verifier \
        --answer answer.txt --chunks chunks.json [--config config/guardrail_config.json]

chunks.json: [{"id": "c1", "url": "https://...", "title": "...", "text": "..."}]
Exit code: 0 = all citations verified, 1 = at least one unverified, 2 = usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from difflib import SequenceMatcher
from typing import Iterable, List, Optional
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term",
                   "utm_content", "gclid", "fbclid", "ref", "ref_src"}


# ---------------------------------------------------------------- data model
@dataclass
class Chunk:
    id: str
    text: str = ""
    url: Optional[str] = None
    title: Optional[str] = None
    score: float = 1.0           # retrieval similarity (0..1)


@dataclass
class Citation:
    raw: str                     # text as it appeared in the answer
    kind: str                    # url | title | index
    value: str                   # normalized value that is checked
    status: str = "pending"      # verified | unverified | out_of_range
    matched_chunk: Optional[str] = None
    detail: str = ""


@dataclass
class VerificationResult:
    citations: List[Citation] = field(default_factory=list)

    @property
    def verified(self) -> List[Citation]:
        return [c for c in self.citations if c.status == "verified"]

    @property
    def unverified(self) -> List[Citation]:
        return [c for c in self.citations if c.status != "verified"]

    @property
    def ok(self) -> bool:
        return not self.unverified

    @property
    def has_citations(self) -> bool:
        return bool(self.citations)

    def to_dict(self) -> dict:
        return {"ok": self.ok, "total": len(self.citations),
                "verified": len(self.verified), "unverified": len(self.unverified),
                "citations": [asdict(c) for c in self.citations]}


# ------------------------------------------------------------- normalization
def normalize_url(url: str) -> str:
    """Canonical form: https, lowercase host, no www, no fragment,
    no tracking params, no trailing slash, sorted query."""
    url = url.strip().rstrip(".,;:!?)]}>\"'")
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    try:
        port = f":{p.port}" if p.port and p.port not in (80, 443) else ""
    except ValueError:
        port = ""
    path = re.sub(r"/{2,}", "/", p.path).rstrip("/")
    q = sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True)
               if k.lower() not in TRACKING_PARAMS)
    return urlunsplit(("https", host + port, path, urlencode(q), ""))


def normalize_title(title: str) -> str:
    t = re.sub(r"[\u2018\u2019\u201c\u201d]", "'", title)
    t = re.sub(r"[^\w\s']", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------- extraction
_MD_LINK = re.compile(r"\[([^\]\n]{1,300})\]\((https?://[^)\s]+)(?:\s+\"[^\"]*\")?\)")
_BARE_URL = re.compile(
    r"https?://[^\s<>\"')\]]+|(?<![\w/@.])(?:www\.)[\w.-]+\.[a-z]{2,}(?:/[^\s<>\"')\]]*)?", re.I)
_SOURCE_TAG = re.compile(r"\[(?:source|sources|ref|citation|doc)\s*:\s*([^\]\n]{2,300})\]", re.I)
_QUOTED_TITLE = re.compile(
    r"(?:according to|per|source:|see|from)\s+[\"\u201c]([^\"\u201d\n]{3,200})[\"\u201d]", re.I)
_NUMERIC = re.compile(r"\[(\d{1,3}(?:\s*[,\-\u2013]\s*\d{1,3})*)\](?!\()")
_CODE_FENCE = re.compile(r"```.*?```", re.S)


def _expand_numeric(group: str) -> List[int]:
    nums: List[int] = []
    for part in re.split(r"\s*,\s*", group):
        m = re.match(r"^(\d+)\s*[\-\u2013]\s*(\d+)$", part)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            nums.extend(range(a, min(b, a + 50) + 1))
        elif part.strip().isdigit():
            nums.append(int(part))
    return nums


def extract_citations(answer: str) -> List[Citation]:
    """Pull every citation-like reference out of the answer."""
    text = _CODE_FENCE.sub(" ", answer)
    out: List[Citation] = []
    seen = set()

    def add(c: Citation):
        key = (c.kind, c.value)
        if key not in seen:
            seen.add(key)
            out.append(c)

    consumed = []
    for m in _MD_LINK.finditer(text):
        label, url = m.group(1), m.group(2)
        add(Citation(raw=m.group(0), kind="url", value=normalize_url(url)))
        # link label is anchor text; the URL is the identifier that gets verified
        consumed.append(m.span())

    def free(span):
        return not any(a <= span[0] < b for a, b in consumed)

    for m in _BARE_URL.finditer(text):
        if free(m.span()):
            add(Citation(raw=m.group(0), kind="url", value=normalize_url(m.group(0))))
    for m in _SOURCE_TAG.finditer(text):
        for t in re.split(r"\s*;\s*", m.group(1)):
            if t.strip():
                if re.match(r"^(https?://|www\.)", t.strip(), re.I):
                    add(Citation(raw=t, kind="url", value=normalize_url(t)))
                else:
                    add(Citation(raw=t.strip(), kind="title", value=normalize_title(t)))
    for m in _QUOTED_TITLE.finditer(text):
        add(Citation(raw=m.group(1), kind="title", value=normalize_title(m.group(1))))
    for m in _NUMERIC.finditer(text):
        for n in _expand_numeric(m.group(1)):
            add(Citation(raw=f"[{n}]", kind="index", value=str(n)))
    return out


# -------------------------------------------------------------- verification
def _title_match(value: str, chunk_titles: Iterable[tuple], threshold: float):
    best = (0.0, None)
    for cid, t in chunk_titles:
        nt = normalize_title(t)
        if not nt:
            continue
        r = 1.0 if nt == value else SequenceMatcher(None, value, nt).ratio()
        if r > best[0]:
            best = (r, cid)
    return best if best[0] >= threshold else (best[0], None)


def verify_citations(answer: str, chunks: List[Chunk],
                     title_threshold: float = 0.90,
                     allow_domain_only: bool = False,
                     index_base: int = 1) -> VerificationResult:
    """Check each extracted citation against the retrieved chunks.

    * url   -> normalized URL must equal a chunk URL (bare domain allowed if configured)
    * title -> normalized title must fuzzy-match a chunk title (>= title_threshold)
    * index -> [n] must be within 1..len(chunks)
    """
    res = VerificationResult(extract_citations(answer))
    url_map = {normalize_url(c.url): c.id for c in chunks if c.url}
    dom_map = {urlsplit(u).hostname: cid for u, cid in url_map.items()}
    titles = [(c.id, c.title) for c in chunks if c.title]
    n = len(chunks)

    for c in res.citations:
        if c.kind == "url":
            host, path = urlsplit(c.value).hostname, urlsplit(c.value).path
            if c.value in url_map:
                c.status, c.matched_chunk = "verified", url_map[c.value]
            elif allow_domain_only and host in dom_map and not path:
                c.status, c.matched_chunk = "verified", dom_map[host]
                c.detail = "domain-only match"
            else:
                c.status, c.detail = "unverified", "URL not present in retrieved chunks"
        elif c.kind == "title":
            score, cid = _title_match(c.value, titles, title_threshold)
            if cid:
                c.status, c.matched_chunk, c.detail = "verified", cid, f"title similarity {score:.2f}"
            else:
                c.status = "unverified"
                c.detail = f"no chunk title >= {title_threshold:.2f} (best {score:.2f})"
        elif c.kind == "index":
            i = int(c.value) - index_base
            if 0 <= i < n:
                c.status, c.matched_chunk = "verified", chunks[i].id
            else:
                c.status = "out_of_range"
                c.detail = f"index {c.value} outside 1..{n}"
    return res


# ----------------------------------------------------------------------- CLI
def _main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--answer", required=True, help="path to LLM answer text")
    ap.add_argument("--chunks", required=True, help="path to retrieved chunks JSON")
    ap.add_argument("--config", help="guardrail_config.json (optional)")
    ap.add_argument("--json", action="store_true", help="emit JSON report")
    a = ap.parse_args(argv)
    try:
        with open(a.answer, encoding="utf-8") as f:
            answer = f.read()
        with open(a.chunks, encoding="utf-8") as f:
            chunks = [Chunk(**c) for c in json.load(f)]
        cfg = {}
        if a.config:
            with open(a.config, encoding="utf-8") as f:
                cfg = json.load(f)
    except (OSError, ValueError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    cv = cfg.get("citation_verification", {})
    r = verify_citations(answer, chunks, cv.get("title_match_threshold", 0.90),
                         cv.get("allow_domain_only_match", False),
                         cv.get("index_base", 1))
    if a.json:
        print(json.dumps(r.to_dict(), indent=2))
    else:
        for c in r.citations:
            print(f"[{c.status.upper():12}] {c.kind:5} {c.raw[:70]!r} -> "
                  f"{c.matched_chunk or '-'} {c.detail}")
        print(f"\n{len(r.verified)}/{len(r.citations)} verified ->", "PASS" if r.ok else "FAIL")
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(_main())
