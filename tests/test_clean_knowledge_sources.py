"""Cleaning and chunking of all approved knowledge sources (scripts/clean_knowledge_sources.py).

Runs on the committed snapshots in data/kb/sources/2026-10-27, so the tests are
offline and do not change when the live site changes.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import clean_knowledge_sources as cks  # noqa: E402
from kb_privacy_scan import scan_file  # noqa: E402

SNAPSHOTS = ROOT / "data" / "kb" / "sources" / "2026-10-27"
COMMITTED = ROOT / "data" / "kb" / "approved"
DAY = date(2026, 10, 27)

UI_TEXT = ["Download Free", "Download App", "Read Article", "Read FAQs", "Related Articles", "About the Author",
           "min read", "Learn more", "View Full Profile", "Write a Blog", "Explore Features", "Get Support",
           "Latest Blog Posts", "WHY USE HISABDO", "See also:", "→", "Ready to Get Started", "questions answered",
           "Home | About", "All rights reserved"]


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("kb")
    result = cks.run(SNAPSHOTS, out, DAY)
    chunks = [json.loads(line) for line in (out / "kb_chunks.jsonl").read_text(encoding="utf-8").splitlines()]
    return result, chunks, out


def test_only_sources_approved_in_the_register_are_cleaned():
    ids = {s.source_id for s in cks.approved_sources()}
    assert len(ids) == 23
    assert {"OFF-01", "OFF-02", "OFF-03", "OFF-04", "OFF-06", "OFF-07", "OFF-08"} <= ids
    assert {f"BLOG-{n:02d}" for n in range(1, 17)} <= ids
    assert not ids & {"OFF-05", "OFF-09"}  # user reviews and marketing videos are not approved
    assert not any(i.startswith("REPO-") for i in ids)  # repository files have no approval record


def test_committed_output_is_exactly_what_the_cleaner_produces(built):
    """data/kb/approved must be regenerated whenever the cleaner, the register or a snapshot changes."""
    _, _, out = built
    for name in ("kb_chunks.jsonl", "cleaning_report.json"):
        assert (COMMITTED / name).read_text(encoding="utf-8") == (out / name).read_text(encoding="utf-8"), name
    fresh = {p.name: p.read_text(encoding="utf-8") for p in (out / "chunks").glob("*.md")}
    committed = {p.name: p.read_text(encoding="utf-8") for p in (COMMITTED / "chunks").glob("*.md")}
    assert committed == fresh


def test_every_chunk_has_the_required_metadata(built):
    _, chunks, _ = built
    assert len(chunks) > 300 and len({c["id"] for c in chunks}) == len(chunks)
    for c in chunks:
        assert c["title"] and c["section"] and c["heading"] and c["body"], c["id"]
        assert c["category"] in {"product_faq", "product_guide", "legal_policy", "finance_guide"}
        assert c["source_url"].startswith("https://") and c["source_id"]
        assert c["language"] == "en"
        assert c["last_updated"] is None or re.fullmatch(r"\d{4}-\d{2}(-\d{2})?", c["last_updated"])
        assert c["last_updated_basis"]
        assert c["area"] and c["scope"] in {"product", "company", "legal", "general_finance"}
        assert c["owner"] and c["approval"].startswith("Approved") and c["review_policy"].startswith("P-")
        assert c["retrieved_on"] == "2026-10-27" and c["next_review_due"] > c["retrieved_on"]
        assert re.fullmatch(r"[0-9a-f]{64}", c["content_sha256"])
        assert c["usage"] == ("reference_only" if c["category"] == "legal_policy" else "answer")


def test_dates_come_from_the_page_and_are_never_invented(built):
    _, chunks, _ = built
    first = {c["source_id"]: c for c in reversed(chunks)}
    assert first["BLOG-02"]["last_updated"] == "2025-07-14"
    assert first["OFF-06"]["last_updated"] == "2026-09-24"
    assert first["OFF-08"]["last_updated"] == "2026-04"  # the page gives a month only
    assert first["OFF-04"]["last_updated"] == "2026-10-13"
    for undated in ("OFF-01", "OFF-02", "OFF-03", "BLOG-06", "BLOG-07"):  # audit O-02
        assert first[undated]["last_updated"] is None
        assert first[undated]["last_updated_basis"] == "not shown on the page"


def test_navigation_footer_and_ui_text_are_removed(built):
    result, chunks, _ = built
    for c in chunks:
        text = c["heading"] + "\n" + c["body"]
        for phrase in UI_TEXT:
            assert phrase not in text, (c["id"], phrase)
        assert "<" not in c["body"]
    for r in result["reports"]:
        assert any(x.startswith("header:") for x in r["removed"]), r["source_id"]


def test_irrelevant_sections_are_removed(built):
    result, chunks, _ = built
    removed = [x for r in result["reports"] for x in r["removed"]]
    for gone in ("irrelevant section: Latest Blog Posts", "irrelevant section: Application Screens",
                 "irrelevant section: Apna business ka tajurba share karein", "keyword list: WHY USE HISABDO? (14 lines)",
                 "author biography"):
        assert gone in removed
    headings = {c["heading"] for c in chunks}
    assert not headings & {"Latest Blog Posts", "Application Screens", "Why Use Hisabdo?"}


def test_no_sentence_is_added_or_changed(built):
    result, _, _ = built
    assert [w for r in result["reports"] for w in r["warnings"] if w.startswith("NOT FOUND")] == []


def test_meaning_check_catches_changed_wording():
    page = cks.words("HisabDo supports PKR, USD and INR. Backups are stored on your device.")
    assert cks.unsupported_sentences("HisabDo supports PKR, USD and INR.", page) == []
    assert cks.unsupported_sentences("- HisabDo supports PKR, USD and INR.\n- Backups are stored on your device.",
                                     page) == []
    assert cks.unsupported_sentences("HisabDo supports PKR, USD, INR and AED.", page) != []
    assert cks.unsupported_sentences("Backups are stored in the cloud.", page) != []


def test_duplicates_are_removed_keeping_the_authoritative_or_newest_copy(built):
    result, chunks, _ = built
    pairs = {(d["removed"].split("-")[0] + "-" + d["removed"].split("-")[1] + "-" + d["removed"].split("-")[2],
              d["duplicate_of"].split("-")[0] + "-" + d["duplicate_of"].split("-")[1] + "-" + d["duplicate_of"].split("-")[2])
             for d in result["duplicates"]}
    assert ("blog-07-014", "off-01-017") in pairs  # blog repeats the official FAQ answer: FAQ kept
    assert ("blog-03-013", "blog-08-017") in pairs  # same answer in two posts: April 2026 post kept over July 2025
    grams = {c["id"]: cks.shingles(c["body"]) for c in chunks}
    for a in chunks:
        for b in chunks:
            ga, gb = grams[a["id"]], grams[b["id"]]
            if a["id"] != b["id"] and len(ga) >= 3:
                assert len(ga & gb) / len(ga) < 0.8, (a["id"], b["id"])


def test_partial_overlap_is_not_treated_as_a_duplicate(built):
    _, chunks, _ = built
    ids = {"-".join(c["id"].split("-")[:3]) for c in chunks}
    assert {"blog-01-021", "blog-09-012"} <= ids  # both "hire an accountant" answers say something the other does not
    assert {"off-07-013", "off-08-009"} <= ids  # each legal document keeps its own contact section


def test_conflicting_facts_are_flagged_not_resolved(built):
    result, chunks, _ = built
    flagged = {c["id"][:10]: c for c in chunks if c["status"] == "needs_confirmation"}
    assert set(flagged) == {"off-01-019", "off-02-010", "off-04-010"}
    for c in flagged.values():
        assert "C-06" in c["notes"][0] and "OFF-04 (2026-10-13)" in c["notes"][0]
    assert "PKR" in flagged["off-01-019"]["body"] and "AED" not in flagged["off-01-019"]["body"]
    assert "AED" in flagged["off-04-010"]["body"]
    assert result["conflicts"][0]["audit_ref"] == "C-06"


def test_links_only_point_to_pages_that_exist(built):
    _, chunks, _ = built
    site = BeautifulSoup((SNAPSHOTS / "OFF-03.html").read_text(encoding="utf-8"), "html.parser")
    known = cks.site_pages(site, {s.url for s in cks.approved_sources()})
    for c in chunks:
        for url in re.findall(r"\]\((https://hisabdo\.app[^)#]*)", c["body"]):
            assert url.rstrip("/") in known, (c["id"], url)


def test_chunks_are_retrieval_sized_and_areas_are_sensible(built):
    _, chunks, _ = built
    assert all(len(c["body"]) <= 1600 for c in chunks)
    area = {c["id"][:10]: c["area"] for c in chunks}
    assert area["off-01-003"] == "Company"
    assert area["off-01-012"] == "Suppliers & Payables"
    assert area["off-01-014"] == "Voice Entry"
    assert area["off-01-018"] == "Language & Currency"
    assert area["off-01-029"] == "Platform & Devices"
    assert all(c["area"] == "Legal & Policy" for c in chunks if c["category"] == "legal_policy")
    assert all(c["area"] not in cks.PRODUCT_ONLY_AREAS for c in chunks if c["scope"] == "general_finance")


def test_output_passes_the_privacy_gate():
    for path in [*sorted((COMMITTED / "chunks").glob("*.md")), COMMITTED / "kb_chunks.jsonl",
                 COMMITTED / "cleaning_report.json"]:
        findings = [h for h in scan_file(path) if "(allowed" not in h[1]]
        assert findings == [], f"{path.name}: {findings}"


def test_synthetic_article_is_cleaned_and_chunked():
    page = """<html lang="en"><header><a href="/">Home</a><a href="/contact">Contact</a></header><main>
      <section class="hero"><div class="badge">Guide</div><h1>Test Guide \U0001F4D2</h1>
        <p>Intro  paragraph&nbsp;here .</p><p class="hero-note">By X • Published: May 8, 2026 • 9 min read</p>
        <div class="hero-buttons"><a class="btn" href="#">Download Free</a></div></section>
      <section><nav class="toc"><a href="#a">Part A</a></nav>
        <h2>Part A</h2><p>First fact. It is a full paragraph, long enough to stand as its own section in the knowledge base without being merged into the next one. A second sentence adds length.</p><p>See also: <a href="/x">Other</a></p>
        <h2>Short Intro</h2><p>One line.</p>
        <h2>Part B</h2><p>Read <a href="/track-customer-dues">dues</a> and <a href="/gone">gone</a>.</p>
        <p>Related Articles</p><p><a href="/y">→ Y</a></p>
        <h2>Frequently Asked Questions</h2><h3>Q one?</h3><p>A one.</p>
        <details class="faq-item"><summary>Q two?</summary><p>A two.</p></details>
        <p>About the Author</p><p>Bio text.</p></section>
      <section class="hero"><h2>Ready?</h2><a class="btn" href="#">Download Free</a></section></main>
      <footer>(c) 2026</footer></html>"""
    src = cks.Source("BLOG-99", "t", "finance_guide", 4, "https://hisabdo.app/blog/test", "o", "Approved", "P-FAQ",
                     "answer")
    chunks, report = cks.clean_source(src, page, DAY, {"https://hisabdo.app/blog/track-customer-dues"})
    got = [(c.section, c.body) for c in chunks]
    assert got == [
        ("Overview", "Intro paragraph here."),
        ("Part A", "First fact. It is a full paragraph, long enough to stand as its own section in the knowledge base "
                   "without being merged into the next one. A second sentence adds length."),
        ("Short Intro > Part B", "One line.\n\nRead [dues](https://hisabdo.app/blog/track-customer-dues) and gone."),
        ("Frequently Asked Questions", "A one."),
        ("Frequently Asked Questions", "A two."),
    ]
    assert chunks[0].title == "Test Guide" and chunks[0].last_updated == "2026-05-08"
    assert [c.heading for c in chunks[3:]] == ["Q one?", "Q two?"]
    assert report["broken_links"] == ["https://hisabdo.app/gone"]
    assert not [w for w in report["warnings"] if w.startswith("NOT FOUND")]
    assert "author biography" in report["removed"] and "Ready? Download Free" in report["removed"]
