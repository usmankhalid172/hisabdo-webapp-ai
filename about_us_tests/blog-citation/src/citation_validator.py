"""
Citation Validator for Blog & News Grounded Generation
======================================================
Validates that every [n] marker in a grounded response complies with the
citation contract defined in blog-grounded-prompt-rules.md.

Four integrity checks:
  CHECK 1 — Orphan marker:     every [n] in body has a Sources entry
  CHECK 2 — Padded source:     every Sources entry has a [n] in body
  CHECK 3 — Fabricated index:  every cited index <= len(retrieved_articles)
  CHECK 4 — URL allowlist:     every URL in Sources matches the blog URL regex

Optional verbatim-quote check (CHECK 5):
  If the response wraps text in straight double quotes "..." and attributes
  it to [n], the quoted text must appear (case-insensitive, whitespace
  normalised) inside the body of retrieved_articles[n-1].

API:
    from src.citation_validator import validate_citations
    report = validate_citations(response, retrieved_articles)
    print(report["overall_pass"], report["errors"])

The function is pure: it takes a response string + list of retrieved article
dicts and returns a structured report. It does NOT call the retriever or LLM.
"""

import re
from typing import Dict, List, Any

# Blog URL allowlist (mirrors src/utils.py BLOG_URL_PATTERN)
BLOG_URL_PATTERN = re.compile(
    r'^https://www\.xicteksystems\.com/blog/[a-z0-9-]+$'
)


# ============================================================
# PARSING HELPERS
# ============================================================
def _split_sources_block(response: str) -> (str, str):
    """Split a response into (body, sources_block_text).

    The Sources block starts at the first line beginning with 'Sources:'
    or '**Sources:**' (case-insensitive). If no such marker is found, the
    sources block is empty (which will be flagged by CHECK 1).
    """
    # Match either "**Sources:**" or "Sources:" at start of a line
    pattern = re.compile(r'^\*?\*?Sources:?\*?\*?\s*$', re.IGNORECASE | re.MULTILINE)
    m = pattern.search(response)
    if not m:
        return response, ""
    body = response[:m.start()].rstrip()
    sources_block = response[m.end():]
    return body, sources_block


def _extract_markers(text: str) -> List[int]:
    """Extract all [n] markers from a text. Returns sorted unique list of ints."""
    matches = re.findall(r'\[(\d+)\]', text)
    return sorted(set(int(n) for n in matches))


def _extract_markers_with_count(text: str) -> Dict[int, int]:
    """Extract [n] markers and their occurrence count from text."""
    counts: Dict[int, int] = {}
    for n in re.findall(r'\[(\d+)\]', text):
        idx = int(n)
        counts[idx] = counts.get(idx, 0) + 1
    return counts


def _parse_sources_entries(sources_block: str) -> List[Dict[str, Any]]:
    """Parse Sources block into list of {index, title, url, section, raw}.

    Accepts entries of the form:
        [n] Title — URL
        [n] Title — § "Section" — URL
        [n] Title - URL        (hyphen instead of em-dash)
        [n] [Title](URL)        (markdown link form)
    """
    if not sources_block.strip():
        return []

    entries = []
    # Each entry starts with [n]
    entry_pattern = re.compile(
        r'^\s*\[(\d+)\]\s*(.+)$',
        re.MULTILINE
    )
    for m in entry_pattern.finditer(sources_block):
        idx = int(m.group(1))
        rest = m.group(2).strip()

        # Try markdown-link form: [Title](URL)
        md_link = re.match(r'\[([^\]]+)\]\(([^)]+)\)', rest)
        if md_link:
            entries.append({
                "index": idx,
                "title": md_link.group(1).strip(),
                "url": md_link.group(2).strip(),
                "section": None,
                "raw": m.group(0).strip(),
            })
            continue

        # Try § "Section" form: Title — § "Section" — URL
        section_match = re.match(
            r'(.+?)\s*[—-]\s*§\s*"([^"]+)"\s*[—-]\s*(https?://\S+)',
            rest
        )
        if section_match:
            entries.append({
                "index": idx,
                "title": section_match.group(1).strip(),
                "url": section_match.group(3).strip(),
                "section": section_match.group(2).strip(),
                "raw": m.group(0).strip(),
            })
            continue

        # Default form: Title — URL
        default_match = re.match(r'(.+?)\s*[—-]\s*(https?://\S+)', rest)
        if default_match:
            entries.append({
                "index": idx,
                "title": default_match.group(1).strip(),
                "url": default_match.group(2).strip(),
                "section": None,
                "raw": m.group(0).strip(),
            })
            continue

        # Fallback — entry exists but URL is missing or malformed
        entries.append({
            "index": idx,
            "title": rest,
            "url": None,
            "section": None,
            "raw": m.group(0).strip(),
        })
    return entries


