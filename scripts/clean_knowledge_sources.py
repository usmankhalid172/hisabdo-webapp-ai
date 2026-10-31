"""Clean every approved knowledge source into Markdown chunks for the chatbot KB.

Approved sources come from the register, data/knowledge_source_audit.csv: official
publications whose verdict is "Keep ...". Repository files have no approval record
and are not cleaned here (see docs/dept3-knowledge-source-audit.md).

For each source the cleaner
  * keeps only the page content: header, footer, navigation, table of contents,
    badges, buttons, call-to-action banners, stats tiles, "Related Articles",
    "About the Author" and keyword lists are removed and listed in the report;
  * fixes formatting glitches (shared with clean_product_faqs.clean_text);
  * splits the content into chunks: one per FAQ question, one per page section
    (h2), long sections split at sub-headings or paragraphs;
  * attaches metadata: title, section, category, source URL, language,
    last-updated date, product/company area, owner, approval, review policy;
  * removes duplicate chunks (keeps the copy from the most authoritative source);
  * flags facts that disagree between sources instead of choosing one;
  * checks that every sentence in every chunk appears in the source page, so the
    cleaning cannot change the meaning or add information.

    python scripts/clean_knowledge_sources.py --fetch    # download today's snapshots, then clean
    python scripts/clean_knowledge_sources.py            # clean the latest saved snapshots
"""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import re
import sys
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, Tag

sys.path.insert(0, str(Path(__file__).resolve().parent))
from clean_product_faqs import clean_text, contextualise, inline_markdown, slugify  # noqa: E402
from clean_product_faqs import extract as extract_faq  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "data" / "knowledge_source_audit.csv"
SNAPSHOTS = ROOT / "data" / "kb" / "sources"
OUT_DIR = ROOT / "data" / "kb" / "approved"
MAX_CHARS = 1500  # longer sections are split; about 300 words keeps one idea per chunk

# Category in the KB (the audit's categories, normalised) and how much the source is trusted
# when two sources say the same thing. Lower wins.
CATEGORIES = {
    "Product FAQ": ("product_faq", 1),
    "Feature guide": ("product_guide", 2),
    "Policy/legal": ("legal_policy", 3),
    "Workflow/practice guide (general)": ("finance_guide", 4),
}
REVIEW_DAYS = {"P-FAQ": 30, "P-LEGAL": 182, "P-CONCEPT": 365}

# Blocks that are UI, not knowledge. Matched on CSS class.
DROP_CLASSES = {"toc", "hero-buttons", "badge", "btn", "btn-outline", "section-divider", "split-img",
                "card-icon", "stats", "stat-item", "hero-note"}
DROP_TAGS = {"script", "style", "svg", "img", "picture", "video", "iframe", "form", "button", "noscript"}
FAQ_HEADING = re.compile(r"^(frequently asked questions|faqs?)$", re.I)
# Whole sections that are navigation or calls to action: blog teasers, contributor sign-up, screenshot gallery.
IRRELEVANT_SECTIONS = re.compile(r"^(latest blog posts|application screens|apna business ka tajurba share karein)$", re.I)
# Sections of the Play description that are search keywords, not statements.
KEYWORD_SECTIONS = {"WHY USE HISABDO?"}

# Area of the product (or company) a chunk is about. First the heading is scored (x3), then the text.
AREAS = [
    ("Company", ["xictek", "founder", "who created", "who built", "company", "why we built"]),
    ("Product Overview", ["what is hisabdo", "designed for", "built for", "who is hisabdo"]),
    ("Pricing & Download", ["free to use", "free of charge", "download", "google play", "subscription", "price"]),
    ("Platform & Devices", ["android", "ios", "iphone", "android version", "device support"]),
    ("Language & Currency", ["language", "urdu", "hindi", "arabic", "currenc", "pkr", "inr", "aed", "usd"]),
    ("Data, Backup & Sync", ["backup", "back up", "restore", "sync", "supabase", "offline", "internet", "cloud",
                             "lose my phone", "new phone", "uninstall"]),
    ("Privacy & Security", ["privacy", "secure", "security", "personal information", "third part", "delete",
                            "permission", "children", "retention"]),
    ("Reports & PDF Export", ["pdf", "report", "statement", "export"]),
    ("Suppliers & Payables", ["payable", "supplier", "vendor"]),
    ("Customers & Receivables", ["receivable", "customer", "udhar", "dues", "credit", "owed to me", "collect"]),
    ("Expenses & Income", ["expense", "income", "spending", "budget", "categor"]),
    ("Analytics", ["analytics", "insight", "chart", "trend"]),
    ("Voice Entry", ["voice"]),
    ("Support", ["hisabdo support", "contact", "feedback", "bug", "follow hisabdo", "help center"]),
    ("Khata & Ledger", ["khata", "ledger", "transaction", "bookkeeping"]),
]


