# Knowledge Base Content Cleaning — All Approved Sources

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-10-27 · **Branch:** `FahadZubairi_AI`
**Builds on:** [dept3-knowledge-source-audit.md](dept3-knowledge-source-audit.md) (which sources are approved) and
[product-faq-cleaning.md](product-faq-cleaning.md) (the FAQ cleaner, now one part of this pipeline).

## 1. Result

| | |
|---|---|
| Approved sources cleaned | **23** (FAQ, About the App, home page, Google Play listing, Privacy Policy, Terms, Disclaimer, 16 blog articles) |
| Chunks in the KB | **364** (product FAQ 33, product guides 37, legal 40, finance guides 254) |
| UI / navigation blocks removed | **286** (listed per source in `cleaning_report.json`) |
| Irrelevant sections removed | 4 (blog teasers, screenshot gallery, write-a-blog call to action, Play keyword list) |
| Duplicate chunks removed | 2 |
| Facts flagged as conflicting | 1 (supported currencies, audit C-06: 3 chunks) |
| Sentences not found in their source | **0** (checked automatically for every chunk) |
| Broken links repaired or removed | 1 repaired; 95 broken article links reported to the website owner |
| Privacy gate | Clean (only the allowlisted support address) |

## 2. Which sources, and why only these

The register `data/knowledge_source_audit.csv` decides. The cleaner takes every official publication (`OFF-*`,
`BLOG-*`) whose verdict starts with "Keep" and whose approval status is "Approved". That gives 23 sources.

Not cleaned, on purpose:

| Source | Reason |
|---|---|
| OFF-05 Google Play user reviews | Personal data of reviewers; audit verdict "Do not ingest". The Play snapshot keeps only the "About this app" section, so no review text is even stored. |
| OFF-09 YouTube channel | Marketing video, not instructional (P-NONE) |
| REPO-01 … REPO-27 | Repository files have no approval record (audit section 3). They need a content owner's sign-off first. |
| hisabdo.app pages not in the audit (`/about`, `/company`, `/leadership`, `/careers`, `/delete-data`, `/why-i-built-hisabdo`) | Found in the sitemap but never audited. `/delete-data` in particular should be audited and added: users will ask how to delete their data. |

## 3. Output

| Path | Contents |
|---|---|
| `data/kb/approved/chunks/<id>.md` | One Markdown file per chunk: YAML front matter + `## heading` + text |
| `data/kb/approved/kb_chunks.jsonl` | The same chunks, one JSON object per line, for loading into the retriever |
| `data/kb/approved/cleaning_report.json` | Counts, everything removed per source, rewrites, duplicates, conflicts, warnings |
| `data/kb/sources/2026-10-27/<source_id>.html` | Snapshot of each source as retrieved (provenance; the tests run on these) |
| `scripts/clean_knowledge_sources.py` | The pipeline |
| `tests/test_clean_knowledge_sources.py` | 15 tests |

`data/kb/product_faqs/` from 2026-10-26 is **removed**. The same 33 FAQ chunks are now in `data/kb/approved/`
with the full metadata, and keeping both would have put every FAQ answer in the KB twice.

### Metadata on every chunk

```yaml
id: "blog-02-005-track-money-coming-in"
title: "Cash Flow Management for Small Businesses: A Practical Guide"   # page title (h1)
section: "Track Money Coming In"            # page section (h2); "A > B" when a one-line intro was merged in
heading: "Track Money Coming In"            # the question for FAQ chunks
category: "finance_guide"                   # product_faq | product_guide | legal_policy | finance_guide
source_id: "BLOG-02"                        # row in the audit register
source_url: "https://hisabdo.app/blog/cash-flow-management"
language: "en"                              # from <html lang>, checked against the script of the text
last_updated: "2025-07-14"                  # as shown on the page, or null; never guessed
last_updated_basis: "published date shown on the page"
area: "Customers & Receivables (general practice)"
scope: "general_finance"                    # product | company | legal | general_finance
usage: "answer"                             # reference_only for legal pages
owner: "Mian Usman Khalid (founder, XICTEK Systems)"
approval: "Approved (official publication)"
review_policy: "P-FAQ"
retrieved_on: "2026-10-27"
next_review_due: "2026-11-26"
content_sha256: "a3b6…"
status: "active"                            # needs_confirmation when sources disagree
notes: []                                   # why, when status is not active
```

