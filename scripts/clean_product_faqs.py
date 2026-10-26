"""Clean the approved HisabDo product FAQ into one Markdown chunk per question.

Source: the official Help Center (https://hisabdo.app/faq), the only approved
product FAQ (see docs/dept3-knowledge-source-audit.md, OFF-01).

What it removes or fixes:
  * site header navigation, footer, intro text and call-to-action blocks
    (only the <details class="faq-item"> question/answer blocks are kept);
  * formatting glitches: HTML entities, non-breaking and zero-width spaces,
    mojibake (UTF-8 read as cp1252), curly quotes, emoji, repeated whitespace,
    space before punctuation;
  * website-relative wording that makes no sense inside a chatbot answer
    ("this website", "links in the footer"), replaced with explicit links
    taken from the same page;
  * links: converted to Markdown, e-mail addresses kept as plain text.

Each chunk gets front matter (id, section, source, owner, approval, dates,
review policy, content hash). Re-running compares hashes with the previous
index and reports added, changed and removed questions.

    python scripts/clean_product_faqs.py                          # fetch the live page
    python scripts/clean_product_faqs.py --html saved_page.html   # use a saved copy
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import sys
import unicodedata
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://hisabdo.app/faq"
SITE = "https://hisabdo.app"
OUT_DIR = ROOT / "data" / "kb" / "product_faqs"
OWNER = "Mian Usman Khalid (founder, XICTEK Systems)"
REVIEW_POLICY = "P-FAQ"
REVIEW_DAYS = 30  # P-FAQ: re-verify every 30 days and within 7 days of each app release

# Facts on this page that other official sources contradict (audit C-06).
NOTES = {
    "Which currencies does HisabDo support?":
        "Conflict (audit C-06): the Google Play listing of 2026-10-13 also lists AED. Confirm with the product owner.",
}

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]")
ZERO_WIDTH = re.compile("[​‌‎‏⁠﻿]")
SMART = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', " ": " ", " ": " "})


@dataclass
class FaqChunk:
    id: str
    question: str
    section: str
    answer: str
    source_url: str = SOURCE_URL
    owner: str = OWNER
    approval: str = "Approved (official publication)"
    retrieved_on: str = ""
    last_verified: str = ""
    review_policy: str = REVIEW_POLICY
    next_review_due: str = ""
    content_sha256: str = ""
    notes: str = ""
    fixes: list[str] = field(default_factory=list)  # what cleaning changed in this chunk


# ------------------------------------------------------------------------------------ cleaning


# A UTF-8 lead byte read as cp1252 (Â..ô) followed by 1-3 continuation bytes read as cp1252.
MOJIBAKE = re.compile("[Â-ô][-¿ŒœŠšŸŽžƒ"
                      "ˆ˜–—‘-„†-•…‰‹›€™]{1,3}")


def fix_mojibake(text: str) -> str:
    """'donâ€™t' -> 'don't': UTF-8 bytes that were decoded as cp1252.

    Each run is repaired on its own, so correct characters elsewhere in the text
    (which may not survive a cp1252 round trip) do not block the repair.
    """
    def repair(m: re.Match) -> str:
        try:
            return m.group(0).encode("cp1252").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return m.group(0)
    return MOJIBAKE.sub(repair, text)


def clean_text(text: str) -> str:
    text = html_lib.unescape(text)
    text = ZERO_WIDTH.sub("", text).replace(" ", " ")
    text = fix_mojibake(text)  # after the strip above: those characters break the cp1252 round trip
    text = unicodedata.normalize("NFC", text).translate(SMART)
    text = EMOJI.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)  # "word ." -> "word."
    return text


def inline_markdown(node: Tag, base_url: str) -> str:
    """Text of an answer element, with links as Markdown and e-mail addresses as plain text."""
    parts = []
    for child in node.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif child.name == "a":
            label = clean_text(child.get_text(" "))
            href = (child.get("href") or "").strip()
            if href.startswith("mailto:") or "@" in label:
                parts.append(label)
            elif href:
                parts.append(f"[{label}]({urljoin(base_url, href)})")
            else:
                parts.append(label)
        elif child.name in ("strong", "b"):
            parts.append(f"**{clean_text(child.get_text(' '))}**")
        elif child.name in ("em", "i"):
            parts.append(f"*{clean_text(child.get_text(' '))}*")
        elif child.name == "br":
            parts.append(" ")
        else:
            parts.append(inline_markdown(child, base_url))
    return clean_text("".join(parts))


def answer_markdown(details: Tag, base_url: str) -> str:
    blocks = []
    for el in details.find_all(["p", "ul", "ol"], recursive=False):
        if el.name == "p":
            text = inline_markdown(el, base_url)
            if text:
                blocks.append(text)
        else:
            marker = "-" if el.name == "ul" else "1."
            items = [inline_markdown(li, base_url) for li in el.find_all("li", recursive=False)]
            blocks.append("\n".join(f"{marker} {i}" for i in items if i))
    return "\n\n".join(blocks)


def contextualise(answer: str) -> tuple[str, list[str]]:
    """Replace website-relative wording, which means nothing inside a chatbot answer."""
    fixes = []
    if "in the footer of this website" in answer:
        # Social profile URLs are left out on purpose: the KB privacy gate blocks profile links.
        answer = answer.replace("Links are available in the footer of this website.",
                                f"Links to the official profiles are on [hisabdo.app]({SITE}).")
        fixes.append("replaced 'links in the footer of this website' with a link to hisabdo.app")
    if "on this website" in answer or "this website" in answer:
        answer = answer.replace("on this website", f"on [hisabdo.app]({SITE})").replace("this website", f"[hisabdo.app]({SITE})")
        fixes.append("replaced 'this website' with an explicit link")
    # Site pages named in an answer; the paths are the ones the site's own navigation uses.
    for phrase, path in (("Contact page", "/contact"), ("Privacy Policy", "/privacy-policy")):
        if f"our {phrase}" in answer and f"[{phrase}]" not in answer:
            answer = answer.replace(f"our {phrase}", f"our [{phrase}]({SITE}{path})")
            fixes.append(f"linked the {phrase}")
    return answer, fixes


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


# ------------------------------------------------------------------------------------ extraction


def extract(page_html: str, retrieved_on: date, base_url: str = SOURCE_URL) -> tuple[list[FaqChunk], dict]:
    soup = BeautifulSoup(page_html, "html.parser")
    main = soup.find("main") or soup
    report = {"removed_boilerplate": [], "warnings": []}

    # Everything outside the FAQ items is boilerplate: record what was dropped, for the cleaning report.
    for region in ("header", "footer"):
        tag = soup.find(region)
        if tag:
            report["removed_boilerplate"].append(f"{region}: {clean_text(tag.get_text(' | '))[:160]}")
    for el in main.find_all(["h1", "p", "a"]):
        if not el.find_parent("details"):
            text = clean_text(el.get_text(" "))
            if text and text not in report["removed_boilerplate"]:
                report["removed_boilerplate"].append(f"main: {text}")

    chunks, seen = [], set()
    for n, details in enumerate(main.find_all("details", class_="faq-item"), 1):
        summary = details.find("summary")
        question = clean_text(summary.get_text(" ")) if summary else ""
        heading = details.find_previous("h2")
        section = clean_text(heading.get_text(" ")) if heading else "General"
        answer = answer_markdown(details, base_url)
        if not question or not answer:
            report["warnings"].append(f"item {n}: empty question or answer, skipped")
            continue
        if question.lower() in seen:
            report["warnings"].append(f"duplicate question skipped: {question}")
            continue
        seen.add(question.lower())

        raw_answer = clean_text(" ".join(p.get_text(" ") for p in details.find_all("p")))
        fixes = []
        if raw_answer != " ".join(p.get_text(" ") for p in details.find_all("p")).strip():
            fixes.append("normalised whitespace/characters")
        answer, context_fixes = contextualise(answer)
        fixes += context_fixes

        chunk = FaqChunk(
            id=f"hisabdo-faq-{n:03d}", question=question, section=section, answer=answer,
            retrieved_on=retrieved_on.isoformat(), last_verified=retrieved_on.isoformat(),
            next_review_due=(retrieved_on + timedelta(days=REVIEW_DAYS)).isoformat(),
            notes=NOTES.get(question, ""), fixes=fixes,
        )
        chunk.content_sha256 = hashlib.sha256(f"{question}\n{answer}".encode("utf-8")).hexdigest()
        chunks.append(chunk)

    claimed = re.search(r"(\d+)\s+questions answered", main.get_text(" "))
    if claimed and int(claimed.group(1)) != len(chunks):
        report["warnings"].append(
            f"page says '{claimed.group(1)} questions answered' but contains {len(chunks)}: page counter is stale")
    return chunks, report


# ------------------------------------------------------------------------------------ output


def to_markdown(c: FaqChunk) -> str:
    def yaml_str(v: str) -> str:
        return json.dumps(v, ensure_ascii=False)  # JSON strings are valid YAML scalars

    meta = [f"id: {c.id}", f"question: {yaml_str(c.question)}", f"section: {yaml_str(c.section)}",
            f"source_url: {c.source_url}", f"owner: {yaml_str(c.owner)}", f"approval: {yaml_str(c.approval)}",
            f"retrieved_on: {c.retrieved_on}", f"last_verified: {c.last_verified}",
            f"review_policy: {c.review_policy}", f"next_review_due: {c.next_review_due}",
            f"content_sha256: {c.content_sha256}"]
    if c.notes:
        meta.append(f"notes: {yaml_str(c.notes)}")
    return "---\n" + "\n".join(meta) + "\n---\n\n" + f"## {c.question}\n\n{c.answer}\n"


def write(chunks: list[FaqChunk], report: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    index_file = out_dir / "index.json"
    previous = {}
    if index_file.exists():
        previous = {e["question"]: e["content_sha256"] for e in json.loads(index_file.read_text(encoding="utf-8"))["chunks"]}
    for old in out_dir.glob("*.md"):
        if old.name != "README.md":
            old.unlink()

    entries = []
    for c in chunks:
        name = f"{c.id}-{slugify(c.question)}.md"
        (out_dir / name).write_text(to_markdown(c), encoding="utf-8")
        entries.append({**{k: v for k, v in asdict(c).items() if k not in ("answer", "fixes")}, "file": name})

    current = {c.question: c.content_sha256 for c in chunks}
    changes = {
        "added": sorted(q for q in current if q not in previous),
        "changed": sorted(q for q in current if q in previous and previous[q] != current[q]),
        "removed": sorted(q for q in previous if q not in current),
    } if previous else {"added": sorted(current), "changed": [], "removed": []}
    index = {"source_url": SOURCE_URL, "chunk_count": len(chunks), "sections": sorted({c.section for c in chunks}),
             "warnings": report["warnings"], "changes_since_last_run": changes, "chunks": entries}
    index_file.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changes


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--html", help="saved copy of the FAQ page (default: fetch the live page)")
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--retrieved-on", default=date.today().isoformat())
    args = ap.parse_args()

    if args.html:
        page = Path(args.html).read_text(encoding="utf-8", errors="replace")
    else:
        req = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "HisabDo-KB-cleaner/1.0"})
        page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")

    chunks, report = extract(page, date.fromisoformat(args.retrieved_on))
    changes = write(chunks, report, Path(args.out))
    print(f"{len(chunks)} chunks in {len({c.section for c in chunks})} sections -> {args.out}")
    print(f"removed boilerplate blocks: {len(report['removed_boilerplate'])}")
    for b in report["removed_boilerplate"]:
        print(f"  - {b}")
    for w in report["warnings"]:
        print(f"WARNING: {w}")
    print(f"changes since last run: {', '.join(f'{k} {len(v)}' for k, v in changes.items())}")
    for c in chunks:
        if c.fixes:
            print(f"  {c.id}: {'; '.join(c.fixes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