# Areas that only make sense for statements about HisabDo itself.
PRODUCT_ONLY_AREAS = {"Company", "Product Overview", "Pricing & Download", "Platform & Devices", "Voice Entry",
                      "Support", "Language & Currency"}


@dataclass
class Source:
    source_id: str
    title: str
    category: str
    priority: int
    url: str
    owner: str
    approval: str
    review_policy: str
    usage: str  # "answer": the chatbot may answer from it; "reference_only": quote and link, do not interpret


@dataclass
class Chunk:
    id: str
    title: str
    section: str
    heading: str
    body: str
    category: str
    source_id: str
    source_url: str
    language: str
    last_updated: str | None
    last_updated_basis: str
    area: str
    scope: str  # product | company | legal | general_finance
    usage: str
    owner: str
    approval: str
    review_policy: str
    retrieved_on: str
    next_review_due: str
    content_sha256: str = ""
    status: str = "active"  # active | needs_confirmation
    notes: list[str] = field(default_factory=list)


# ------------------------------------------------------------------------------------ sources


def approved_sources() -> list[Source]:
    """Official publications the audit approved for the KB."""
    sources = []
    for r in csv.DictReader(AUDIT.open(encoding="utf-8-sig")):
        if not r["source_id"].startswith(("OFF-", "BLOG-")) or not r["verdict"].startswith("Keep"):
            continue
        if not r["approval_status"].startswith("Approved"):
            continue
        category, priority = CATEGORIES[r["category"]]
        sources.append(Source(
            source_id=r["source_id"], title=r["title"], category=category, priority=priority, url=r["url"],
            owner=r["content_owner"], approval=r["approval_status"], review_policy=r["review_policy"].split(":")[0],
            usage="reference_only" if "reference only" in r["verdict"] else "answer"))
    return sources


def fetch(source: Source, snapshot_dir: Path) -> None:
    url = source.url + ("&hl=en" if "play.google.com" in source.url else "")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (HisabDo-KB-cleaner/1.0)"})
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
    if "play.google.com" in source.url:
        page = trim_play_page(page)  # the full page is ~1.2 MB of scripts and user reviews (OFF-05, not approved)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_dir / f"{source.source_id}.html").write_text(page, encoding="utf-8")


def trim_play_page(page: str) -> str:
    soup = BeautifulSoup(page, "html.parser")
    title = soup.find("h1")
    about = soup.find("h2", string=re.compile("About this app"))
    section = about.find_parent("section") if about else None
    updated = re.search(r"Updated on</div><div[^>]*>([^<]+)", page)
    return ("<html lang=\"en\"><body><main>"
            f"<h1>{title.get_text(strip=True) if title else ''}</h1>"
            f"<div class=\"updated-on\">{updated.group(1) if updated else ''}</div>"
            f"{section if section else ''}</main></body></html>")


# ------------------------------------------------------------------------------------ page parsing


def parse_date(text: str) -> str | None:
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    try:
        return datetime.strptime(text.strip(), "%B %Y").strftime("%Y-%m")  # month only: keep the precision given
    except ValueError:
        return None


def page_date(soup: BeautifulSoup) -> tuple[str | None, str]:
    note = soup.select_one(".hero-note")
    if note and (m := re.search(r"Published:\s*([A-Z][a-z]+ \d{1,2}, \d{4})", note.get_text(" "))):
        return parse_date(m.group(1)), "published date shown on the page"
    if m := re.search(r"Effective Date:\s*([A-Z][a-z]+(?: \d{1,2},)? \d{4})", soup.get_text(" ")):
        return parse_date(m.group(1)), "effective date shown on the page"
    if (upd := soup.select_one(".updated-on")) and upd.get_text(strip=True):
        return parse_date(upd.get_text(strip=True)), "Google Play 'Updated on' date"
    return None, "not shown on the page"


