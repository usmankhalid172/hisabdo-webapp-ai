# XICTEK Website Content Ingestion and Update Guide

**Owner:** Ali Hassan  
**Purpose:** Define repeatable ingestion and update rules for changing public website content while preventing duplicate knowledge chunks.  
**Scope:** Publicly accessible XICTEK Systems pages, beginning with `https://www.xicteksystems.com/`. This is an ingestion specification and reference workflow; it does not change or crawl the company website.

## 1. Operating principles

1. **The source page is authoritative.** Store the canonical URL, page title, retrieval time, content hash, and source status with every chunk.
2. **Ingestion is idempotent.** Reprocessing unchanged content must update or reuse existing records, not create additional copies.
3. **A changed page replaces its own old chunks.** Publish the new page version only after extraction, chunking, and validation succeed; then retire stale chunks from that source.
4. **Keep provenance separate from content identity.** Identical text on two pages may share a content fingerprint, but each source relationship and citation must remain attributable to its own canonical URL.
5. **Keep product boundaries explicit.** Use a namespace such as `xictek-public` for XICTEK pages. Only include HisabDo or other external product pages when explicitly approved, and then use a separate namespace/source policy. Do not mix records from unrelated sites or products.
6. **Do not ingest private or action-bearing content.** Respect `robots.txt`, site terms, access controls, and crawl limits. Do not submit forms, access accounts, or collect personal application/customer data.
7. **Fail visibly.** A fetch, parse, validation, or index-write failure must be logged and prevent retirement of the previous good version.

## 2. URL and source rules

- Allow only explicitly approved public hosts. Initial allowlist: `xicteksystems.com` and `www.xicteksystems.com`.
- Reject non-HTTP(S) schemes, credentials in URLs, localhost/private-network targets, and redirects to unapproved hosts.
- Follow redirects and prefer the page's valid canonical link when it resolves to an approved host.
- Normalize host casing, remove fragments, normalize the trailing slash, and remove tracking parameters such as `utm_*`, `gclid`, and `fbclid`. Preserve query parameters that change the actual page content.
- Treat the resulting normalized URL as the **source key**. Store the originally discovered URL as `requested_url` for audit.
- Apply an explicit page allowlist or sitemap-based scope. Exclude search results, tag archives, pagination variants, duplicate print views, login/admin paths, and pages outside the approved site scope.
- Do not assume every link to another domain belongs to the same knowledge corpus. External product pages require explicit inclusion and a separate product namespace.

## 3. Change detection and deduplication identity

### Page identity

`source_id = SHA256(namespace + "|" + canonical_url)`

Store `etag` and `last_modified` response headers when available. Use conditional requests where supported. If validators are absent, compare the SHA-256 hash of normalized extracted page text.

### Chunk identity

For each meaningful section, compute:

`chunk_id = SHA256(namespace + "|" + canonical_url + "|" + heading_path + "|" + normalized_chunk_text)`

Normalize Unicode, whitespace, and line endings before hashing. Keep the original readable text separately. Do not use retrieval time, random UUIDs, or a changing chunk ordinal as identity. An ordinal can be stored for display but must not be the deduplication key.

Also compute:

- `content_hash = SHA256(normalized_chunk_text)` to detect identical text across sources.
- `page_content_hash = SHA256(normalized_full_page_text)` to detect page-level changes.
- `embedding_key = SHA256(embedding_model_version + "|" + normalized_embedding_input)` to avoid recomputing an unchanged embedding.

Identical chunks on separate pages should keep separate source-specific `chunk_id` records and citations. A storage layer may reuse one embedding by `content_hash`/`embedding_key`, but it must retain every approved source relationship.

## 4. Extraction and chunk construction rules

1. Extract the main article/page body, not navigation, footer, cookie banners, related-post widgets, or repeated site chrome.
2. Remove scripts, styles, hidden text, tracking pixels, and boilerplate before chunking.
3. Preserve page title, heading hierarchy, lists, and meaningful table labels. Keep a section's heading path with its chunks.
4. Split on semantic boundaries first: section headings, paragraphs, and list groups. Use a configurable target (for example 400–700 tokens) with a modest overlap (for example 40–80 tokens) only when needed to preserve context. Confirm actual limits against the selected embedding model.
5. Never split in the middle of a sentence when an adjacent paragraph boundary is available. Do not create empty or boilerplate-only chunks.
6. Validate each chunk for minimum meaningful content, maximum model input size, non-empty source metadata, and an approved canonical URL.
7. Record chunker name/version and embedding model/version. A chunker or model change is a controlled reprocessing event, not a routine content update.

## 5. Required chunk metadata

Each indexed chunk should carry:

| Field | Purpose |
|---|---|
| `chunk_id` | Deterministic idempotent record key |
| `source_id` | Stable identity of namespace + canonical URL |
| `namespace` | Product/site boundary, e.g. `xictek-public` |
| `canonical_url` | Citation URL after normalization/redirect resolution |
| `requested_url` | Original discovered URL, for audit |
| `title` | Page title |
| `heading_path` | Section/subsection context |
| `text` | Clean readable chunk text |
| `content_hash` | Exact normalized-text duplicate detection |
| `page_content_hash` | Version identifier for the extracted page |
| `retrieved_at` | UTC timestamp of successful fetch |
| `etag`, `last_modified` | Conditional-fetch validators, when provided |
| `chunker_version`, `embedding_model_version` | Reproducibility and migration controls |
| `status`, `generation_id` | Active/staged version management |

