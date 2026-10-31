# Content Cleaning — Product FAQs

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-10-26 · **Branch:** `FahadZubairi_AI`

> **Superseded on 2026-10-27** by [kb-content-cleaning.md](kb-content-cleaning.md). The FAQ is now cleaned
> together with every other approved source by `scripts/clean_knowledge_sources.py`, into `data/kb/approved/`.
> `data/kb/product_faqs/` was removed so the FAQ answers are not in the KB twice. The FAQ cleaner below is
> still used as the FAQ reader inside the new pipeline.

## 1. Scope

The only **approved** product FAQ is the official Help Center, <https://hisabdo.app/faq>
(source `OFF-01` in [dept3-knowledge-source-audit.md](dept3-knowledge-source-audit.md)). No FAQ text in the
repository has an approval record, so nothing else was cleaned. The page was retrieved on 2026-10-26.

## 2. Output

| Path | What it is |
|---|---|
| `data/kb/product_faqs/hisabdo-faq-NNN-<slug>.md` | 33 Markdown chunks, one question + answer each |
| `data/kb/product_faqs/index.json` | Manifest: metadata for every chunk, warnings, changes since the last run |
| `scripts/clean_product_faqs.py` | The cleaner (fetches the live page or reads a saved copy) |
| `tests/fixtures/hisabdo_faq_2026-10-26.html` | Saved copy of the page, so the tests run offline |
| `tests/test_clean_product_faqs.py` | 11 tests |

Chunk format (front matter is YAML; string values are JSON-quoted):

```markdown
---
id: hisabdo-faq-016
question: "Can I add notes to transactions?"
section: "Features"
source_url: https://hisabdo.app/faq
owner: "Mian Usman Khalid (founder, XICTEK Systems)"
approval: "Approved (official publication)"
retrieved_on: 2026-10-26
last_verified: 2026-10-26
review_policy: P-FAQ
next_review_due: 2026-11-25
content_sha256: e022cd77…
---

## Can I add notes to transactions?

Yes. You can add descriptive notes to any transaction entry, …
```

The chunks are split by question so retrieval returns one complete answer, never half of one or two
answers merged. The `## question` heading stays inside the chunk so the question text is embedded with the
answer. Sections: Features 11, General 5, Data & Backup 4, Privacy & Security 4, Language & Currency 3,
Device & Platform 3, Support 3.

## 3. What was removed

Only `<details class="faq-item">` blocks inside `<main>` are kept. The section comes from the nearest
preceding `<h2>`. Everything else is UI boilerplate:

| Removed | Content |
|---|---|
| Header navigation | Home, About, App, Company, Founder, Leadership, Blog, Write a Blog, FAQ, Careers, Contact, Privacy Policy, Get App |
| Page intro | "Frequently Asked Questions", "Everything you need to know…", "30 questions answered. Can't find what you need? Contact us." |
| Call to action | "Ready to Get Started?", "Download HisabDo free…", "Download Free", "Contact Support", "🚀 Available on Google Play" |
| Footer | Tagline, XICTEK attribution, Explore / Legal link lists, copyright line, social icons |
| Scripts and styles | All `<script>` / `<style>` content (never read as text) |

The cleaner prints this list on every run, so a reviewer can see exactly what was dropped.

## 4. Formatting glitches fixed

| Glitch | Fix | Found on this page? |
|---|---|---|
| Repeated spaces, tabs, line breaks inside answers | Collapsed to one space | Yes: faq-031, faq-032 |
| Space before punctuation (`word .`) | Removed | Checked, none |
| HTML entities (`&amp;`, `&nbsp;`) | Decoded | Checked, none in FAQ text |
| Non-breaking / zero-width spaces, BOM | Removed | Checked, none |
| Mojibake (`donâ€™t`) | Repaired run by run (cp1252 → UTF-8) | Checked, none |
| Curly quotes | Straight quotes | Checked, none |
| Emoji / decorative symbols | Removed | Only in the removed CTA |
| Links | `[label](absolute URL)`; e-mail addresses kept as plain text | Yes: Support answers |

The page passed the checks that found nothing because it is well formed today. They stay in the cleaner
because the page will change, and the tests feed it deliberately broken HTML to prove each one works.

### Website-relative wording

Some answers only make sense on the website. Inside a chatbot reply they point nowhere, so they were rewritten
with links taken from the page's own navigation. The meaning is not changed.

| Chunk | Original | Cleaned |
|---|---|---|
| faq-005 | "use the download link on this website" | "…on [hisabdo.app](https://hisabdo.app)" |
| faq-025, faq-026 | "see our Privacy Policy" | "see our [Privacy Policy](https://hisabdo.app/privacy-policy)" |
| faq-031 | "through our Contact page" | "through our [Contact page](https://hisabdo.app/contact)" |
| faq-033 | "Links are available in the footer of this website." | "Links to the official profiles are on [hisabdo.app](https://hisabdo.app)." |

Social profile URLs are deliberately **not** put in the chunks. `scripts/kb_privacy_scan.py` blocks profile
links in the knowledge base, and an exception for company profiles would weaken that gate for every source.

## 5. Issues found (reported, not silently changed)

| # | Issue | Handling |
|---|---|---|
| 1 | The page says **"30 questions answered"** but contains **33** | Warning in `index.json`; to be fixed on the website (owner: web team) |
| 2 | faq-019 currencies: the FAQ lists PKR, USD, INR; the Google Play listing (2026-10-13) also lists AED (audit **C-06**) | Answer kept as published; the conflict is recorded in the chunk's `notes` for the product owner to resolve |

The cleaner never edits facts. Facts are corrected at the source (the website), and the next run picks the
correction up.

## 6. Checks

* Privacy gate: all 33 chunks and `index.json` pass `kb_privacy_scan.py`. The only e-mail is the official
  support address, which is on the allowlist.
* Live drift check: re-running against the live page on 2026-10-26 gives `added 0, changed 0, removed 0`.
* Tests: `tests/test_clean_product_faqs.py` covers 33 chunks / 7 sections, boilerplate absent, no glitch
  characters, required metadata, reported issues, link handling, a synthetic dirty-HTML page (entities,
  nbsp, zero-width, mojibake, emoji, duplicate and empty items, relative links, lists), idempotent re-runs
  with change detection, committed files matching the cleaner output, and the privacy gate.
* Full suite: 541 passed, 4 skipped. The 26 failures are pre-existing failures in `tests/xictek_website_assistant`,
  unchanged by this work.

## 7. How to re-run (P-FAQ: every 30 days and within 7 days of each app release)

```bash
python scripts/clean_product_faqs.py
```

Read the output. `changes since last run` names every added, changed or removed question. Review those
chunks, update `tests/fixtures/` with the new page if you want the tests to follow it, run
`python -m pytest tests/test_clean_product_faqs.py`, and commit.

## 8. Not done here

* The chunks are **not yet loaded into the live chatbot** (`data/faq_docs.json`). Swapping retrieval to these
  chunks changes TF-IDF scores and needs the release-gate evaluation re-run. That is a separate change.
* Only the English page exists; there is no approved Urdu FAQ to clean.