def language_of(soup: BeautifulSoup, text: str) -> str:
    declared = (soup.html.get("lang") if soup.html else None) or "en"
    arabic_script = len(re.findall(r"[؀-ۿ]", text))
    if arabic_script > 0.3 * max(1, len(re.findall(r"\w", text))):
        return "ur"
    return declared.split("-")[0].lower()


def blocks(el: Tag, base_url: str, removed: list[str]):
    """Content blocks in document order: ('h', level, text) ('p', text) ('list', items) ('qa', q, a)."""
    for c in el.children:
        if isinstance(c, NavigableString) or not isinstance(c, Tag):
            continue
        classes = set(c.get("class", []))
        if c.name in DROP_TAGS:
            continue
        if classes & DROP_CLASSES or c.name in ("nav", "aside", "header", "footer"):
            text = clean_text(c.get_text(" "))
            if text:
                removed.append(text)
            continue
        if c.name == "section" and "hero" in classes and not c.find("h1"):
            removed.append(clean_text(c.get_text(" ")))  # call-to-action banner
            continue
        if re.fullmatch(r"h[1-4]", c.name):
            yield ("h", int(c.name[1]), clean_text(c.get_text(" ")))
        elif c.name == "p":
            yield ("p", inline_markdown(c, base_url))
        elif c.name in ("ul", "ol"):
            items = [inline_markdown(li, base_url) for li in c.find_all("li", recursive=False)]
            yield ("list", c.name, [i for i in items if i])
        elif c.name == "details":
            summary = c.find("summary")
            q = clean_text(summary.get_text(" ")) if summary else ""
            a = "\n\n".join(inline_markdown(p, base_url) for p in c.find_all("p"))
            yield ("qa", q, a)
        elif c.name == "table":
            rows = [[inline_markdown(td, base_url) for td in tr.find_all(["th", "td"])] for tr in c.find_all("tr")]
            yield ("table", rows)
        elif c.name == "a":
            text = clean_text(c.get_text(" "))
            if text:
                removed.append(text)  # stand-alone link outside a paragraph: navigation
        else:
            yield from blocks(c, base_url, removed)


def drop_page_furniture(items: list, removed: list[str]) -> list:
    """Remove 'Related Articles' link lists and 'About the Author' boxes, which are not knowledge."""
    out, skip = [], None
    for b in items:
        text = plain(b[1]) if b[0] == "p" else ""
        if text.startswith("See also:"):
            removed.append(text)  # cross-links to other articles
            continue
        if b[0] == "p" and (text == "About the Author" or re.fullmatch("(All )?Related Articles", text)):
            skip = text
            removed.append(text)
            continue
        if b[0] == "p" and (text.startswith("→") or LINK_ONLY.fullmatch(b[1])):
            removed.append(text)  # a paragraph that is only a link ("→ Article title", "All Related Articles")
            continue
        if skip == "About the Author" and b[0] == "p":
            removed.append("author biography")
            skip = None
            continue
        skip = None
        out.append(b)
    return out


def render(b) -> str:
    if b[0] == "p":
        return b[1]
    if b[0] == "list":
        marker = "-" if b[1] == "ul" else "1."
        return "\n".join(f"{marker} {i}" for i in b[2])
    if b[0] == "table":
        rows = [r for r in b[1] if any(r)]
        if not rows:
            return ""
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
        return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in rows[1:]])
    if b[0] == "h":
        return f"### {b[2]}"
    return ""


def split_long(heading: str, parts: list[str]) -> list[tuple[str, str]]:
    """Split a long section at sub-headings, else between paragraphs. Never inside a paragraph."""
    text = "\n\n".join(p for p in parts if p)
    if len(text) <= MAX_CHARS:
        return [(heading, text)]
    groups, current = [], []
    for p in parts:
        size = sum(len(x) + 2 for x in current)
        if current and (p.startswith("### ") or size + len(p) > MAX_CHARS):
            groups.append(current)
            current = []
        current.append(p)
    groups.append(current)
    return [(f"{heading} (part {n})", "\n\n".join(g)) for n, g in enumerate(groups, 1)]


