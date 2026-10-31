"""Scan knowledge-base files for personal identifiers before they reach the chatbot.

Flags e-mail addresses, Pakistani and international phone numbers, CNIC numbers,
and reviewer-identity fields (author, reviewer, user name, profile links) in
JSON records. Official business contact addresses on an allowlist are reported
as allowed, not as findings.

    python scripts/kb_privacy_scan.py                       # the live chatbot KB files
    python scripts/kb_privacy_scan.py path/to/file.json ... # any files

Exit code 1 if any personal identifier is found, so it can gate KB changes in CI.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE_KB = [ROOT / "data" / "faq_docs.json", ROOT / "data" / "sample_financial_knowledge.json"]

# Official business contact published on https://hisabdo.app/faq; not a personal identifier.
ALLOWED = {"hisabdo.app@gmail.com"}

PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "pk_phone": re.compile(r"(?:\+92[\s-]?|0)3\d{2}[\s-]?\d{7}\b"),
    "intl_phone": re.compile(r"\+\d{1,3}[\s-]?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}\b"),
    "cnic": re.compile(r"\b\d{5}-\d{7}-\d\b"),
    "profile_link": re.compile(r"https?://(?:www\.)?(?:facebook|instagram|linkedin|tiktok|x|twitter)\.com/[^\s\"']+", re.I),
}
IDENTITY_KEYS = {"author", "reviewer", "reviewer_name", "user", "user_name", "username", "customer_name",
                 "name", "email", "phone", "profile", "avatar"}


def scan_text(text: str) -> list[tuple[str, str]]:
    hits = []
    for kind, pattern in PATTERNS.items():
        for m in pattern.finditer(text):
            value = m.group(0)
            hits.append((kind, value if value.lower() not in ALLOWED else f"{value} (allowed: official contact)"))
    return hits


def scan_json_keys(data, path="$") -> list[tuple[str, str]]:
    hits = []
    if isinstance(data, dict):
        for k, v in data.items():
            if k.lower() in IDENTITY_KEYS and isinstance(v, str) and v.strip():
                hits.append(("identity_field", f"{path}.{k}"))
            hits += scan_json_keys(v, f"{path}.{k}")
    elif isinstance(data, list):
        for i, v in enumerate(data):
            hits += scan_json_keys(v, f"{path}[{i}]")
    return hits


def scan_file(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    hits = scan_text(text)
    if path.suffix == ".json":
        try:
            hits += scan_json_keys(json.loads(text))
        except json.JSONDecodeError:
            hits.append(("unreadable_json", str(path.name)))
    return hits


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    files = [Path(a) for a in argv] or LIVE_KB
    blocking = 0
    for f in files:
        hits = scan_file(f)
        real = [h for h in hits if "(allowed" not in h[1]]
        blocking += len(real)
        status = "CLEAN" if not real else f"{len(real)} PERSONAL IDENTIFIER(S)"
        print(f"{status:28} {f.name}")
        for kind, value in hits:
            print(f"    {kind}: {value}")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
