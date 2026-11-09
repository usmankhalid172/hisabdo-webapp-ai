# Knowledge Base Ingestion & Update Technical Specification
**Prepared by:** Muhammad Daniyal  
**Project:** XICTEK Systems / HisabDo AI Knowledge Base  
**Date:** 9 November 2026  
**Document status:** Proposed engineering standard for review and adoption

## 1. Purpose

Define a repeatable, auditable process for importing, validating, parsing, chunking, embedding, publishing, and updating knowledge-base content from structured files and approved web sources. The standard applies across company, product, careers, services, blog, FAQ, and portfolio/case-study content.

This document distinguishes **observed repository behavior** from **proposed standards**. The proposed metadata contract is not represented as already implemented or deployed.

## 2. Repository baseline and current-state findings

The reviewed repository archive contains `src/xictek_website_assistant/ingest.py`, `chunking.py`, `vector_store.py`, `config.py`, and `data/xictek_faq_raw.jsonl`.

| Area | Observed implementation | Specification implication |
|---|---|---|
| Source acquisition | Breadth-first crawl from configured seed URLs; allowed host list; HTML extraction with BeautifulSoup | Preserve allow-listing; strengthen canonical URL and redirect validation |
| Structured source file | `xictek_faq_raw.jsonl` exists | Define a documented JSONL record contract and strict parsing |
| Chunking | Paragraph-aware, defaults to 1,200 characters with 200-character overlap | Keep paragraph boundaries; add chunk metadata inheritance |
| Deduplication | Exact duplicate chunk text removed within each crawled page | Add canonical-source and content-hash deduplication across all input types |
| Chunk record | Persisted fields are `id`, `title`, `url`, `text` | Extend to a versioned metadata envelope |
| Index metadata | `metadata.json` currently records the embedding model | Record schema, parser, corpus, build, and embedding versions |
| Update strategy | Full rebuild; no incremental/delta indexing | Define safe full rebuild first; incremental updates as a later controlled enhancement |
| Domain control | Host allow-list is used for discovered links | Also validate input URLs, redirect destinations, and final response URLs |

**Important:** This is a specification/review document. No repository code has been changed, no new index has been deployed, and no production ingestion run is claimed.

## 3. Scope and supported source formats

### 3.1 Supported inputs

1. **JSONL** — one UTF-8 JSON object per line; preferred for FAQ, product, careers, and other structured knowledge records.
2. **JSON** — UTF-8 object or array; accepted only when the top-level structure is documented and deterministic.
3. **CSV** — UTF-8 with a header row; column names must map explicitly to the canonical fields. Do not infer columns by position.
4. **HTML/web pages** — only from configured HTTPS domains; extract readable main content and retain the canonical page URL.
5. **Markdown/text** — optional future source type; parse front matter only if its schema is declared.

Unsupported or malformed files must be rejected or quarantined with a clear error. Never silently skip a malformed record.

### 3.2 Processing flow

`discover → acquire → parse → normalize → validate → deduplicate → classify → chunk → embed → stage → verify → publish → log`

Each stage must be deterministic for the same input, configuration, parser version, and embedding model.

## 4. Canonical metadata contract

Every source record must be normalized to the following logical fields before chunking. Fields marked **Required** must be present and valid.

| Field | Requirement | Rule / example |
|---|---|---|
| `schema_version` | Required | String version, e.g. `1.0` |
| `source_id` | Required | Stable ID; recommended `src_` + SHA-256 prefix of normalized canonical URL or stable source key |
| `source_type` | Required | Enum: `web_page`, `blog`, `faq`, `product`, `service`, `career`, `case_study`, `policy`, `document` |
| `domain` | Required | Lowercase approved host, e.g. `xicteksystems.com` or `hisabdo.app` |
| `canonical_url` | Required for web-backed records | Absolute HTTPS URL; no credentials or fragment; approved host |
| `title` | Required | Non-empty, trimmed text; recommended max 300 characters |
| `content` | Required | Non-empty UTF-8 text after extraction/normalization |
| `published_at` | Optional | ISO 8601 date `YYYY-MM-DD`, if known |
| `updated_at` | Required | ISO 8601 date `YYYY-MM-DD`; source's last-known content update date |
| `ingested_at` | Pipeline-generated | UTC ISO 8601 timestamp, e.g. `2026-11-09T09:30:00Z` |
| `language` | Required | BCP-47 language tag, e.g. `en`, `ur`, `ar`; use `und` if genuinely unknown |
| `product_tags` | Required array | Zero or more controlled lowercase slugs; empty array is valid |
| `category` | Required | Controlled category aligned with `source_type` and taxonomy |
| `status` | Required | `active`, `draft`, `archived`, or `deleted` |
| `content_hash` | Pipeline-generated | SHA-256 of normalized content |
| `parser_version` | Pipeline-generated | Version of parser/extractor used |
| `chunking_version` | Pipeline-generated | Version of chunking policy |
| `source_owner` | Recommended | Team/domain responsible for correctness |
| `access_level` | Required | `public` or `internal`; never ingest secrets |

