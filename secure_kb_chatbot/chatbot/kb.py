"""Knowledge base files: load, validate, and split into chunks.

Layout (one folder per KB version, kept in git so every change is reviewable):

    kb/v1/manifest.json        {"kb_version": "1.0.0", "released_on": "...", "changes": "..."}
    kb/v1/faqs.json            [{"id": "KB-001", "question": ..., "answer": ..., "status": "verified", ...}]
    kb/v1/docs/<name>.md       product documentation with a header block (see below)

A doc file starts with a header between two '---' lines:

    ---
    id: KB-101
    title: Recording an expense
    status: verified
    verified_by: Product team
    verified_on: 2026-10-13
    source: HisabDo user guide, section 4
    ---
    ## Section heading
    Text...

Only entries with status "verified" AND a named verifier AND a date are ever
indexed. A draft can sit in the folder without any risk of the chatbot quoting it.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

MAX_CHUNK_CHARS = 1200
_ID = re.compile(r"^KB-\d{3,}$")


class KBError(ValueError):
    pass


@dataclass(frozen=True)
class KBEntry:
    id: str
    title: str
    body: str  # FAQ: the answer. Doc: the markdown text.
    kind: str  # "faq" | "doc"
    status: str  # "verified" | "draft"
    verified_by: str = ""
    verified_on: str = ""
    source: str = ""
    category: str = ""

    @property
    def is_verified(self) -> bool:
        return self.status == "verified" and bool(self.verified_by.strip()) and bool(self.verified_on.strip())


@dataclass(frozen=True)
class KBChunk:
    entry_id: str
    chunk_no: int
    title: str
    section: str
    text: str
    source: str
    kb_version: str


def load_kb(version_dir: str | Path) -> tuple[str, list[KBEntry]]:
    """Read one KB version folder. Returns (kb_version, entries) and raises KBError on any problem."""
    root = Path(version_dir)
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        version = str(manifest["kb_version"])
    except (OSError, KeyError, json.JSONDecodeError) as e:
        raise KBError(f"{root}/manifest.json is missing or has no kb_version: {e}") from None

    entries: list[KBEntry] = []
    faq_file = root / "faqs.json"
    if faq_file.exists():
        try:
            raw_faqs = json.loads(faq_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise KBError(f"{faq_file}: invalid JSON: {e}") from None
        for f in raw_faqs:
            entries.append(KBEntry(
                id=str(f.get("id", "")), title=str(f.get("question", "")).strip(), body=str(f.get("answer", "")).strip(),
                kind="faq", status=str(f.get("status", "draft")), verified_by=str(f.get("verified_by", "")),
                verified_on=str(f.get("verified_on", "")), source=str(f.get("source", "")), category=str(f.get("category", "")),
            ))
    for path in sorted((root / "docs").glob("*.md")) if (root / "docs").exists() else []:
        entries.append(_parse_doc(path))

    _validate(entries)
    return version, entries


def _parse_doc(path: Path) -> KBEntry:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        raise KBError(f"{path}: missing the '---' header block")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip().lower()] = value.strip()
    return KBEntry(
        id=meta.get("id", ""), title=meta.get("title", ""), body=m.group(2).strip(), kind="doc",
        status=meta.get("status", "draft"), verified_by=meta.get("verified_by", ""),
        verified_on=meta.get("verified_on", ""), source=meta.get("source", ""), category=meta.get("category", ""),
    )


def _validate(entries: list[KBEntry]) -> None:
    problems, seen = [], set()
    for e in entries:
        label = e.id or f"(no id: {e.title[:40]!r})"
        if not _ID.match(e.id):
            problems.append(f"{label}: id must look like KB-001")
        if e.id in seen:
            problems.append(f"{label}: duplicate id")
        seen.add(e.id)
        if not e.title or not e.body:
            problems.append(f"{label}: empty title/question or body/answer")
        if e.status not in ("verified", "draft"):
            problems.append(f"{label}: status must be 'verified' or 'draft'")
        if e.status == "verified":
            if not e.verified_by.strip():
                problems.append(f"{label}: verified entries need verified_by")
            try:
                date.fromisoformat(e.verified_on)
            except ValueError:
                problems.append(f"{label}: verified entries need verified_on as YYYY-MM-DD")
    if problems:
        raise KBError("Knowledge base problems:\n  - " + "\n  - ".join(problems))


def chunk_entries(kb_version: str, entries: list[KBEntry]) -> list[KBChunk]:
    """Split VERIFIED entries into retrieval-sized chunks. Drafts are skipped."""
    chunks: list[KBChunk] = []
    for e in entries:
        if not e.is_verified:
            continue
        if e.kind == "faq":
            parts = [("", f"Q: {e.title}\nA: {e.body}")]
        else:
            parts = _split_doc(e.body)
        for n, (section, text) in enumerate(parts, 1):
            chunks.append(KBChunk(e.id, n, e.title, section, text, e.source, kb_version))
    return chunks


def _split_doc(body: str) -> list[tuple[str, str]]:
    """Split on '## ' headings, then on paragraphs if a section is still too long."""
    sections: list[tuple[str, str]] = []
    heading, lines = "", []
    for line in body.splitlines():
        if line.startswith("## "):
            if "".join(lines).strip():
                sections.append((heading, "\n".join(lines).strip()))
            heading, lines = line[3:].strip(), []
        else:
            lines.append(line)
    if "".join(lines).strip():
        sections.append((heading, "\n".join(lines).strip()))

    out: list[tuple[str, str]] = []
    for heading, text in sections:
        if len(text) <= MAX_CHUNK_CHARS:
            out.append((heading, text))
            continue
        current = ""
        for para in re.split(r"\n\s*\n", text):
            if current and len(current) + len(para) + 2 > MAX_CHUNK_CHARS:
                out.append((heading, current.strip()))
                current = ""
            current += para + "\n\n"
        if current.strip():
            out.append((heading, current.strip()))
    return out