**Area** says which part of the product or company the chunk is about (15 areas, e.g. Data, Backup & Sync;
Customers & Receivables; Reports & PDF Export; Platform & Devices; Company; Legal & Policy). Finance-guide chunks
that never mention HisabDo get `scope: general_finance` and an area suffixed "(general practice)". The chatbot
can then tell general advice ("follow up on overdue balances weekly") apart from statements about the app.

**Last-updated** comes only from the page: the blog "Published" date, the legal "Effective Date", or Google
Play's "Updated on". Five sources show no date (OFF-01, OFF-02, OFF-03, BLOG-06, BLOG-07). They get `null` and a
warning, as audit O-02 already noted. The Disclaimer gives a month only, so it is stored as `2026-04`.

**Usage `reference_only`** (Privacy Policy, Terms, Disclaimer, per the audit verdict): the chatbot may quote the
section and link to it, but should not interpret legal text.

## 4. What was removed

| Removed | Count | Examples |
|---|---|---|
| Related-article and see-also link lists | 108 | "Related Articles → Bookkeeping Basics …", "See also: …" |
| UI blocks | 95 | badges, buttons ("Download Free", "Read FAQs"), table of contents, bylines ("By … • 14 min read"), stats tiles, CTA banners |
| Author boxes | 32 | "About the Author" + biography on every article |
| Header navigation | 23 | Home \| About \| App \| Company \| … \| Get App |
| Footer | 22 | tagline, link columns, copyright |
| Irrelevant sections | 4 | home: "Latest Blog Posts" (teasers that duplicate the articles), "Application Screens" (screenshot titles only), "Apna business ka tajurba share karein" (write-a-blog CTA); Play: "WHY USE HISABDO?" (a keyword list, no statements) |
| Empty sections | 2 | home: "Follow HisabDo" (icons only), "Meet The Founder" wrapper |

Every removed block is listed under `per_source[].removed` in `cleaning_report.json`, so a reviewer can
confirm nothing useful was dropped.

### Outdated content

No approved page contains a statement that a newer official page proves wrong. The pages were already updated for
the guest / signed-in sync model, and no blog post still claims "data never leaves your phone". What was outdated
or stale:

| Item | Handling |
|---|---|
| FAQ intro "30 questions answered" (page has 33) | Removed with the intro; warning in the report |
| Home stats tile "3 Currencies (PKR, USD, INR)" | Removed (UI tile); the currency question is flagged below |
| Two near-identical "customer disputes a balance" answers (July 2025 and April 2026 posts) | The older one removed, the newer one kept |
| Currency lists in the FAQ and About page (undated) vs Google Play (2026-10-13) | Possibly outdated, but not proven: flagged, not deleted (section 6) |

The pipeline does not delete content only because it is old. Old general advice is still correct. Instead
each chunk carries its date and its next review date, and undated sources are reported.

## 5. Duplicates

A chunk is a duplicate when at least 80% of its four-word phrases appear in another chunk, or when it is the
same answer reworded (word-sequence similarity ≥ 85%). The copy from the more authoritative source is kept
(FAQ > product pages > legal > blog). Between equals, the copy from the more recently updated page is kept.

| Removed | Kept | Why |
|---|---|---|
| BLOG-07 "What languages does HisabDo support?" | OFF-01 "Does HisabDo support Urdu?" | Blog repeats the official FAQ answer |
| BLOG-03 (2025-07-10) "What should I do if a customer disputes a balance?" | BLOG-08 (2026-04-01) | Same answer, reworded; newer page wins |

