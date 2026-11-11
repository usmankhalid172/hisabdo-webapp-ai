# Department 3 Automated Ingestion Execution Report

Generated (UTC): 2026-11-11T11:23:51.954618+00:00

## Run result

| Metric | Result |
|---|---:|
| Source records read | 20 |
| Approved documents staged | 12 |
| Approved documents indexed | 12 |
| Unapproved documents excluded | 8 |
| Chunks generated | 12 |
| New documents | 0 |
| Modified documents | 0 |
| Unchanged documents | 12 |
| Deleted source IDs | 0 |
| Removed from staging due to approval change | 0 |
| Duplicate content records | 0 |
| Failures | 0 |
| Warnings | 0 |
| Embedding build | built |

## Embedding configuration

- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
- Dimension: 384
- Normalization: L2
- Similarity: cosine
- Vector dtype: float32
- Index: flat exact staging matrix
- Embedding status: built

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
`2026-11-11T11:23:51.949151+00:00`

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

## Final validation update — 2026-11-11

- Automated embedding build completed successfully with a pinned model revision.
- Vector integrity verified: 12 rows, 384 dimensions, float32, finite values, non-zero vectors and L2 norms equal to 1.
- Dedicated ingestion tests: 20 passed.
- Fresh staged retrieval evaluation: 60 questions; 28 MATCH, 13 MISS, 8 REVIEW, 11 SAFE_ABSTENTION.
- In-scope expected-source match rate: 68.29% (28/41).
- Detailed outputs are saved in docs/evaluation/department3_staged_retrieval_results_v1.0.csv and docs/evaluation/department3_staged_retrieval_report_v1.0.md.
- Current approved staged corpus contains FAQ content only. Other requested content types still need representative approved samples before chunk optimization can be considered complete.
- Staging remains separate from the live chatbot index.
