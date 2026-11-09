# Ingestion and Update Instructions

## 1. Before ingestion
1. Treat this package as a standardized review export, not an automatically approved production release.
2. Assign a named source owner for each record.
3. Obtain documented approval from the product owner or authorized reviewer.
4. Resolve records marked `unverified`, missing `source_url`, or requiring engineering confirmation.
5. Check the source itself and record the actual reviewer, approval evidence, and review date. Never convert a metadata flag into independent approval.

## 2. Record format
Use `schema/knowledge_record.schema.json`. Every record must contain:
`id`, `title`, `section`, `category`, `source_url`, `language`, `last_updated`, `product_module`, `content`, `source_reference`, `source_verification_status`, `content_review_status`, `last_reviewed`, `version`, and `ingestion_eligibility`.

Use JSON `null` when a source URL or date is not evidenced. Do not invent URLs, dates, owners, module behavior, or approval status.

## 3. Cleaning rules
- Remove repeated navigation labels, stale page chrome, duplicated headers/footers, and unrelated promotional copy only when they are demonstrably outside the source's substantive meaning.
- Normalize whitespace and line endings; do not paraphrase substantive content during mechanical cleanup.
- Merge only records proven to be exact duplicates after comparing their complete source text and provenance. Keep similar but distinct definitions/questions separate.
- Keep product-specific instructions separate from general financial education.
- Preserve caveats and uncertainty, including statements that exact screen steps or exports are not confirmed.
- Do not ingest internal engineering notes, test reports, planning documents, or audit logs as customer-facing product guidance without explicit approval.

## 4. Update procedure
1. Obtain the updated authorized source and compare it with the current record.
2. Update only affected content and metadata.
3. Set `last_updated` to the actual source update date and `last_reviewed` to the actual completed review date.
4. Increment `version` according to the repository's versioning convention.
5. Record the change, reviewer, approval evidence, and reason in the change log.
6. Run `python scripts/validate_department3_knowledge.py`.
7. Review the diff and obtain owner approval before replacing any production knowledge file.
8. Re-ingest only records whose `ingestion_eligibility` has been explicitly changed to `eligible_after_approval` after approval is recorded.

## 5. Safety and rollback
- Keep the previous production dataset and a versioned backup.
- Do not deploy a dataset that fails validation.
- If a source is withdrawn, mark it for review and follow the authorized owner’s removal process; retain audit history.
- Never include customer names, account identifiers, balances, or transaction examples unless they are explicitly authorized and privacy-reviewed.
