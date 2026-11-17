"""Content cleaning of the approved product FAQ (scripts/clean_product_faqs.py).

Uses the saved official page tests/fixtures/hisabdo_faq_2026-10-26.html, so the
tests run offline and do not change when the live site changes. The KB output for
the FAQ is now produced by clean_knowledge_sources.py (tests/test_clean_knowledge_sources.py).
"""

import re
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from clean_product_faqs import clean_text, extract, to_markdown, write  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "hisabdo_faq_2026-10-26.html"
DAY = date(2026, 10, 26)

BOILERPLATE = ["Download Free", "Contact Support", "Ready to Get Started", "Frequently Asked Questions",
               "questions answered", "Everything you need to know", "Write a Blog", "Careers", "Get App",
               "XICTEK Systems. All rights", "footer", "this website"]


@pytest.fixture(scope="module")
def result():
    return extract(FIXTURE.read_text(encoding="utf-8"), DAY)


def test_every_faq_on_the_page_becomes_one_chunk(result):
    chunks, _ = result
    assert len(chunks) == 33
    assert len({c.id for c in chunks}) == 33 and len({c.question for c in chunks}) == 33
    assert [c.section for c in chunks][:1] == ["General"]
    assert {c.section for c in chunks} == {"General", "Features", "Language & Currency", "Data & Backup",
                                           "Privacy & Security", "Device & Platform", "Support"}


def test_ui_boilerplate_and_navigation_are_stripped(result):
    chunks, report = result
    for c in chunks:
        text = to_markdown(c)
        for phrase in BOILERPLATE:
            assert phrase.lower() not in c.answer.lower() and phrase not in c.question, (c.id, phrase)
        assert "<" not in c.answer and "&amp;" not in text
    assert any(b.startswith("header:") for b in report["removed_boilerplate"])
    assert any(b.startswith("footer:") for b in report["removed_boilerplate"])


def test_no_formatting_glitches_remain(result):
    chunks, _ = result
    for c in chunks:
        for field in (c.question, c.answer):
            assert "  " not in field and field == field.strip(), c.id
            assert not re.search("[ ​‌‍﻿‘’“”]", field), c.id
            assert not re.search("[\U0001F000-\U0001FAFF☀-➿]", field), c.id
            assert not re.search(r"\s[,.;:!?]", field), c.id


def test_every_chunk_carries_source_and_review_metadata(result):
    chunks, _ = result
    for c in chunks:
        assert c.source_url == "https://hisabdo.app/faq"
        assert c.owner and c.approval.startswith("Approved")
        assert c.retrieved_on == c.last_verified == "2026-10-26"
        assert c.review_policy == "P-FAQ" and c.next_review_due == "2026-11-25"
        assert re.fullmatch(r"[0-9a-f]{64}", c.content_sha256)
        assert to_markdown(c).startswith("---\nid: ") and f"## {c.question}" in to_markdown(c)


def test_known_issues_are_reported_not_hidden(result):
    chunks, report = result
    assert any("30 questions answered" in w and "33" in w for w in report["warnings"])
    currency = next(c for c in chunks if c.question == "Which currencies does HisabDo support?")
    assert "C-06" in currency.notes and "AED" in currency.notes


def test_links_become_markdown_and_support_email_stays_plain(result):
    chunks, _ = result
    contact = next(c for c in chunks if c.question == "How do I contact HisabDo support?")
    assert "hisabdo.app@gmail.com" in contact.answer and "mailto:" not in contact.answer
    assert "[Contact page](https://hisabdo.app/contact)" in contact.answer
    privacy = [c for c in chunks if "Privacy Policy" in c.answer]
    assert privacy and all("[Privacy Policy](https://hisabdo.app/privacy-policy)" in c.answer for c in privacy)


def test_dirty_html_is_cleaned():
    dirty = """<html><header><nav>Home | Blog</nav></header><main>
      <h1>Frequently Asked Questions</h1><p>3 questions answered.</p>
      <section><h2>General</h2>
        <details class="faq-item"><summary> Is it free ? \U0001F680</summary>
          <p>Yes&nbsp;&amp; it​ is.   Donâ€™t   pay .</p></details>
        <details class="faq-item"><summary>Is it free?</summary><p>Duplicate.</p></details>
        <details class="faq-item"><summary>Empty</summary></details>
        <details class="faq-item"><summary>Export?</summary><p>See <a href="/guide">the <b>guide</b></a>.</p>
          <ul><li>PDF</li><li> CSV </li></ul></details>
      </section><h2>Ready to Get Started?</h2><a href="#">Download Free</a></main>
      <footer>(c) XICTEK</footer></html>"""
    chunks, report = extract(dirty, DAY, base_url="https://hisabdo.app/faq")
    assert [c.question for c in chunks] == ["Is it free?", "Export?"]
    assert chunks[0].answer == "Yes & it is. Don't pay."
    assert chunks[1].answer == "See [the guide](https://hisabdo.app/guide).\n\n- PDF\n- CSV"
    assert any("duplicate" in w for w in report["warnings"]) and any("empty" in w for w in report["warnings"])
    assert any("3 questions answered" in w for w in report["warnings"])


def test_clean_text_unit_cases():
    assert clean_text("cafÃ© “quoted”") == "café \"quoted\""
    assert clean_text("  a\n\tb  ") == "a b"


def test_rerun_is_idempotent_and_reports_changes(result, tmp_path):
    chunks, report = result
    write(chunks, report, tmp_path)
    first = {p.name: p.read_text(encoding="utf-8") for p in tmp_path.iterdir()}
    changes = write(chunks, report, tmp_path)
    assert changes == {"added": [], "changed": [], "removed": []}
    second = {p.name: p.read_text(encoding="utf-8") for p in tmp_path.iterdir()}
    assert {k: v for k, v in first.items() if k != "index.json"} == \
           {k: v for k, v in second.items() if k != "index.json"}

    edited = [replace(c) for c in chunks if c.id != "hisabdo-faq-002"]  # copies: chunks is shared
    edited[0].content_sha256 = "0" * 64
    changes = write(edited, report, tmp_path)
    assert changes["removed"] == ["Is HisabDo free to use?"] and changes["changed"] == [edited[0].question]
    assert len(list(tmp_path.glob("*.md"))) == 32  # stale chunk files are removed
