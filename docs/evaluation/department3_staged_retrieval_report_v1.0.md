# Department 3 Staged Retrieval Evaluation

- Questions evaluated: 60
- Model: sentence-transformers/all-MiniLM-L6-v2
- Model revision: 1110a243fdf4706b3f48f1d95db1a4f5529b4d41
- Similarity: cosine (dot product on normalized vectors)
- Threshold: 0.4
- Top K: 3 unique source documents
- Staged documents: 12
- Staged chunks: 12
- In-scope expected-source match rate: 68.29% (28/41)

| Outcome | Questions |
|---|---:|
| MATCH | 28 |
| MISS | 13 |
| OUT_OF_SCOPE | 0 |
| SAFE_ABSTENTION | 11 |
| REVIEW | 8 |

## Interpretation

- OUT_OF_SCOPE means none of the expected source IDs exists in the staged index.
- MATCH and MISS are calculated only when at least one expected source is staged.
- REVIEW and SAFE_ABSTENTION apply to cases without a verified expected source.
- This is a staged-vector benchmark, not an end-to-end chatbot answer evaluation.
- Results are not directly comparable to the historical live FaqRetriever benchmark.

Detailed results: `docs\evaluation\department3_staged_retrieval_results_v1.0.csv`
