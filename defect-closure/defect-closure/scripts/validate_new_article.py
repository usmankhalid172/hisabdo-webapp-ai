"""
Ingestion-time Content Validator — Blog & News Articles
=======================================================
Runs on every new or updated blog article before it is indexed into the
retrieval corpus. Mitigates Defect D10 (article corpus integrity assumes
CMS trust): if an attacker compromises the CMS and injects malicious
content into a blog article, this validator scans the article body for
prompt-injection patterns and dangerous URIs before indexing. Flagged
articles are rejected and held for manual review.

Validation rules (article is REJECTED if ANY of these fire):

  R1  Required frontmatter is present
      (Source, Category, Reading time, Published, Author)
  R2  Source URL is on the production blog allowlist
      (https://www.xicteksystems.com/blog/<slug>)
  R3  Body length is within chunking limits
      (50 <= len(body) <= 5000 characters; longer articles are
      truncated by the chunker, but a >5000-char body suggests
      an untrimmed dump — likely a CMS injection)
  R4  No prompt-injection patterns in body
      ("ignore previous instructions", "ignore all prior",
       "you are now", "[SYSTEM]", "<<SYS>>", "<|im_start|>",
       "new instructions:", "system prompt:", etc.)
  R5  No dangerous URI schemes in body
      (javascript:, file:, data:, vbscript:)
  R6  No non-blog HTTP URLs masquerading as sources in body
      (/services, /contact, /about, hisabdo.app, external domains
       that are not the production blog)
  R7  No base64-looking blobs over 200 chars
      (possible encoded injection payloads)
  R8  No exfiltration patterns
      (curl, wget, http://evil, fetch() in article body — these
       are not normal blog content)

Usage:
    python3 scripts/validate_new_article.py data/articles/new-article.md
    python3 scripts/validate_new_article.py data/articles/  # validate all
    python3 scripts/validate_new_article.py --strict data/articles/new.md
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Dict

# ---- Patterns (frozen from Frozen Domain Configuration Spec §8) ----

REQUIRED_FRONTMATTER = ["Source", "Category", "Reading time", "Published", "Author"]

BLOG_URL_ALLOWLIST = re.compile(
    r'^https://www\.xicteksystems\.com/blog/[a-z0-9-]+$'
)

# R4 — Prompt-injection patterns (case-insensitive substring match)
INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"ignore all prior instructions",
    r"ignore the above",
    r"disregard previous",
    r"disregard the above",
    r"you are now (a|an) ",
    r"new instructions:",
    r"system prompt:",
    r"override the system",
    r"\[SYSTEM\]",
    r"<<SYS>>",
    r"<\|im_start\|>",
    r"<\|system\|>",
    r"reveal (your|the) system prompt",
    r"reveal (your|the) hidden instructions",
    r"print (your|the) initial message",
]

# R5 — Dangerous URI schemes
DANGEROUS_URI_SCHEMES = [
    re.compile(r'\bjavascript:', re.IGNORECASE),
    re.compile(r'\bfile://', re.IGNORECASE),
    re.compile(r'\bdata:', re.IGNORECASE),
    re.compile(r'\bvbscript:', re.IGNORECASE),
]

# R6 — Non-blog HTTP URLs (URL allowlist violation in body)
NON_BLOG_URL_PATTERNS = [
    re.compile(r'xicteksystems\.com/(services|contact|about|careers)([/\s\)\]]|$)'),
    re.compile(r'\bhisabdo\.app\b'),
    re.compile(r'\b(linkedin|facebook|twitter|instagram)\.com\b'),
    re.compile(r'\b(evil|attacker|malicious|example)\.(com|net|io)\b'),
]

# R7 — Base64-looking blobs (long alphanumeric+/=+/ runs)
BASE64_BLOB = re.compile(r'[A-Za-z0-9+/=]{200,}')

# R8 — Exfiltration patterns (not normal in blog content)
EXFIL_PATTERNS = [
    re.compile(r'\bcurl\b\s+https?://', re.IGNORECASE),
    re.compile(r'\bwget\b\s+https?://', re.IGNORECASE),
    re.compile(r'\bfetch\s*\(\s*[\'"]https?://', re.IGNORECASE),
    re.compile(r'\bXMLHttpRequest\b', re.IGNORECASE),
    re.compile(r'\beval\s*\(', re.IGNORECASE),
]


def parse_frontmatter(text: str) -> dict:
    """Extract metadata pairs from the article header.

    Handles three formats found in the production corpus:
      (a) `*Source: <value>*` — italic single-asterisk wrapper
      (b) `**Key:** <value>` — bold key, value on the same line
      (c) `**Key:** <value> · **Key2:** <value2> · ...` — multiple pairs on one
          line, separated by ` · `
    Scans the first 15 lines of the file.
    """
    fm = {}
    for line in text.split("\n")[:15]:
        # (a) italic Source line: *Source: <value>*
        m_italic = re.match(r'^\*Source:\s*(.+?)\s*\*\s*$', line)
        if m_italic:
            fm["Source"] = m_italic.group(1).strip()
            continue
        # (b) + (c) bold key(s): may have one or more `**Key:** value` segments
        # split by ` · ` on the same line.
        for seg in re.split(r'\s*·\s*', line):
            m = re.match(r'^\*\*([^*]+):\*\*\s*(.+?)\s*$', seg)
            if m:
                fm[m.group(1).strip()] = m.group(2).strip()
    return fm


def extract_body(text: str) -> str:
    """Return the article text minus the frontmatter header lines.

    Skips: italic Source line, bold frontmatter pair lines, blank lines, and
    the H1 title, until the first horizontal-rule separator (`---`) or the
    first non-header content line.
    """
    lines = text.split("\n")
    body_lines = []
    seen_separator = False
    for line in lines:
        # Skip italic Source line
        if re.match(r'^\*Source:\s*.+\*\s*$', line):
            continue
        # Skip bold frontmatter pair lines
        if re.match(r'^\*\*[^*]+:\*\*\s*.+$', line):
            continue
        # Skip the H1 title
        if line.startswith("# ") and not body_lines and not seen_separator:
            continue
        # Skip horizontal-rule separator (frontmatter / body boundary)
        if line.strip() == "---":
            seen_separator = True
            continue
        # Skip leading blank lines
        if line.strip() == "" and not body_lines:
            continue
        body_lines.append(line)
    return "\n".join(body_lines).strip()


def validate_article(article_path: Path, strict: bool = False) -> Dict:
    """Run all validation rules against one article. Return a structured result."""
    result = {
        "path": str(article_path),
        "filename": article_path.name,
        "rules_checked": 8,
        "errors": [],
        "warnings": [],
        "verdict": "PASS",  # PASS | REJECT
    }

    if not article_path.is_file():
        result["errors"].append(f"R0: file does not exist or is not readable")
        result["verdict"] = "REJECT"
        return result

    try:
        text = article_path.read_text(encoding="utf-8")
    except Exception as e:
        result["errors"].append(f"R0: cannot read file as UTF-8: {e}")
        result["verdict"] = "REJECT"
        return result

    # ---- R1: required frontmatter ----
    fm = parse_frontmatter(text)
    missing = [k for k in REQUIRED_FRONTMATTER if k not in fm]
    if missing:
        result["errors"].append(f"R1: missing required frontmatter: {missing}")

    # ---- R2: source URL on blog allowlist ----
    source_url = fm.get("Source", "")
    if source_url and not BLOG_URL_ALLOWLIST.match(source_url):
        result["errors"].append(
            f"R2: Source URL '{source_url}' is not on the production blog allowlist "
            f"(expected https://www.xicteksystems.com/blog/<slug>)"
        )

    # ---- R3: body length within chunking limits ----
    body = extract_body(text)
    body_len = len(body)
    if body_len < 50:
        result["errors"].append(f"R3: body is too short ({body_len} chars; minimum 50)")
    elif body_len > 5000:
        result["warnings"].append(
            f"R3: body is long ({body_len} chars > 5000); chunker will truncate. "
            f"In strict mode this is an error."
        )
        if strict:
            result["errors"].append(
                f"R3: body exceeds 5000 chars in strict mode ({body_len})"
            )

    # ---- R4: no prompt-injection patterns in body ----
    body_lower = body.lower()
    for pat in INJECTION_PATTERNS:
        if re.search(pat, body_lower):
            result["errors"].append(
                f"R4: prompt-injection pattern matched in body: /{pat}/"
            )

    # ---- R5: no dangerous URI schemes ----
    for pat in DANGEROUS_URI_SCHEMES:
        m = pat.search(body)
        if m:
            result["errors"].append(
                f"R5: dangerous URI scheme matched in body: {m.group(0)}"
            )

    # ---- R6: no non-blog HTTP URLs in body ----
    for pat in NON_BLOG_URL_PATTERNS:
        m = pat.search(body)
        if m:
            result["errors"].append(
                f"R6: non-blog URL matched in body (scope leak risk): {m.group(0)}"
            )

    # ---- R7: no base64-looking blobs over 200 chars ----
    for m in BASE64_BLOB.finditer(body):
        if len(m.group(0)) >= 200:
            result["warnings"].append(
                f"R7: base64-looking blob of {len(m.group(0))} chars found in body "
                f"(possible encoded payload; review manually)"
            )
            if strict:
                result["errors"].append(
                    f"R7: base64 blob exceeds 200 chars in strict mode"
                )

    # ---- R8: no exfiltration patterns ----
    for pat in EXFIL_PATTERNS:
        m = pat.search(body)
        if m:
            result["errors"].append(
                f"R8: exfiltration pattern matched in body: {m.group(0)}"
            )

    if result["errors"]:
        result["verdict"] = "REJECT"
    return result


def main():
    p = argparse.ArgumentParser(
        description="Ingestion-time content validator for Blog & News articles"
    )
    p.add_argument("target", help="Article file (.md) or directory of articles")
    p.add_argument("--strict", action="store_true",
                   help="Treat long bodies and base64 blobs as errors, not warnings")
    p.add_argument("--json", action="store_true",
                   help="Output structured JSON instead of human-readable text")
    args = p.parse_args()

    target = Path(args.target)
    if target.is_dir():
        articles = sorted(target.glob("*.md"))
    elif target.is_file():
        articles = [target]
    else:
        print(f"ERROR: target '{target}' is not a file or directory", file=sys.stderr)
        return 2

    if not articles:
        print(f"ERROR: no .md articles found at '{target}'", file=sys.stderr)
        return 2

    results = [validate_article(a, strict=args.strict) for a in articles]

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print("=" * 70)
        print("INGESTION-TIME CONTENT VALIDATOR — Blog & News")
        print("=" * 70)
        print(f"Target: {target}")
        print(f"Strict: {args.strict}")
        print(f"Articles checked: {len(results)}")
        print()
        for r in results:
            mark = "✓" if r["verdict"] == "PASS" else "✗"
            print(f"  {mark} [{r['verdict']:6s}] {r['filename']}")
            for e in r["errors"]:
                print(f"           ERROR: {e}")
            for w in r["warnings"]:
                print(f"           WARN : {w}")
        print()
        pass_count = sum(1 for r in results if r["verdict"] == "PASS")
        reject_count = len(results) - pass_count
        print("=" * 70)
        print(f"RESULT: {pass_count} passed, {reject_count} rejected")
        print("=" * 70)

    return 0 if all(r["verdict"] == "PASS" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