def sections_of_page(soup: BeautifulSoup, base_url: str, removed: list[str]) -> tuple[str, list[dict]]:
    """[{section, heading, body, kind}] from a website page or the trimmed Play page."""
    main = soup.find("main") or soup.body or soup
    for region in ("header", "footer"):
        if tag := soup.find(region):
            removed.append(f"{region}: {clean_text(tag.get_text(' | '))[:200]}")
    h1 = main.find("h1")
    title = clean_text(h1.get_text(" ")) if h1 else ""

    if main.find("h2", string=re.compile("About this app")):
        return title, play_sections(main, removed)

    items = drop_page_furniture(list(blocks(main, base_url, removed)), removed)
    out, section, parts, in_faq = [], "Overview", [], False

    def flush():
        body = [p for p in parts if p]
        if IRRELEVANT_SECTIONS.match(section):
            removed.append(f"irrelevant section: {section}")
        elif any(not p.startswith("### ") for p in body):
            out.extend({"section": s, "heading": s, "body": b, "kind": "section"} for s, b in split_long(section, body))
        elif (body or section != "Overview") and not in_faq:  # FAQ sections become question chunks instead
            removed.append(f"section without content: {section}")

    pending_q = None
    for b in items:
        if b[0] == "h" and b[1] == 1:
            continue
        if b[0] == "h" and b[1] == 2:
            flush()
            section, parts, in_faq, pending_q = b[2], [], bool(FAQ_HEADING.match(b[2])), None
            continue
        if in_faq:
            # FAQ blocks on articles: <details> items or <h3> question + <p> answer. One chunk per question.
            if b[0] == "qa" and b[1] and b[2]:
                out.append({"section": section, "heading": b[1], "body": b[2], "kind": "qa"})
            elif b[0] == "h":
                pending_q = b[2]
            elif b[0] in ("p", "list") and pending_q:
                if out and out[-1]["heading"] == pending_q:
                    out[-1]["body"] += "\n\n" + render(b)
                else:
                    out.append({"section": section, "heading": pending_q, "body": render(b), "kind": "qa"})
            continue
        if b[0] == "qa":
            parts.append(f"### {b[1]}\n\n{b[2]}")
        else:
            parts.append(render(b))
    flush()
    return title, merge_short_intros(out)


def merge_short_intros(sections: list[dict], min_chars: int = 150) -> list[dict]:
    """A one-line section intro ("Here's what happens during a normal day.") becomes the lead of the next section."""
    out = []
    for i, s in enumerate(sections):
        nxt = sections[i + 1] if i + 1 < len(sections) else None
        if (s["kind"] == "section" and len(s["body"]) < min_chars and nxt and nxt["kind"] == "section"
                and s["section"] != "Overview" and not s.get("merged")):
            nxt["body"] = f"{s['body']}\n\n{nxt['body']}"
            nxt["section"] = f"{s['section']} > {nxt['section']}"
            nxt["merged"] = True  # never chain: one intro per section
            continue
        out.append(s)
    return out


def play_sections(main: Tag, removed: list[str]) -> list[dict]:
    """The Play 'About this app' text: ALL-CAPS lines are headings, '•' lines are list items."""
    about = main.find("h2", string=re.compile("About this app"))
    container = max(about.find_parent("section").find_all("div"), key=lambda d: len(d.find_all("br")))
    lines = [clean_text(x) for x in container.get_text("\n").split("\n")]
    lines = [x for x in lines if x]
    out, section, parts = [], "Overview", []

    def flush():
        if section in KEYWORD_SECTIONS:
            removed.append(f"keyword list: {section} ({len(parts)} lines)")
        elif parts:
            body = "\n".join(parts).replace("\n- ", "\n\n- ", 1) if parts and not parts[0].startswith("-") else "\n".join(parts)
            out.append({"section": section.title() if section.isupper() else section, "heading": section.title(),
                        "body": body, "kind": "section"})

    for line in lines:
        if not line.startswith("•") and line.isupper() and len(re.findall(r"[A-Z]", line)) > 3:
            flush()
            section, parts = line, []
        elif line.startswith("•"):
            parts.append("- " + line.lstrip("• ").strip())
        else:
            parts.append(("\n" if parts else "") + line)
    flush()
    return out


# ------------------------------------------------------------------------------------ metadata