def _normalize_whitespace(text: str) -> str:
    """Collapse whitespace for fuzzy string comparison."""
    return re.sub(r'\s+', ' ', text).strip().lower()


def _extract_verbatim_quotes(body: str) -> List[Dict[str, Any]]:
    """Extract double-quoted spans from body that are immediately followed
    by [n] (within 5 chars, allowing trailing punctuation).

    Returns list of {quote, marker}.
    """
    quotes = []
    # Match "..." optionally followed by space/punctuation then [n]
    pattern = re.compile(r'"([^"\n]{8,400}?)"\s*[\s.,;:]*\[(\d+)\]')
    for m in pattern.finditer(body):
        quotes.append({
            "quote": m.group(1).strip(),
            "marker": int(m.group(2)),
        })
    return quotes


# ============================================================
# MAIN VALIDATOR
# ============================================================
def validate_citations(response: str,
                       retrieved_articles: List[Dict[str, Any]],
                       check_verbatim: bool = True) -> Dict[str, Any]:
    """Validate a grounded response against the citation contract.

    Args:
        response: the full LLM response string, including Sources block.
        retrieved_articles: list of article dicts (must have 'slug',
            'title', 'body' keys). Order matches the [n] indices —
            article [1] is retrieved_articles[0].
        check_verbatim: if True, run CHECK 5 (verbatim-quote grounding).

    Returns:
        {
          "overall_pass": bool,
          "checks": {
            "check_1_orphan_markers":   {passed, ...details},
            "check_2_padded_sources":   {passed, ...details},
            "check_3_fabricated_index": {passed, ...details},
            "check_4_url_allowlist":    {passed, ...details},
            "check_5_verbatim_quotes":  {passed, ...details},  # optional
          },
          "markers_in_body": [int, ...],
          "sources_entries": [{index, title, url, ...}, ...],
          "errors": [str, ...],
          "warnings": [str, ...],
        }
    """
    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, Dict[str, Any]] = {}

    body, sources_block = _split_sources_block(response)
    markers_in_body = _extract_markers(body)
    sources_entries = _parse_sources_entries(sources_block)
    source_indices = sorted(set(e["index"] for e in sources_entries))
    body_marker_counts = _extract_markers_with_count(body)

    # ---- CHECK 1: orphan markers (every [n] in body must be in Sources) ----
    orphan_markers = [n for n in markers_in_body if n not in source_indices]
    checks["check_1_orphan_markers"] = {
        "passed": len(orphan_markers) == 0,
        "rule": "Every [n] marker in body must have a matching Sources entry.",
        "markers_in_body": markers_in_body,
        "source_indices": source_indices,
        "orphan_markers": orphan_markers,
    }
    if orphan_markers:
        errors.append(
            f"CHECK 1 FAIL — markers {orphan_markers} appear in body but have "
            f"no Sources entry (orphan citations)."
        )

    # ---- CHECK 2: padded sources (every Sources entry must have a [n] in body) ----
    padded_sources = [n for n in source_indices if n not in markers_in_body]
    checks["check_2_padded_sources"] = {
        "passed": len(padded_sources) == 0,
        "rule": "Every Sources entry must have at least one [n] marker in body.",
        "source_indices": source_indices,
        "markers_in_body": markers_in_body,
        "padded_sources": padded_sources,
    }
    if padded_sources:
        errors.append(
            f"CHECK 2 FAIL — Sources entries {padded_sources} are listed but "
            f"never cited in body (padding the Sources list)."
        )

    # ---- CHECK 3: fabricated index (every cited index <= len(retrieved)) ----
    n_retrieved = len(retrieved_articles)
    all_cited = sorted(set(markers_in_body + source_indices))
    fabricated = [n for n in all_cited if n < 1 or n > n_retrieved]
    checks["check_3_fabricated_index"] = {
        "passed": len(fabricated) == 0,
        "rule": f"Every cited index must be 1..{n_retrieved} (the retrieved set).",
        "n_retrieved": n_retrieved,
        "all_cited_indices": all_cited,
        "fabricated_indices": fabricated,
    }
    if fabricated:
        errors.append(
            f"CHECK 3 FAIL — indices {fabricated} are cited but only "
            f"{n_retrieved} articles were retrieved (fabricated citations)."
        )

    # ---- CHECK 4: URL allowlist ----
    bad_urls = []
    for entry in sources_entries:
        url = entry.get("url")
        if url is None:
            bad_urls.append({"index": entry["index"], "url": None,
                             "reason": "missing URL"})
            continue
        clean = url.rstrip('.,;:')
        if not BLOG_URL_PATTERN.match(clean):
            bad_urls.append({"index": entry["index"], "url": url,
                             "reason": "not on /blog/ allowlist"})
    checks["check_4_url_allowlist"] = {
        "passed": len(bad_urls) == 0,
        "rule": "Every Sources URL must match ^https://www.xicteksystems.com/blog/[a-z0-9-]+$",
        "checked_urls": [e.get("url") for e in sources_entries],
        "violations": bad_urls,
    }
    if bad_urls:
        errors.append(
            f"CHECK 4 FAIL — {len(bad_urls)} URL(s) failed the blog allowlist: {bad_urls}"
        )

    # ---- CHECK 5: verbatim quote grounding (optional) ----
    if check_verbatim:
        quotes = _extract_verbatim_quotes(body)
        ungrounded_quotes = []
        for q in quotes:
            marker = q["marker"]
            if marker < 1 or marker > n_retrieved:
                ungrounded_quotes.append({
                    "quote": q["quote"][:80],
                    "marker": marker,
                    "reason": f"marker [{marker}] out of retrieved range",
                })
                continue
            article_body = retrieved_articles[marker - 1].get("body", "")
            if _normalize_whitespace(q["quote"]) not in _normalize_whitespace(article_body):
                ungrounded_quotes.append({
                    "quote": q["quote"][:80],
                    "marker": marker,
                    "reason": f"quote not found in article [{marker}] body",
                })
        checks["check_5_verbatim_quotes"] = {
            "passed": len(ungrounded_quotes) == 0,
            "rule": "Every \"...\"[n] verbatim quote must appear in article [n]'s body.",
            "quotes_found": len(quotes),
            "ungrounded": ungrounded_quotes,
        }
        if ungrounded_quotes:
            errors.append(
                f"CHECK 5 FAIL — {len(ungrounded_quotes)} verbatim quote(s) not "
                f"grounded in cited article body."
            )
        if not quotes:
            warnings.append(
                "CHECK 5 — no verbatim quotes detected in body "
                "(informational; not a failure)."
            )

    # ---- cross-check: title match (warning, not failure) ----
    for entry in sources_entries:
        idx = entry["index"]
        if 1 <= idx <= n_retrieved:
            actual_title = retrieved_articles[idx - 1].get("title", "")
            listed_title = entry.get("title", "")
            if (actual_title and listed_title
                    and _normalize_whitespace(actual_title)
                        != _normalize_whitespace(listed_title)):
                # Loose substring check — listed title may be a shortened form
                if (_normalize_whitespace(listed_title)
                        not in _normalize_whitespace(actual_title)
                    and _normalize_whitespace(actual_title)
                        not in _normalize_whitespace(listed_title)):
                    warnings.append(
                        f"Title mismatch for [{idx}]: Sources says "
                        f"\"{listed_title}\", retrieved article title is "
                        f"\"{actual_title}\"."
                    )

    overall_pass = all(c["passed"] for c in checks.values())
    return {
        "overall_pass": overall_pass,
        "checks": checks,
        "markers_in_body": markers_in_body,
        "sources_entries": sources_entries,
        "errors": errors,
        "warnings": warnings,
    }


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    # Demo run against the simulated LLM response from grounded_generation.py
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from src.grounded_generation import generate_grounded_response

    print("=" * 70)
    print("CITATION VALIDATOR — DEMO RUN")
    print("=" * 70)
    print()

    demo_queries = [
        "how much does custom software cost in pakistan",
        "what is the agile software development process",
        "tell me about ai chatbot development",
    ]

    all_pass = True
    for q in demo_queries:
        print(f"QUERY: {q}")
        result = generate_grounded_response(q)
        report = validate_citations(result["response"], result["retrieved_articles"])
        print(f"  overall_pass: {report['overall_pass']}")
        if not report["overall_pass"]:
            all_pass = False
            for err in report["errors"]:
                print(f"  ERROR: {err}")
        for w in report["warnings"]:
            print(f"  WARN: {w}")
        print()

    print("=" * 70)
    print(f"DEMO RESULT: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")
    print("=" * 70)
    sys.exit(0 if all_pass else 1)