Kept deliberately: partial overlaps where each copy says something the other doesn't, e.g. the two "hire an
accountant" answers. Also kept are the legal pages' own "Contact" and "Changes" sections, because each belongs
to a different document.

## 6. Conflicting facts: flagged, not resolved

| Fact | Sources | Chunks |
|---|---|---|
| Supported currencies (audit C-06) | OFF-01 FAQ and OFF-02 About the App (undated): PKR, USD, INR · OFF-04 Google Play (2026-10-13): PKR, INR, AED, USD | `off-01-019`, `off-02-010`, `off-04-010` |

The three chunks keep their original text, get `status: needs_confirmation`, and a note naming both versions with
their sources and dates. Choosing one would mean deciding a product fact, which is the product owner's call.
Until then the chatbot should answer with the source and date, or say it is being confirmed.

## 7. Meaning preserved: how it is enforced

1. **No paraphrasing.** Text is only normalised (whitespace, entities, invisible characters, mojibake, curly
   quotes, emoji). Headings, paragraphs, lists and tables keep their order and wording.
2. **Automatic check.** Every sentence in every chunk is compared with its source page, by word sequence and
   ignoring only punctuation and Markdown. The run reports any sentence it cannot find. Result: 0. A test also
   confirms the check *fails* on changed wording ("PKR, USD, INR and AED", "stored in the cloud").
3. **Rewrites are listed.** These are the only deliberate changes, and each is in the report:
   * FAQ: website-relative wording such as "this website" and "our Privacy Policy" replaced by explicit links
     (4 places, from 2026-10-26).
   * Links: one in-text link to `/track-customer-dues`, which returns 404, now points to the real article,
     `/blog/track-customer-dues`. A site link matching no approved source and no page in the site's own menus
     would be turned into plain text. That rule found none in today's text.
4. **One-line intros** ("Here's what happens during a normal business day.") are merged into the section that
   follows, with the section shown as "A Day With HisabDo > Open the App, …", so they are not orphaned. There are
   3 such merges.
5. **Splitting** happens only between paragraphs or at sub-headings, never inside a sentence. Chunk length: 56 to
   1,327 characters, median 342.

## 8. Issues for the website owner

| # | Issue | Where |
|---|---|---|
| W-1 | **95 broken article links**: articles link to each other as `/slug` (404) instead of `/blog/slug` | all 16 blog posts (Related Articles, See also, in-text) |
| W-2 | Currency list disagrees with Google Play (C-06) | FAQ, About the App, home stats tile |
| W-3 | "30 questions answered" but the FAQ has 33 | FAQ intro |
| W-4 | No last-updated date | FAQ, About the App, home page, BLOG-06, BLOG-07 |
| W-5 | `/delete-data` and five other pages are in the sitemap but not in the audit | sitemap |

## 9. Re-running

```bash
python scripts/clean_knowledge_sources.py --fetch
```

This downloads today's snapshot of every approved source into `data/kb/sources/<date>/`, cleans it, and rewrites
`data/kb/approved/`. Without `--fetch`, it rebuilds from the latest saved snapshot. Then:

1. Read the console summary. Any `NOT FOUND ON PAGE` warning means the cleaner changed wording: fix the cleaner.
2. Review new removals, duplicates and conflicts in `cleaning_report.json`.
3. Run `python -m pytest tests/test_clean_knowledge_sources.py tests/test_kb_privacy.py` and commit.

When the audit approves a new source, add its row to `knowledge_source_audit.csv`; the next run includes it.

## 10. Not done here

* **Loading into the live chatbot.** `data/faq_docs.json` is still what `/api/v1/chatbot` retrieves from.
  Switching to `kb_chunks.jsonl` (364 chunks instead of 18) changes TF-IDF scores and must go through the release
  gate with the held-out evaluation. That is a separate change.
* **Other languages.** Every approved source is English. The site has no Urdu or Roman Urdu pages, apart from one
  Roman Urdu call to action, which was removed. REPO-17 (Roman Urdu concepts) is approvable but not yet approved.
