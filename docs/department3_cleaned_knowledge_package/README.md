# HisabDo Department 3 — Cleaned Knowledge Deliverables

## Package contents
- `data/cleaned_knowledge_records.json`: 20 standardized knowledge records.
- `schema/knowledge_record.schema.json`: JSON Schema (Draft 2020-12).
- `samples/structured_sample_batch.json`: five representative records, including both metadata-marked verified and unverified examples.
- `docs/`: prior audit evidence copied from the supplied repository.
- `docs/ingestion_and_update_instructions.md`: operational handling rules.
- `docs/cleanup_and_validation_report.md`: scope, decisions, and validation findings.
- `scripts/validate_department3_knowledge.py`: standard-library validation script.

## Important approval distinction
The source dataset's `verified` and `content_status` fields are preserved as evidence, but they do not prove independent product-owner approval. The audit register reports zero independently confirmed approvals and zero assigned source owners. Therefore every record is currently held from production ingestion pending authorized approval. Do not interpret this package as a product-owner-approved release.

## Preservation
The original application file `data/faq_docs.json` was not modified. This package is a separate standardized export. Record wording was preserved; only whitespace/line-ending normalization was applied. No records were merged or deleted.
