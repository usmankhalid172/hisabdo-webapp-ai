# Department 3 Automated Ingestion Execution Report

Generated (UTC): 2026-11-11T05:42:21.340325+00:00

## Run result

| Metric | Result |
|---|---:|
| Source records read | 20 |
| Metadata-qualified documents staged | 12 |
| Metadata-qualified documents retained in staging | 12 |
| Records excluded by metadata filters | 8 |
| Chunks generated | 12 |
| New documents | 0 |
| Modified documents | 0 |
| Unchanged documents | 12 |
| Deleted source IDs | 0 |
| Removed from staging due to approval change | 0 |
| Duplicate content records | 0 |
| Failures | 0 |
| Warnings | 0 |
| Embedding build | not_requested |

## Approval interpretation

The 12 staged and indexed documents passed the script's existing
metadata filters (`verified: true` and `content_status: approved`).
This is a technical metadata classification only; it does not
represent independent approval by the source owners.

Independent source-owner approval remains pending. These staging
results must not be interpreted as authorization for production use.

## Embedding configuration

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Revision: `NOT PINNED`
- Dimension: 384
- Normalization: L2
- Similarity: cosine
- Vector dtype: float32
- Index: flat exact staging matrix
- Embedding status: not_requested

## Incremental ingestion

Unchanged documents reuse cached chunks when their source hash
and chunk configuration match. Modified documents are rechunked.
Failed documents do not replace their previous successful staged
version when cached data is available.

Deleted source IDs are distinguished from documents excluded
because their approval status changed.

## Duplicate content

Exact normalized duplicates are retained in metadata but do not
generate duplicate chunks. They are reported as warnings, not failures.

No duplicate-content warnings.

## Metadata ingestion timestamp

Last successful metadata ingestion:
`2026-11-11T05:42:21.334692+00:00`

## Production boundary

This script builds staging artifacts only. It does not update the
live chatbot retriever or production index. A production cutover still
requires an approved model revision, dependency lockfile, labeled
retrieval evaluation, and engineering approval.

## Deleted source IDs

[]

## Removed from staging

[]

## Failure log

No failures recorded.
