"""
Unit tests for citation_validator.validate_citations()

Covers each of the 4 mandatory checks + the informational CHECK 5:
  - test_check_1_pass: well-formed response → CHECK 1 passes
  - test_check_1_orphan_marker: body cites [3] not in Sources → CHECK 1 fails
  - test_check_2_pass: well-formed response → CHECK 2 passes
  - test_check_2_padded_source: Sources has [2] never cited → CHECK 2 fails
  - test_check_3_pass: indices within retrieved range → CHECK 3 passes
  - test_check_3_fabricated_index: cites [5] with 2 retrieved → CHECK 3 fails
  - test_check_4_pass: blog URLs only → CHECK 4 passes
  - test_check_4_bad_url: hisabdo.app URL → CHECK 4 fails
  - test_check_5_verbatim_match: quoted text appears in source → CHECK 5 passes
  - test_check_5_verbatim_mismatch: quoted text not in source → CHECK 5 fails
  - test_overall_pass_clean: clean response → overall_pass = True
  - test_overall_fail_multiple: multiple defects → overall_pass = False

Usage:
    python -m pytest tests/test_citation_validator.py -v
    # or:
    python3 tests/test_citation_validator.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.citation_validator import validate_citations

ARTICLES = [
    {
        "slug": "custom-software-development-guide",
        "title": "Custom Software Development Guide for Growing Businesses",
        "body": "Custom software development typically begins with a discovery phase to map business workflows before any code is written. The cost varies based on scope, complexity, and team composition.",
    },
    {
        "slug": "software-development-cost-pakistan",
        "title": "Software Development Cost in Pakistan: What Shapes the Budget",
        "body": "The cost of software development in Pakistan depends on scope and complexity. Typical projects range from $5,000 to $50,000.",
    },
    {
        "slug": "agile-software-development",
        "title": "Agile Software Development: A Practical Guide",
        "body": "Agile is an iterative software development process that breaks work into sprints of 1-4 weeks. The process emphasizes continuous feedback.",
    },
]

BLOG_URL = "https://www.xicteksystems.com/blog/{slug}"


def _url(slug):
    return BLOG_URL.format(slug=slug)


# ============================================================
# CHECK 1 — orphan markers
# ============================================================
def test_check_1_pass():
    response = (
        "Discovery comes first [1]. Cost varies by scope [2].\n\n"
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
        f"[2] {ARTICLES[1]['title']} — {_url(ARTICLES[1]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert r["checks"]["check_1_orphan_markers"]["passed"], \
        f"CHECK 1 should pass but failed: {r['errors']}"


def test_check_1_orphan_marker():
    # Body cites [3] but Sources only has [1]
    response = (
        "Some claim [1]. Another claim [3].\n\n"
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert not r["checks"]["check_1_orphan_markers"]["passed"], \
        "CHECK 1 should fail (orphan [3])"
    assert 3 in r["checks"]["check_1_orphan_markers"]["orphan_markers"]


# ============================================================
# CHECK 2 — padded sources
# ============================================================
def test_check_2_pass():
    response = (
        "Discovery comes first [1].\n\n"
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert r["checks"]["check_2_padded_sources"]["passed"]


def test_check_2_padded_source():
    # Body cites [1] only; Sources lists [1] and [2]
    response = (
        "Discovery comes first [1].\n\n"
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
        f"[2] {ARTICLES[1]['title']} — {_url(ARTICLES[1]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert not r["checks"]["check_2_padded_sources"]["passed"]
    assert 2 in r["checks"]["check_2_padded_sources"]["padded_sources"]


# ============================================================
# CHECK 3 — fabricated index
# ============================================================
def test_check_3_pass():
    response = (
        "Discovery comes first [1]. Cost varies [2].\n\n"
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
        f"[2] {ARTICLES[1]['title']} — {_url(ARTICLES[1]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert r["checks"]["check_3_fabricated_index"]["passed"]


def test_check_3_fabricated_index():
    # Cites [5] when only 3 articles retrieved
    response = (
        "Some claim [5].\n\n"
        "**Sources:**\n"
        f"[5] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert not r["checks"]["check_3_fabricated_index"]["passed"]
    assert 5 in r["checks"]["check_3_fabricated_index"]["fabricated_indices"]


# ============================================================
# CHECK 4 — URL allowlist
# ============================================================
def test_check_4_pass():
    response = (
        "Discovery comes first [1].\n\n"
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert r["checks"]["check_4_url_allowlist"]["passed"]


def test_check_4_bad_url():
    # hisabdo.app URL — not on /blog/ path
    response = (
        "Hisabdo is an expense app [1].\n\n"
        "**Sources:**\n"
        "[1] Hisabdo Features — https://hisabdo.app/features\n"
    )
    r = validate_citations(response, ARTICLES)
    assert not r["checks"]["check_4_url_allowlist"]["passed"]


def test_check_4_services_url_blocked():
    # /services URL — wrong path
    response = (
        "See our services [1].\n\n"
        "**Sources:**\n"
        "[1] Services — https://www.xicteksystems.com/services\n"
    )
    r = validate_citations(response, ARTICLES)
    assert not r["checks"]["check_4_url_allowlist"]["passed"]


# ============================================================
# CHECK 5 — verbatim quotes (informational)
# ============================================================
def test_check_5_verbatim_match():
    # Quote actually appears in article body
    response = (
        'The article says "discovery phase to map business workflows" [1].\n\n'
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert r["checks"]["check_5_verbatim_quotes"]["passed"]


def test_check_5_verbatim_mismatch():
    # Quote does NOT appear in article body — fabricated quote
    response = (
        'The article says "Python is the best language for everything" [1].\n\n'
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert not r["checks"]["check_5_verbatim_quotes"]["passed"]


# ============================================================
# Overall verdict
# ============================================================
def test_overall_pass_clean():
    response = (
        "Custom software development starts with discovery [1]. "
        "Cost depends on scope and complexity [2].\n\n"
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — {_url(ARTICLES[0]['slug'])}\n"
        f"[2] {ARTICLES[1]['title']} — {_url(ARTICLES[1]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert r["overall_pass"], f"Expected overall pass, got errors: {r['errors']}"


def test_overall_fail_multiple():
    # Multiple defects: orphan [3], fabricated [5], bad URL
    response = (
        "Claim [3]. Claim [5].\n\n"
        "**Sources:**\n"
        f"[3] {ARTICLES[0]['title']} — https://hisabdo.app/features\n"
    )
    r = validate_citations(response, ARTICLES)
    assert not r["overall_pass"]
    assert len(r["errors"]) >= 3, \
        f"Expected ≥3 errors, got {len(r['errors'])}: {r['errors']}"


# ============================================================
# Edge cases
# ============================================================
def test_no_sources_block():
    # Body has markers but no Sources block at all
    response = "Some claim [1]."
    r = validate_citations(response, ARTICLES)
    assert not r["overall_pass"]
    assert not r["checks"]["check_1_orphan_markers"]["passed"]


def test_markdown_link_form():
    # Sources uses [Title](URL) form
    response = (
        "Discovery comes first [1].\n\n"
        "**Sources:**\n"
        f"[1] [{ARTICLES[0]['title']}]({_url(ARTICLES[0]['slug'])})\n"
    )
    r = validate_citations(response, ARTICLES)
    assert r["overall_pass"], f"Markdown-link form should pass: {r['errors']}"


def test_section_level_citation():
    # Sources entry with § "Section" form
    response = (
        "Discovery comes first [1].\n\n"
        "**Sources:**\n"
        f"[1] {ARTICLES[0]['title']} — § \"Discovery Phase\" — {_url(ARTICLES[0]['slug'])}\n"
    )
    r = validate_citations(response, ARTICLES)
    assert r["overall_pass"], f"Section-level citation should pass: {r['errors']}"
    assert r["sources_entries"][0]["section"] == "Discovery Phase"


# ============================================================
# Runner
# ============================================================
def run_all():
    tests = [
        name for name in globals()
        if name.startswith("test_") and callable(globals()[name])
    ]
    passed = 0
    failed = 0
    for name in tests:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {name}: {type(e).__name__}: {e}")
            failed += 1
    print()
    print(f"Result: {passed}/{len(tests)} tests passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all())