### 4.1 Example normalized JSONL record

```json
{
  "schema_version": "1.0",
  "source_id": "src_8a1c4d2f",
  "source_type": "product",
  "domain": "hisabdo.app",
  "canonical_url": "https://hisabdo.app/features",
  "title": "HisabDo Product Features",
  "content": "HisabDo supports digital khata, expense records, and offline-first workflows.",
  "published_at": "2026-04-15",
  "updated_at": "2026-10-30",
  "ingested_at": "2026-11-09T09:30:00Z",
  "language": "en",
  "product_tags": ["hisabdo", "expense-management", "digital-khata"],
  "category": "product_features",
  "status": "active",
  "content_hash": "generated-by-pipeline",
  "parser_version": "1.0.0",
  "chunking_version": "1.0.0",
  "source_owner": "Product Team",
  "access_level": "public"
}
```

The example `source_id` is illustrative. In implementation, derive IDs from a stable key; do not copy the sample ID across records.

## 5. Strict validation rules

### 5.1 URL format and source trust

- Require an absolute `https://` URL for web-backed records. Reject `http`, protocol-relative URLs, relative paths, malformed URLs, embedded username/password, whitespace, and fragments.
- Lowercase and validate the hostname against an explicit allow-list. A suffix check alone is unsafe: `xicteksystems.com.attacker.example` must not pass.
- Normalize host casing and remove default port `:443`; preserve meaningful path and query parameters only when the source policy requires them.
- Remove tracking parameters such as `utm_*`, `gclid`, and `fbclid` before canonical deduplication. Do not remove functional query parameters without an approved rule.
- Reject redirect destinations outside the allow-list. Validate both the requested URL and the final response URL after redirects.
- Canonical URL should be stable and unique. If a page declares a canonical link, verify it is HTTPS and on an approved host before accepting it.
- Store the final verified canonical URL, not an untrusted redirect URL.
- A URL reachability check is a separate operational check; syntactic validity alone does not prove a page is live.

### 5.2 Date and timestamp format

- `published_at` and `updated_at`: strict calendar date `YYYY-MM-DD` (example: `2026-11-09`).
- Reject locale formats (`09/11/2026`), natural language (`Nov 9, 2026`), impossible dates, and timestamps in date-only fields.
- `ingested_at`: RFC 3339 / ISO 8601 timestamp in UTC with `Z` suffix (example: `2026-11-09T09:30:00Z`).
- Do not substitute ingestion date for an unknown publication/update date. Use `null` for optional unknown dates; `updated_at` must be supplied by source metadata or explicitly set to the verified source review date under an agreed policy.
- Enforce `published_at <= updated_at <= ingestion calendar date` where both source dates are known. If a future-dated publication is intentionally scheduled, mark it `draft` and document the exception.

### 5.3 Product tags and taxonomy

- `product_tags` must be a JSON array of unique strings; never accept a comma-separated string.
- Each tag must be lowercase kebab-case: `^[a-z0-9]+(?:-[a-z0-9]+)*$`.
- Tags must exist in a centrally maintained allow-list. Proposed initial examples: `hisabdo`, `expense-management`, `digital-khata`, `portfolio`, `career-services`, `custom-software`, `mobile-apps`, `cloud-solutions`, `ui-ux`.
- Do not invent tags during ingestion. Unknown tags go to a review queue; ingestion must fail closed for records that use unapproved tags.
- Keep product identity separate from topic/category. For example, `hisabdo` is a product tag; `product_features` is a category.
- Tag aliases must map through an explicit alias table (e.g. `digital-ledger` → `digital-khata`) before validation.

### 5.4 Content and status

- Trim surrounding whitespace, normalize line endings to `\n`, and remove empty records.
- Preserve meaningful paragraph boundaries, headings, list order, and source attribution.
- Reject empty content, placeholder-only content, binary garbage, and content over configured limits.
- Do not ingest navigation, cookie banners, scripts, forms, or repeated boilerplate as factual knowledge.
- `deleted` means remove from the active index at publish time; retain an audit/tombstone record in the ingestion log.
- `archived` and `draft` are excluded from public retrieval unless an explicit environment policy permits them.
- `internal` content must never enter a public website assistant index.

## 6. Parsing and normalization rules

### 6.1 JSONL

