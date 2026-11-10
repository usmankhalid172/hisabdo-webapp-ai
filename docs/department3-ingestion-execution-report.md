# Department 3 Ingestion Execution Report

## Execution scope
The ingestion run uses data/department3_staging_knowledge.json.
It does not modify data/faq_docs.json and does not crawl external pages.

## Outputs
- data/department3_ingested_chunks.json
- data/department3_ingestion_manifest.json
- docs/department3-ingestion-execution-report.json

## Reported metrics
The generated JSON report records:
- Input and valid record counts
- Generated chunk count
- Added, modified, deleted and unchanged IDs
- Duplicate IDs and duplicate content
- Validation errors
- Failed page attempts
- Missing/unresolved source URLs
- Vector parsing errors

## Important limitations
The current staging records have no approved source URLs.
No external pages are fetched. Failed pages therefore remain empty
unless a future approved fetching stage is implemented.

This pipeline does not generate embeddings or update a production
vector index. It produces deterministic chunks, hashes, a manifest,
and an execution report for staging review.
