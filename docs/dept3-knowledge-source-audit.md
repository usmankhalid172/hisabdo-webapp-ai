# Department 3 Knowledge Source Audit (HisabDo AI Financial Assistant)

**Auditor:** Fahad Zubairi · **Audit date:** 2026-10-25 · **Branch:** `FahadZubairi_AI`
**Audit sheet:** [`data/knowledge_source_audit.csv`](../data/knowledge_source_audit.csv), 52 rows (opens in Excel or Google Sheets)

## Summary

The chatbot's knowledge is spread across 52 documents and pages. Only 23 of them, the official HisabDo website and Google Play pages, are approved publications. **None of the 25 knowledge files in the team repositories has an approval record.** The one file the live chatbot actually loads (`data/faq_docs.json` on `main`) still contains three claims that contradict the official sources; a corrected version is waiting on branch `FahadZubairi_AI`.

| Finding | Count |
|---|---|
| Sources audited | 52 (27 official pages, 25 repository files) |
| Approved by an owner | 23 (all official publications) |
| Contradictory content | 8 issues (C-01 to C-08) |
| Duplicates | 5 groups (D-01 to D-05) |
| Outdated | 4 issues (O-01 to O-04) |
| Low quality or out of scope | 5 issues (L-01 to L-05) |
| Personal identifiers in knowledge content | **0** (privacy scan, all 27 knowledge files) |
| Authorised reviews or feedback | **None available** (gap G-01) |

## Scope and method