- Decode as UTF-8; one JSON object per non-empty line.
- Report errors with filename and 1-based line number.
- Reject arrays, scalars, duplicate keys, invalid JSON, and unexpected fields unless the schema version explicitly allows extensions.
- Parse each line independently but publish the batch only if all required records pass validation (atomic batch by default).

### 6.2 JSON

- Accept a single object or an array of objects only.
- Validate every item against the same canonical schema.
- Preserve source ordering for deterministic output; sort only where a stable key is explicitly defined.

### 6.3 CSV

- Require a header row and UTF-8 encoding (UTF-8 BOM may be stripped).
- Map columns by exact configured header names.
- Parse `product_tags` from JSON array syntax, not free-form comma splitting.
- Empty optional fields become `null`; required empty fields fail.
- Reject duplicate headers and rows with unexpected column counts.

### 6.4 HTML

- Fetch only approved HTTPS URLs with a bounded timeout, request rate, page count, and response size.
- Validate content type and status code; skip non-HTML with a logged reason.
- Strip script/style/navigation/footer/form boilerplate; prefer `<main>` or a documented article selector.
- Capture title, canonical URL, publication/update dates when available, and page text.
- Record extraction warnings if dates or canonical links are absent; do not fabricate them.
- Re-check the final URL after redirects against the allow-list.

## 7. Chunking and metadata inheritance

- Chunk after normalization and validation, not before.
- Prefer semantic/paragraph boundaries. Existing XICTEK defaults are 1,200 characters and 200-character overlap; retain as initial defaults pending evaluation.
- Do not split a question from its answer or a heading from the first explanatory paragraph when structured FAQ data is available.
- Keep chunks within configured maximum length; avoid tiny trailing chunks unless they contain a meaningful standalone fact.
- Every chunk inherits source metadata and adds:
  - `chunk_id` (stable source ID + content/chunk hash; avoid index-only IDs where possible)
  - `chunk_index`
  - `chunk_text`
  - `chunk_hash`
  - `token_count` (if tokenizer available)
- Keep source-level metadata in a shared record or metadata map; do not duplicate inconsistent values across chunks.
- Deduplicate exact normalized content by hash. Cross-source near-duplicates should be flagged for review rather than automatically deleted if they have different owners or URLs.

## 8. Embedding and index build rules

- Build embeddings only for validated, active, public records.
- Record embedding model name, exact model revision, vector dimension, normalization method, and build timestamp in index metadata.
- A model change requires a complete re-embedding of all active chunks; matching vector dimensions do not imply compatible vector spaces.
- Verify `number_of_vectors == number_of_chunks`, vector dimension consistency, finite values, and expected normalization before publication.
- Write build output to a staging directory. Never overwrite the currently serving index while it is being generated.
- Include corpus checksum, schema version, parser version, chunking version, embedding model/revision, record count, chunk count, and rejected-record count in the build manifest.

## 9. Update, deletion, and publication policy

### 9.1 Initial safe update method

The repository currently performs a full rebuild. Continue using a full rebuild as the approved baseline until incremental indexing has separate tests and rollback support.

1. Acquire sources and produce a dated input snapshot.
2. Parse and validate all records.
3. Compare canonical URL + content hash with the previous manifest.
4. Classify records as `new`, `changed`, `unchanged`, `archived`, or `deleted`.
5. Rebuild all active chunks and embeddings in a staging directory.
6. Run integrity, metadata, retrieval-smoke, and source-domain checks.
7. Atomically switch the active index pointer/directory only after every check passes.
8. Retain the previous index for rollback.
9. Write an update log containing input checksums, counts, errors, versions, and operator/CI run ID.

### 9.2 Incremental update (future enhancement)

Incremental upserts may be introduced only when stable IDs, deletion tombstones, deterministic chunk IDs, and embedding-model compatibility are implemented. Changed sources must have their old chunks removed before new chunks are inserted. Deleted sources must remove all associated chunks. A periodic full rebuild remains the reconciliation mechanism.

### 9.3 Rollback

If validation, embedding, integrity, or smoke tests fail, do not publish. Keep the last known-good index active and mark the run failed. Rollback must restore the previous manifest and vector/chunk pair together.

## 10. Logging, errors, and observability

Every run must emit:
- run ID, start/end UTC timestamps, operator or CI identity;
- source files/URLs and input checksums;
- discovered, parsed, accepted, rejected, unchanged, changed, deleted record counts;
- chunks created/deduplicated and embeddings created;
- warnings and errors with source ID, filename, line number or URL, and reason;
- schema/parser/chunking/embedding versions;
- staging path, published index version, and rollback outcome.

