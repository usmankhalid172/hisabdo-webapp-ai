# Department 3 Ingestion Master Checklist

**Scope:** HisabDo expense-management knowledge assets in `data/faq_docs.json` and approved product documentation. This checklist separates the current live FAQ retrieval path from the new staging ingestion procedure.

## 1. Source governance
- [ ] Confirm every source is owned or approved by the product/source owner.
- [ ] Require stable unique `id`, non-empty `title` and `text`, source URL, language, last-updated date, section/category, product area, and explicit verification status.
- [ ] Only ingest `verified: true` and `content_status: approved`; exclude `needs_review`, missing approvals, and unknown status.
- [ ] Do not infer missing UI steps, accounting rules, or product capabilities.
- [ ] Preserve source IDs, URL, section, version, and provenance in every chunk.
- [x] Keep source files unchanged; ingestion writes derived staging artifacts only.

## 2. Content normalization and chunking
- [ ] Classify each source as structured FAQ, accounting feature table, workflow guideline, or long-form documentation.
- [ ] Preserve headings and table row/column relationships; never flatten a table into an ambiguous list.
- [x] Use the type-specific starting sizes/overlaps in `department3_chunking_embedding_configuration.md`.
- [x] Keep each chunk associated with its parent document and source hash.
- [x] Detect exact normalized duplicate bodies; log them and avoid indexing repeated copies.
- [ ] Do not remove merely similar documents without owner review.

## 3. Embedding and vector index reproducibility
- [x] Model ID: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions).
- [ ] Pin the exact Hugging Face model commit SHA before embedding builds.
- [ ] Pin Python and all direct/transitive dependencies in a lockfile; repository ranges are not sufficient.
- [x] Use CPU inference, L2-normalized float32 vectors, cosine similarity.
- [ ] Validate vector count equals chunk count, dimension equals 384, all values are finite, and no vector has zero norm.
- [ ] Record model ID/revision, dimensions, normalization, similarity, index type, chunking config, and source hashes in the manifest.
- [ ] Never load vectors created by a different model revision, even if dimensions match.

## 4. Incremental ingestion and failure handling
- [x] Run `python scripts\department3_ingestion.py` from repository root after source changes.
- [x] Compare stable IDs and source hashes to detect new, modified, unchanged, and deleted sources.
- [x] Ensure repeated runs with unchanged input are idempotent.
- [x] Log invalid JSON, malformed records, missing IDs, duplicate IDs, duplicate content, chunk failures, model download/embedding failures, and vector shape errors.
- [ ] Retain the last valid live index if a candidate build fails.
- [ ] Review `data/department3_ingestion/failures.json` before approval.
- [ ] Deleted source IDs are removed from the next staging manifest/chunk set; retain an audit record of the deletion event before production cutover.

## 5. Validation and release
- [x] Run `pytest -q tests/test_department3_ingestion.py tests/test_faq_rag.py`.
- [x] Run the full repository test suite.
- [ ] Evaluate chunking on labeled FAQ, table, workflow, and long-document queries; measure retrieval precision/recall and irrelevant-context rate.
- [ ] Recheck all expense-management workflow gaps against approved app documentation.
- [x] Review the execution report and failure log.
- [ ] Obtain source-owner and engineering approval before wiring staging artifacts into production.
- [ ] Commit/push only after the user reviews the completed deliverables.

## 6. Current known limitations
- The supplied live `FaqRetriever` creates an in-memory LangChain vector store from verified FAQs; it does not currently persist or incrementally update a vector database.
- `requirements-lock-current.txt` captures the current installed environment using `pip freeze`, and `python -m pip check` reports no broken requirements. This is an environment snapshot, not yet a verified project-only or cross-platform lockfile. The embedding model commit SHA remains unpinned.
- Feature-table and workflow-specific content types are supported by the staging classifier, but the current FAQ JSON does not establish that these content types are populated with approved examples.
- The staging script does not crawl external pages. Source acquisition/HTTP page crawling must remain a separate approved-source process with URL allowlisting, retries, status-code checks, and page-level failure capture.

## Final validation update — 2026-11-11

- [x] Deterministic ingestion procedure implemented.
- [x] Approved-source staging generated.
- [x] Pinned embedding model revision used for build.
- [x] Embedding matrix shape, dtype, finite values and normalization validated.
- [x] Dedicated ingestion test suite passed (20 tests).
- [x] Fresh 60-question staged retrieval evaluation executed.
- [x] Separate evaluation CSV and Markdown report generated.
- [ ] Empirical chunk optimization across all four requested content types.
- [ ] Representative approved accounting-table, workflow and long-document samples obtained.
- [ ] Independent source-owner approval for production promotion.