**In scope:** every source that answers, or could answer, a HisabDo user's question through the chatbot:
- product FAQs, feature guides, workflow guides, reviews and feedback, and the policy pages the chatbot may cite
- the official website (https://hisabdo.app), the Google Play listing and the official YouTube channel
- every knowledge file on every branch of `hisabdo-webapp-ai` and `hisabdo-ai`

**Out of scope:** knowledge bases for other products found on the same repositories (doctor-information and healthcare assistants, the XICTEK website assistant, careers). They are excluded because their audience is not HisabDo users.

**How each source was checked:**

| Check | How |
|---|---|
| Approved | An approval record, or official publication by the product owner |
| Up to date | The page's published or effective date, or the file's last Git change |
| Relevant | Answers HisabDo users' questions |
| Right audience | Shopkeepers, freelancers and small business owners, in plain language |
| Accurate | Product claims compared with the official FAQ, About page, home page and Google Play listing |
| Owner and maintainer | Official pages: the publisher. Repository files: the author of the last Git change. |
| Privacy | `scripts/kb_privacy_scan.py` (see "Privacy review") |

## 1. Verified inventory

| Type | Sources | Approved | Notes |
|---|---|---|---|
| Product FAQs | OFF-01, REPO-01, 02, 05, 08, 10, 12, 13, 14 | OFF-01 only | The official FAQ (30 answers) is the primary source; every repository FAQ is a team copy or rewrite |
| Feature guides | OFF-02, OFF-03, OFF-04, REPO-23 | OFF-02 to 04 | Feature level only |
| Workflow guides | BLOG-01 to 16, REPO-11, REPO-18 to 20 | BLOG-01 to 16 | Official guides give practice advice, not screen steps. The only screen-by-screen guides (REPO-18 to 20) are unverified and describe screens no official source mentions. |
| Financial concepts | REPO-03, 09, 16, 17, 21 | none | Generally sound; heavily duplicated |
| Reviews and feedback | OFF-05 | **none authorised** | Public Google Play reviews only; see gap G-01 |
| Policy and legal | OFF-06 to 08 | all | Privacy Policy and Terms effective 2026-09-24 |
| Not knowledge sources | OFF-09, REPO-04, 06, 07, 15, 22, 24 to 27 | n/a | Marketing videos, metadata, backups, prompts, test files and design notes |

The full row-by-row inventory, with owner, URL, dates and verdict, is in the audit sheet.

## 2. Source audit sheet

`data/knowledge_source_audit.csv` has one row per document or page:

| Column | Meaning |
|---|---|
| `content_owner` | Who must approve the content. For official pages, the founder (XICTEK Systems); for repository files, the product owner, who is not yet assigned in the repositories. |
| `maintainer` | Who last changed it |
| `category`, `chatbot_relevance` | What it is and how much it matters to chatbot answers |
| `location`, `url` | Repository and branch, plus a direct link |
| `approval_status` | Approved / no approval record / not authorised / awaiting approval |
| `source_last_updated`, `last_verified` | When the source last changed; when this audit checked it (2026-10-25) |
| `review_policy`, `next_review_due` | The policy below, and the resulting date |
| `verdict`, `issues_and_action` | Keep / fix / merge / remove / do not ingest, and why |

**Review and expiry policies:**

| Code | Applies to | Review | Expires |
|---|---|---|---|
| P-FAQ | Product FAQ and feature content | Every 30 days, and within 7 days of each app release | 90 days after last verification |
| P-WF | Workflow guides with screen steps | On every app release | 60 days |
| P-CONCEPT | Financial concepts and glossaries | Every 12 months | When the concept changes |
| P-TAX | Tax and regulatory guidance | Every 6 months, or on any FBR change | 6 months |
| P-LEGAL | Privacy policy, terms, disclaimer | When the effective date changes, at least every 6 months | Replaced by the new version |
| P-REVIEW | Reviews and feedback | Anonymised themes only, refreshed every 90 days | 180 days |
| P-NONE | Not a knowledge source | None | Keep out of the KB |

## 3. Sources requiring action

**Contradictory** (claims that conflict with official sources or with each other):

| ID | Conflict | Sources | Action | Owner |
|---|---|---|---|---|
| C-01 | "Export a CSV or PDF from the Reports section, filtered by date, category or tag" vs official: PDF statements by customer or time period, no CSV | REPO-01 (`faq-005`, **live**), REPO-05 | Merge the corrected REPO-02; fix REPO-05 before merge | AI team / Product |
| C-02 | "HisabDo predicts expense categories with a machine-learning model" vs official: no such feature documented | REPO-01 (`faq-002`, **live**), REPO-05 | Merge REPO-02 | AI team |
| C-03 | Sales, Invoices, Inventory and Tasks modules vs the official feature list (khata, customers, receivables, payables, expenses, PDF, analytics, voice, backup). One official YouTube title does advertise "WhatsApp Invoice". | REPO-13, 14, 18 to 20; OFF-09 | Product owner to confirm whether invoices exist; until then do not ingest | Product |
| C-04 | "The AI cannot see your data" vs the live chatbot's private data route | REPO-14, REPO-15 | Update or retire | AI team |
| C-05 | "30-day refund policy, support Monday to Friday" vs official: free app; support by email, reply within 48 hours | REPO-24 | Rename as a non-HisabDo sample, or delete | KB-preparation owner |
| C-06 | Currencies: website lists PKR, USD, INR; Google Play (2026-10-13) adds AED | OFF-03, OFF-04, REPO-10 (`KB-006` held as draft) | Product owner to confirm; update the stale page | Product |
| C-07 | "HisabDo is a business assistant" vs official "khata and ledger app" | REPO-12 | Rewrite from OFF-01 | AI team |
| C-08 | Exact screen steps ("Tap Sales > Add Sale", "Add Customer requires phone number") with no official source | REPO-18 to 20, REPO-23 | Verify on an Android device or delete | QA / Product |

**Duplicates:**

| ID | Duplicate | Action |
|---|---|---|
| D-01 | `finance_001`-`006` are identical in REPO-01, REPO-03 and REPO-05 | Keep them in `faq_docs.json` only; delete REPO-03 (no code loads it) |
| D-02 | REPO-06 is a byte-for-byte copy of REPO-01 | Delete; Git history already keeps old versions |
| D-03 | Profit, revenue, expense, cash-flow, receivable and payable definitions repeated across REPO-08, 16, 17, 21, 23 and BLOG-14 | Merge into one glossary; prefer REPO-17 (Roman Urdu) and BLOG-14 (official) |
| D-04 | The same verified product facts in REPO-02 and REPO-10 | Keep REPO-02 as the single live source; the prototype reads from it |
| D-05 | REPO-08 reuses IDs `faq-001`-`006` for different questions than `faq_docs.json` | Renumber before any merge, or answers will be cited under the wrong ID |

**Outdated:**

| ID | Issue | Action |
|---|---|---|
| O-01 | The live KB on `main` (REPO-01) has not been corrected; the fix exists only on `FahadZubairi_AI` | Merge pull request #103 after review |
| O-02 | BLOG-06 and BLOG-07 show no published date, and OFF-01 to 03 show no last-updated date | Ask the owner to add dates; until then, re-verify them every 30 days |
| O-03 | REPO-14 and REPO-15 state the AI has no data access, which is no longer true | Update or retire |
| O-04 | REPO-04 (KB manifest) tracks only a version number and document count | Replace with this audit sheet as the register of sources |

**Low quality or out of scope:**

| ID | Issue | Action |
|---|---|---|
| L-01 | REPO-26: a skincare test upload ("ABC Store - Face Serum") committed into `services/knowledge` | Delete |
| L-02 | REPO-07: IT-support content (DNS, ipconfig) in a "business knowledge" file | Do not ingest |
| L-03 | REPO-24: a fabricated "HisabDo Knowledge Base Sample" with invented policies | Rename or delete |
| L-04 | REPO-08: source labels ("HisabDo Finance FAQ", "Business Finance Glossary") name documents that don't exist, and items are self-marked "verified" with no verifier | Replace with real source URLs and a named verifier |
| L-05 | REPO-15 and REPO-22 are behaviour rules and prompt templates, not knowledge | Move into the system prompt |

## 4. Privacy review

**Result: no personal identifiers are stored in any knowledge source.**

- **Every knowledge file was scanned.** `scripts/kb_privacy_scan.py` checked all 27 audited knowledge files and the live chatbot KB for:
  - e-mail addresses
  - Pakistani and international phone numbers
  - CNIC numbers
  - social-media profile links
  - JSON fields that identify a person (author, reviewer, user name and similar)

  All are clean. The only contact found is HisabDo's official support address, `hisabdo.app@gmail.com`, which is published on the FAQ and allowed.
- **The scanner was tested.** It flags 40 identifiers in the prototype's synthetic demo data (`secure_kb_chatbot/data/seed.json`, fake `.example` addresses). That file is test business data, not knowledge content, and must never be indexed.
- **No review content is stored anywhere in the KB**, so there were no reviewer identities to remove.
  - Google Play reviews show reviewer display names; none were copied into any file, including this audit.
  - Some official YouTube titles name real people; none were copied.
- **Guard in the test suite.** `tests/test_kb_privacy.py` runs the scan on the live KB, so any future entry with a personal identifier fails.

**Rule for future review content.** If the owner approves using reviews:
- store only anonymised themes, such as "users find the dashboard easy to read"
- never store names, profile pictures, dates tied to a person, or verbatim quotes that could identify someone
- run the scanner before every merge

## 5. Unavailable reviews, approved alternatives and knowledge gaps

**G-01: no authorised reviews or feedback exist.**
- No repository contains reviews, testimonials or feedback data, and no approved feedback channel feeds the KB.
- The only reviews are public Google Play reviews: 4.9 stars from 62 reviews on 2026-10-13. Public is not the same as authorised, and they show reviewers' names.

Approved alternatives, until the owner authorises a feedback source:

| Alternative | Approved | What it covers |
|---|---|---|
| Official "Built Around Real Situations" personas (OFF-02): corner shop owner, freelancer, wholesaler, home-based seller | Yes | Who uses HisabDo and why, without real people |
| Aggregate store rating and count (OFF-04), cited with its date | Yes | Overall satisfaction, with no reviewer data |
| Official FAQ (OFF-01) | Yes | Common questions users ask |
| Support channel (hisabdo.app@gmail.com, per OFF-01) as the route to collect authorised, consented feedback | Needs owner decision | Future feedback themes |

**Remaining knowledge gaps:**

| ID | Gap | Impact | Owner |
|---|---|---|---|
| G-01 | No authorised reviews or feedback | The chatbot cannot answer "what do other users say?" | Product owner |
| G-02 | No official screen-by-screen workflow guides (the blog gives practice advice; YouTube videos are promotional) | The chatbot can explain features but not exact taps | Product / QA (record steps on Android) |
| G-03 | Whether invoices, inventory and tasks exist in the app (C-03) | Risk of describing features that don't exist | Product owner |
| G-04 | The current currency list (C-06) | A currency question gets no verified answer | Product owner |
| G-05 | Almost no Urdu-script or Roman Urdu product content; only REPO-17 (concepts, unapproved) | Weaker answers for Urdu speakers | AI team |
| G-06 | No dates on the official FAQ, About and home pages | Freshness can't be confirmed from the page | Website owner |
| G-07 | No named product owner recorded in any repository for KB approval | Nobody can formally approve entries | Team Lead |

## 6. Recommended next steps

1. **Assign a KB owner** (G-07), who approves entries and signs off rows in the audit sheet.
2. **Merge the corrected KB** (pull request #103), which removes the live contradictions C-01 and C-02.
3. **Delete or quarantine** REPO-03, 06, 07, 24 and 26. Keep REPO-18 to 20 out of every KB until verified on the app.
4. **Answer G-03 and G-04 with the product owner**, then update the KB and the stale official page.
5. **Run the privacy scan and this audit's checks** before every KB change, and review each source on its `next_review_due` date.

## How to re-run

```bash
python scripts/kb_privacy_scan.py
```

```bash
python scripts/kb_privacy_scan.py path/to/new_source.json
```

```bash
pytest tests/test_kb_privacy.py
```