Error categories:
- `E_FILE_FORMAT`, `E_JSON_PARSE`, `E_SCHEMA`, `E_URL_SCHEME`, `E_URL_DOMAIN`, `E_URL_REDIRECT`, `E_DATE_FORMAT`, `E_TAG_UNKNOWN`, `E_CONTENT_EMPTY`, `E_DUPLICATE`, `E_EMBEDDING`, `E_INDEX_INTEGRITY`, `E_PUBLISH`.

Never log API keys, access tokens, credentials, private user data, or full internal-only content.

## 11. Security and governance controls

- Maintain approved domains, tag taxonomy, source types, and category mappings in version-controlled configuration.
- Use least-privilege credentials and never store secrets in source records.
- Respect robots.txt, site terms, rate limits, and approved crawl scope.
- Sanitize extracted HTML; treat source content as untrusted data, not executable instructions.
- Keep internal and public corpora separate at ingestion and index level.
- Require source owner/reviewer approval for sensitive policy, pricing, legal, or recruitment updates.
- Preserve an audit trail for content replacement and deletion.

## 12. Acceptance checklist

A release is acceptable only when:

- [ ] JSONL, JSON, and CSV parsers reject malformed input with line/row-level diagnostics.
- [ ] Every active record passes the canonical metadata schema.
- [ ] URLs are HTTPS, syntactically valid, and within the exact approved host allow-list.
- [ ] Redirect and canonical URLs are revalidated.
- [ ] Date-only fields use strict `YYYY-MM-DD`; ingestion timestamp is UTC ISO 8601.
- [ ] Product tags are arrays of approved lowercase kebab-case slugs.
- [ ] Unknown tags and unsupported source types fail validation.
- [ ] Empty, duplicate, archived, deleted, and internal records follow the documented policy.
- [ ] Chunk metadata maps back to one stable source record.
- [ ] Vector count, chunk count, dimensions, and finite values match.
- [ ] Failed builds never replace the active index.
- [ ] A rollback test restores the previous known-good index.
- [ ] A run manifest and audit log are generated for every build.

## 13. Recommended implementation sequence

| Priority | Work item | Expected outcome |
|---|---|---|
| P1 | Add canonical Pydantic metadata model and versioned schema | One shared contract for all domains |
| P1 | Add JSONL/JSON/CSV parser with line/row diagnostics | Repeatable structured ingestion |
| P1 | Add strict URL/date/tag validators and domain allow-list | Invalid or untrusted metadata rejected |
| P1 | Extend `Chunk` and persisted `chunks.json` with source metadata | Traceable chunks and filtering |
| P1 | Expand `metadata.json` into a build manifest | Reproducible index provenance |
| P1 | Add staging, integrity checks, and atomic publish/rollback | Safe index updates |
| P2 | Add canonical/content-hash deduplication across source types | Fewer duplicate chunks |
| P2 | Add incremental upsert/delete after stable IDs are proven | Faster updates without stale chunks |
| P2 | Add CI fixtures for malformed metadata and source regressions | Automated release gate |

## 14. Repository files to update (proposed)

- `src/xictek_website_assistant/schemas.py` — canonical source metadata model and enums.
- `src/xictek_website_assistant/ingest.py` — structured parsers, normalization, URL/redirect validation, run logging.
- `src/xictek_website_assistant/chunking.py` — stable chunk metadata and structured FAQ handling.
- `src/xictek_website_assistant/vector_store.py` — persist extended metadata and validate index integrity.
- `src/xictek_website_assistant/config.py` — approved domains, tag allow-list, schema and parser versions.
- `tests/xictek_website_assistant/` — parser, validator, dedupe, update, rollback, and integrity tests.
- `data/index/metadata.json` — versioned build manifest.

These are recommendations, not completed code changes.

## 15. Operational runbook

**Before ingestion:** review source ownership, confirm allowed domains/tags, snapshot input files, and verify the embedding model/configuration.

**Run ingestion:** execute from repository root using the approved CI or development environment with outbound HTTPS access. The existing command is `python -m src.xictek_website_assistant.ingest`; the proposed structured-file parser should be invoked by the same orchestrator.

**After ingestion:** inspect the run manifest; verify record/chunk/vector counts; run parser and retrieval regression tests; confirm citations point to approved canonical URLs; publish only after all gates pass.

**If any gate fails:** retain the old index, correct the source or schema, rerun validation, and document the failure. Do not bypass validation to meet a deadline.

## 16. Limitations and handover notes

- The reviewed archive is a repository snapshot, not a live production environment.
- This specification proposes a common metadata standard; implementation and team approval are still required.
- The repository's existing full rebuild approach is retained as the initial safe update strategy.
- Product tag examples are a proposed starting taxonomy and must be confirmed by the relevant content owners.
- No live crawl, production deployment, or index replacement was performed as part of preparing this document.