def classify(heading: str, body: str, source: Source) -> tuple[str, str]:
    """(area, scope)."""
    if source.category == "legal_policy":
        return "Legal & Policy", "legal"
    head, text = heading.lower(), body.lower()
    general = source.category == "finance_guide" and "hisabdo" not in text and "hisabdo" not in head
    names = [a for a, _ in AREAS if not (general and a in PRODUCT_ONLY_AREAS)]

    def hits(keys, s):  # whole words, so "invoice" is not "voice"
        return sum(len(re.findall(r"\b" + re.escape(k), s)) for k in keys)

    scores = {name: 5 * hits(keys, head) + hits(keys, text) for name, keys in AREAS if name in names}
    area = max(scores, key=lambda n: (scores[n], -names.index(n)))
    if general:
        return f"{area} (general practice)" if scores[area] else "Business finance (general)", "general_finance"
    if scores[area] == 0:
        area = "Khata & Ledger"
    return area, "company" if area == "Company" else "product"


def plain(text: str) -> str:
    """Text without Markdown, for comparison with the source page."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s*(?:[-*]|\d+\.|#+)\s+", "", text, flags=re.M)
    text = text.replace("**", "").replace("|", " ")
    return re.sub(r"\s+", " ", text).strip()


def words(text: str) -> str:
    """Word sequence used by the meaning check: punctuation, bullets and Markdown ignored, wording not."""
    return " " + " ".join(re.findall(r"[a-z0-9]+", text.lower())) + " "


def unsupported_sentences(body: str, page_words: str) -> list[str]:
    """Sentences of a chunk whose wording is not on the source page. Must be empty for every chunk.

    Checked paragraph by paragraph, so a merged intro is not joined to the next paragraph.
    """
    return [s for para in body.split("\n\n") for s in sentences(plain(para)) if words(s) not in page_words]


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", text) if len(s.strip()) > 2]


# ------------------------------------------------------------------------------------ cleaning run


SITE = "https://hisabdo.app"
LINK_ONLY = re.compile(r"\[[^\]]*\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")


def site_pages(soup: BeautifulSoup, approved_urls: set[str]) -> set[str]:
    """Pages a link may point to: approved sources plus the pages in the site's own header/footer menus."""
    pages = {u.rstrip("/") for u in approved_urls}
    for region in ("header", "footer"):
        for a in (soup.find(region) or BeautifulSoup("", "html.parser")).find_all("a", href=True):
            url = urljoin(SITE + "/", a["href"]).split("#")[0].rstrip("/")
            if url.startswith(SITE):
                pages.add(url)
    return pages | {SITE}


def fix_links(body: str, known: set[str], report: dict) -> tuple[str, list[str]]:
    """Repair site links that point to a missing root path, and unlink site links that lead nowhere.

    The articles link to each other as /slug, which is a 404: the articles live at /blog/slug.
    """
    fixes = []

    def repl(m: re.Match) -> str:
        label, url = m.group(1), m.group(2)
        base = url.split("#")[0].rstrip("/")
        if not base.startswith(SITE) or base in known:
            return m.group(0)
        blog = base.replace(SITE, SITE + "/blog", 1)
        if blog in known:
            fixes.append(f"link {base} (404) -> {blog}")
            return f"[{label}]({blog})"
        fixes.append(f"link {base} matches no known page: kept the text, removed the link")
        report["broken_links"].append(base)
        return label

    return LINK.sub(repl, body), fixes


def clean_source(source: Source, page: str, retrieved_on: date,
                 approved_urls: set[str] = frozenset()) -> tuple[list[Chunk], dict]:
    soup = BeautifulSoup(page, "html.parser")
    known_pages = site_pages(soup, approved_urls)
    removed: list[str] = []
    report = {"source_id": source.source_id, "url": source.url, "removed": removed, "warnings": [], "rewrites": [],
              "broken_links": []}
    last_updated, basis = page_date(soup)
    if last_updated is None:
        report["warnings"].append("no last-updated date on the page (audit O-02)")
    page_text = clean_text(BeautifulSoup(page, "html.parser").get_text(" "))
    page_words = words(page_text)

    if source.source_id == "OFF-01":
        faqs, faq_report = extract_faq(page, retrieved_on, source.url, rewrite=False)
        removed.extend(faq_report["removed_boilerplate"])
        report["warnings"].extend(faq_report["warnings"])
        title = "HisabDo Help Center FAQ"
        raw = [{"section": f.section, "heading": f.question, "body": f.answer, "kind": "qa"} for f in faqs]
    else:
        title, raw = sections_of_page(soup, source.url, removed)

    language = language_of(soup, page_text)
    due = (retrieved_on + timedelta(days=REVIEW_DAYS.get(source.review_policy, 30))).isoformat()
    chunks = []
    for n, r in enumerate(raw, 1):
        body, fixes = contextualise(r["body"])
        body, link_fixes = fix_links(body, known_pages, report)
        fixes += link_fixes
        if fixes:
            report["rewrites"].append({"heading": r["heading"], "fixes": fixes})
        # Meaning check, before the link and wording rewrites (which are listed in the report).
        for s in unsupported_sentences(r["body"], page_words):
            report["warnings"].append(f"NOT FOUND ON PAGE ({r['heading']}): {s[:120]}")
        area, scope = classify(r["heading"], body, source)
        c = Chunk(
            id=f"{source.source_id.lower()}-{n:03d}-{slugify(r['heading'])[:48].strip('-')}",
            title=title, section=r["section"], heading=r["heading"], body=body, category=source.category,
            source_id=source.source_id, source_url=source.url, language=language, last_updated=last_updated,
            last_updated_basis=basis, area=area, scope=scope, usage=source.usage, owner=source.owner,
            approval=source.approval, review_policy=source.review_policy,
            retrieved_on=retrieved_on.isoformat(), next_review_due=due)
        chunks.append(c)
    return chunks, report


