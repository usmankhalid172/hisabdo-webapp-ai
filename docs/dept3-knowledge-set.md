# Department 3 Knowledge Set: Standardized Records, Schema and Ingestion

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-10 · **Branch:** `FahadZubairi_AI`
**Builder:** `scripts/build_dept3_knowledge_set.py` · **Tests:** `tests/test_dept3_knowledge_set.py` (5)

## 1. Result

| | |
|---|---|
| Knowledge set | `data/kb/dept3/knowledge_set.jsonl`: **363 records**, schema v1.0, from 23 approved sources |
| Expense-management scope | 256 records (expenses and income, udhar, payables, ledger, reports, entry, bookkeeping) |
| By document type | 33 feature FAQ · 36 product documentation · 254 workflow guide · 40 authorized reference (legal) |
| Purged | 286 UI and page blocks + 2 duplicates when the KB was cleaned (27 Oct); **1 promotional record** in this pass |
| Meaning preserved | Record content is the cleaned source text, byte for byte (tested); every sentence of the cleaned KB was checked against its source page (0 mismatches) |
| Verified sample | `sample_batch.jsonl`: 28 records, 2 per product module; **28/28 pass** all checks |

## 2. Metadata schema (v1.0)

`data/kb/dept3/schema/knowledge_record.schema.json` (JSON Schema 2020-12, no extra fields allowed).

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | "1.0" | Schema version |
| `record_id` | string | Stable id: source id, position, heading slug (`off-01-013-can-i-export-pdf-reports`) |
| `title` | string | Page title |
| `section` | string | Page section; "A > B" when a one-line intro was merged into B |
| `heading` | string | FAQ question or section heading |
| `category` | enum | `product_faq` · `product_guide` · `finance_guide` · `legal_policy` (audit register) |
| `doc_type` | enum | `feature_faq` · `product_documentation` · `workflow_guide` · `authorized_reference` |
| `product_module` | enum | `expenses_income` · `customers_udhar` · `suppliers_payables` · `khata_ledger` · `reports_pdf` · `entry_voice` · `data_backup_sync` · `privacy_security` · `app_platform` · `language_currency` · `product_overview` · `company_support` · `legal_policy` · `general_bookkeeping` |
| `expense_management_scope` | boolean | True for the expense-management modules |
| `scope` | enum | `product` · `company` · `legal` · `general_finance` |
| `source_id`, `source_url` | string | Audit register row; official `https` page |
| `language` | enum | `en` · `ur` · `roman_ur` |
| `last_updated` | date or null | Date shown on the page, else null (never guessed) |
| `last_updated_basis` | string | Where the date came from |
| `retrieved_on`, `next_review_due` | date | Snapshot date; due date from the review policy |
| `review_policy` | enum | `P-FAQ` · `P-WF` · `P-CONCEPT` · `P-TAX` · `P-LEGAL` |
| `owner`, `approval` | string | Content owner; "Approved …" only |
| `usage` | enum | `answer` · `reference_only` (legal: quote and link) |
| `status`, `notes` | enum, array | `needs_confirmation` + reason when official sources disagree (currency, C-06) |
| `content` | string | Markdown `## heading` + cleaned source text |
| `content_sha256` | string | Hash of `content` |

Records by module: expenses_income 76 · customers_udhar 73 · khata_ledger 43 · legal_policy 40 · data_backup_sync 38 ·
suppliers_payables 29 · reports_pdf 26 · language_currency 8 · app_platform 7 · company_support 6 ·
general_bookkeeping 6 · privacy_security 5 · product_overview 3 · entry_voice 3.

## 3. What was purged

| Pass | Removed |
|---|---|
| KB cleaning (27 Oct, `clean_knowledge_sources.py`) | 286 blocks: header and footer navigation, tables of contents, buttons and call-to-action banners, bylines, author boxes, "Related Articles" and "See also" link lists, stats tiles, the blog teaser and screenshot sections, the Play keyword list, stale counters ("30 questions answered", "3 Currencies"); 2 duplicate answers |
| This pass | `off-04-016` "Start Managing Your Finances" (Google Play): a call to action ("Download HisabDo today and simplify…") with no information |
| Checked, kept | Repeated text across sources: only "See the Privacy Policy for details" (3 sources): a meaningful pointer, kept. Descriptive adjectives ("powerful") inside factual sentences: kept, as rewording would change the source |

No text was rewritten in this pass. The only rewrites in the KB are the documented link fixes from cleaning
(website-relative wording such as "this website" replaced by the explicit link, and 404 blog links pointed to their
real `/blog/` address).

## 4. Verified sample batch

`sample_verification.json`, 28 records (2 per module), each checked for: schema valid, content hash matches, every
sentence found on the source snapshot page (ignoring the documented link rewrites), `https` source, no promotional
filler, module assigned. **28/28 passed.**

## 5. Ingestion and update instructions

1. **Add or approve a source.** Add its row to `data/knowledge_source_audit.csv` (owner, category, URL, approval
   "Approved …", review policy). Only approved official sources are ingested; repository files and user reviews are not.
2. **Fetch and clean** (every 30 days, and within 7 days of an app release; P-FAQ):
   ```bash
   python scripts/clean_knowledge_sources.py --fetch
   ```
   Stop if the console shows `NOT FOUND ON PAGE` (wording changed by the cleaner), new conflicts, or a large drop in
   chunks; review `data/kb/approved/cleaning_report.json`.
3. **Build and verify the standardized set:**
   ```bash
   python scripts/build_dept3_knowledge_set.py      # schema validation fails the build on any error
   python -m pytest tests/test_dept3_knowledge_set.py tests/test_clean_knowledge_sources.py tests/test_kb_privacy.py
   ```
4. **Load into the chatbot without a restart** (validates first; a bad file is rejected and the current index keeps
   serving):
   ```python
   from src.financial_assistant import service
   service.reload_kb()
   ```
5. **Recalibrate retrieval** if many records changed (`docs/dept3-monitoring-runbook.md` §5.3), and re-run the
   grounded-answer evaluation.
6. **Schema changes:** add fields in a new schema version (`1.1`), never change the meaning of an existing field;
   update `SCHEMA_VERSION` in the builder and the enum lists together.

## 6. Limits

* Product modules are derived from each record's words (the area assigned at cleaning); a record that spans two
  modules gets the dominant one.
* All approved sources are English; Urdu and Roman Urdu users are served through the query rewrite, not translated
  records.
* Missing official documentation (how to add, edit or recategorize an expense, receipts, budgets, recurring entries,
  multi-user) cannot be produced by cleaning: it needs new official pages (Phase 2 Day 1 items D3-18, D3-19).