## 6. Automated ingestion rule sequence

For each scheduled or manually triggered run:

1. **Discover** URLs from the approved sitemap or source manifest. Do not recursively follow arbitrary external links.
2. **Normalize and validate** each URL against scheme, host, path, namespace, and exclusion rules.
3. **Fetch politely** with a descriptive user agent, bounded concurrency, timeouts, retry/backoff for transient errors, and conditional headers. Respect robots instructions and rate limits.
4. **Resolve redirects** and record the final canonical URL. Reject redirects outside the allowlist.
5. **Detect unchanged pages.** If a conditional request returns `304`, keep the existing page version and chunks unchanged. Otherwise extract and compare `page_content_hash`.
6. **Extract and clean** the main content; retain title, headings, and provenance.
7. **Chunk and validate** using the configured chunker. A page with zero valid chunks or a parsing anomaly is an error, not an instruction to delete prior knowledge.
8. **Prepare a staging generation.** Compute deterministic IDs and hashes; detect duplicates within the page; verify that every chunk belongs to the expected source and namespace.
9. **Upsert idempotently.** Write records by `chunk_id`; updating a record with the same key must replace its payload, not append another copy. Reuse embeddings whose `embedding_key` is unchanged.
10. **Verify writes** by reading back the staged generation and checking expected chunk count, unique IDs, source metadata, and embedding presence.
11. **Commit atomically per source.** Mark the new generation active only after verification. Retire previous active chunk IDs for that source that are absent from the new generation.
12. **Log a run summary** with discovered/fetched/unchanged/changed/failed page counts, new/updated/retired chunk counts, duplicates suppressed, and duration.
13. **Alert and preserve prior good data** if a source fails fetch, parse, validation, or write. Never convert a transient failure into an empty page or mass deletion.

## 7. Step-by-step content update procedure

### Routine scheduled update

1. Run discovery for the approved source manifest.
2. Review the proposed URL additions, removals, redirects, and namespace assignment.
3. Fetch changed pages using conditional requests and record the run ID.
4. Compare page title, canonical URL, page hash, and extracted text against the last successful version.
5. Generate a staged chunk manifest with deterministic IDs and a diff:
   - unchanged IDs;
   - new/changed IDs to upsert;
   - old IDs to retire after commit;
   - duplicate content hashes suppressed or linked.
6. Validate samples from each changed page and confirm citations point to the right official page.
7. Approve the generation (manual approval for high-impact or policy/privacy pages; automated approval may be used for low-risk routine edits with passing checks).
8. Upsert and read back; then activate the generation and retire only stale chunks belonging to that same source.
9. Save the run report and retain the previous generation for rollback according to the retention policy.

### Urgent correction or page removal

1. Confirm the exact canonical source URL and the content change with the content owner.
2. For a correction, ingest and verify the new content using the routine staged workflow.
3. For a confirmed removal, mark that source as intentionally removed and deactivate only its associated chunks; retain an audit tombstone (source URL, time, reason, operator/run ID).
4. Do not remove chunks merely because a fetch timed out, returned a server error, or produced an empty extraction.
5. Check retrieval results for the corrected/deleted fact and verify that stale versions are no longer returned.

### Rollback

1. Pause further promotion for the affected source.
2. Reactivate the last known-good generation for that source.
3. Rebuild or restore its index entries using the stored chunk manifest and compatible embedding model version.
4. Verify retrieval and citations, record the rollback reason, and schedule a corrected re-ingestion.

## 8. Operational safeguards and monitoring

- **Idempotency check:** running the same source generation twice must leave the number of active chunk IDs unchanged.
- **No-duplicate check:** within one source and heading path, duplicate normalized chunk text must not produce multiple active IDs.
- **Source-isolation check:** a source update may retire only records with the matching `source_id` and namespace.
- **Coverage check:** alert if a page unexpectedly loses most of its valid chunks, becomes empty, or changes canonical URL.
- **Citation check:** every active chunk must have a resolvable canonical URL and title. Periodically recheck links, but do not confuse link reachability with factual support.
- **Freshness check:** track last successful ingestion by source; alert on stale critical pages.
- **Version check:** embedding/chunker changes require an explicit migration plan and shadow comparison before replacing the active generation.
- **Audit log:** capture run ID, operator/scheduler, timestamps, source IDs, page hashes, chunk counts, status, and errors. Do not store secrets or private user data in logs.
- **Concurrency control:** serialize updates per source or use a source-level lock/generation compare-and-swap to prevent two overlapping runs from retiring each other's chunks.

## 9. Acceptance checks for each ingestion run

- [ ] All discovered URLs passed allowlist and namespace validation.
- [ ] No prohibited private/action-bearing content was fetched or submitted.
- [ ] Unchanged sources were skipped or safely upserted without growing active chunk count.
- [ ] Changed pages created deterministic IDs and a complete staged manifest.
- [ ] Duplicate chunks were suppressed or linked without losing source provenance.
- [ ] Failed/empty extraction did not remove the previous good version.
- [ ] Read-back validation matched the staged manifest before activation.
- [ ] Stale chunks were retired only after successful source-level commit.
- [ ] Run summary, errors, approvals, and rollback references were retained.

## 10. Reference implementation

The accompanying `xictek_ingestion_dedupe_reference.py` demonstrates URL normalization, deterministic source/chunk identities, and a dry-run diff of chunks to upsert or retire. It deliberately does not fetch pages, create embeddings, or write to a vector database; connect those operations only after selecting the production crawler, storage, and approval controls.