def shingles(text: str, n: int = 4) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z0-9]+", plain(text).lower())
    return {tuple(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


def remove_duplicates(chunks: list[Chunk], priority: dict[str, int], contained: float = 0.8,
                      reworded: float = 0.85) -> tuple[list[Chunk], list[dict]]:
    """Drop a chunk that repeats one from an equally or more authoritative source.

    Repeat = at least `contained` of its 4-word phrases appear in the other chunk, or the same
    answer lightly reworded (word-sequence similarity >= `reworded`). Rewording is not applied
    between legal chunks: each legal document keeps its own sections even when they read alike.
    Partial overlap is kept, because each copy then says something the other does not.
    """
    # Most authoritative source first; between equals, the most recently updated page wins.
    order = sorted(range(len(chunks)), key=lambda i: chunks[i].last_updated or "", reverse=True)
    order = sorted(order, key=lambda i: priority[chunks[i].source_id])
    kept, dropped, grams, tokens = [], [], {}, {}
    for i in order:
        c = chunks[i]
        g = shingles(c.body)
        t = re.findall(r"[a-z0-9]+", plain(c.body).lower())
        twin, how = None, ""
        if len(g) >= 3:
            for k in kept:
                overlap = len(g & grams[k.id]) / len(g)
                if overlap >= contained:
                    twin, how = k, f"{overlap:.0%} of its text is in the other chunk"
                    break
                if overlap >= 0.5 and "legal" not in (c.scope, k.scope):
                    ratio = difflib.SequenceMatcher(None, t, tokens[k.id], autojunk=False).ratio()
                    if ratio >= reworded:
                        twin, how = k, f"same answer reworded ({ratio:.0%} word-sequence similarity)"
                        break
        if twin:
            dropped.append({"removed": c.id, "heading": c.heading, "duplicate_of": twin.id, "reason": how})
        else:
            kept.append(c)
            grams[c.id], tokens[c.id] = g, t
    keep_ids = {c.id for c in kept}
    return [c for c in chunks if c.id in keep_ids], dropped


CURRENCY = re.compile(r"\b(PKR|INR|USD|AED)\b")


def flag_conflicts(chunks: list[Chunk]) -> list[dict]:
    """Facts that differ between approved sources. Both sides stay in the KB, marked for confirmation."""
    conflicts = []
    stated = {c.id: set(CURRENCY.findall(c.body)) for c in chunks if "currenc" in (c.heading + c.body).lower()}
    stated = {k: v for k, v in stated.items() if len(v) >= 2}
    if len({frozenset(v) for v in stated.values()}) > 1:
        by_id = {c.id: c for c in chunks}
        versions: dict[str, list[str]] = {}
        for cid, codes in stated.items():
            c = by_id[cid]
            versions.setdefault(", ".join(sorted(codes)), []).append(
                f"{c.source_id} ({c.last_updated or 'undated'})")
        summary = "; ".join(f"{', '.join(sorted(set(srcs)))} list {codes}" for codes, srcs in sorted(versions.items()))
        for cid in stated:
            by_id[cid].status = "needs_confirmation"
            by_id[cid].notes.append(f"Currency list differs between official sources (audit C-06): {summary}. "
                                    "Answer with the source and its date, or confirm with the product owner.")
        conflicts.append({"fact": "supported currencies", "audit_ref": "C-06",
                          "statements": {k: sorted(v) for k, v in stated.items()}})
    return conflicts


# ------------------------------------------------------------------------------------ output


def to_markdown(c: Chunk) -> str:
    def q(v) -> str:
        return json.dumps(v, ensure_ascii=False)

    meta = {k: v for k, v in asdict(c).items() if k not in ("body", "notes")}
    lines = [f"{k}: {q(v) if isinstance(v, str) or v is None else v}" for k, v in meta.items()]
    if c.notes:
        lines.append("notes:")
        lines += [f"  - {q(n)}" for n in c.notes]
    return "---\n" + "\n".join(lines) + "\n---\n\n" + f"## {c.heading}\n\n{c.body}\n"


def write(chunks: list[Chunk], reports: list[dict], duplicates: list[dict], conflicts: list[dict],
          out_dir: Path) -> None:
    chunk_dir = out_dir / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    for old in chunk_dir.glob("*.md"):
        old.unlink()
    for c in chunks:
        c.content_sha256 = hashlib.sha256(f"{c.heading}\n{c.body}".encode("utf-8")).hexdigest()
        (chunk_dir / f"{c.id}.md").write_text(to_markdown(c), encoding="utf-8")
    with (out_dir / "kb_chunks.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for c in chunks:
            f.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")
    summary = {
        "chunk_count": len(chunks),
        "sources": sorted({c.source_id for c in chunks}, key=lambda s: (s[:3], int(s.split("-")[1]))),
        "by_category": count(c.category for c in chunks),
        "by_area": count(c.area for c in chunks),
        "by_language": count(c.language for c in chunks),
        "needs_confirmation": [c.id for c in chunks if c.status != "active"],
        "duplicates_removed": duplicates,
        "conflicts": conflicts,
        "per_source": [{**r, "removed": r["removed"]} for r in reports],
    }
    (out_dir / "cleaning_report.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                                                  encoding="utf-8")


def count(values) -> dict:
    out: dict[str, int] = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


def latest_snapshot_dir() -> Path:
    dirs = sorted(d for d in SNAPSHOTS.iterdir() if d.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d.name))
    if not dirs:
        raise SystemExit("no snapshots: run with --fetch first")
    return dirs[-1]


def run(snapshot_dir: Path, out_dir: Path, retrieved_on: date) -> dict:
    sources = approved_sources()
    all_chunks, reports = [], []
    for s in sources:
        page = (snapshot_dir / f"{s.source_id}.html").read_text(encoding="utf-8")
        chunks, report = clean_source(s, page, retrieved_on, {x.url for x in sources})
        all_chunks += chunks
        reports.append(report)
    priority = {s.source_id: s.priority for s in sources}
    kept, duplicates = remove_duplicates(all_chunks, priority)
    conflicts = flag_conflicts(kept)
    write(kept, reports, duplicates, conflicts, out_dir)
    return {"sources": len(sources), "chunks_before_dedup": len(all_chunks), "chunks": len(kept),
            "duplicates": duplicates, "conflicts": conflicts, "reports": reports}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fetch", action="store_true", help="download today's snapshots of every approved source first")
    ap.add_argument("--snapshots", help="snapshot folder (default: the latest under data/kb/sources)")
    ap.add_argument("--out", default=str(OUT_DIR))
    args = ap.parse_args()

    if args.fetch:
        snapshot_dir = SNAPSHOTS / date.today().isoformat()
        for s in approved_sources():
            fetch(s, snapshot_dir)
    else:
        snapshot_dir = Path(args.snapshots) if args.snapshots else latest_snapshot_dir()
    result = run(snapshot_dir, Path(args.out), date.fromisoformat(snapshot_dir.name))

    print(f"{result['sources']} approved sources -> {result['chunks']} chunks "
          f"({result['chunks_before_dedup'] - result['chunks']} duplicates removed) in {args.out}")
    for r in result["reports"]:
        print(f"  {r['source_id']:8} removed {len(r['removed']):3} UI/furniture blocks, "
              f"{len(r['rewrites'])} wording rewrites, {len(r['warnings'])} warnings")
        for w in r["warnings"]:
            print(f"           WARNING: {w}")
    for d in result["duplicates"]:
        print(f"  duplicate: {d['removed']} == {d['duplicate_of']}")
    for c in result["conflicts"]:
        print(f"  conflict ({c['audit_ref']}): {c['fact']}: {c['statements']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
