# Department 3 Retrieval Performance Report

## Run scope

- Evaluation set: 60 questions
- Verified questions included in positive relevance metrics: 41
- Unverified questions excluded from positive relevance metrics: 19
- Staged chunks: 12
- Original historical baseline misses: 11
- Strategies: dense vector, BM25, hybrid RRF, metadata-filtered hybrid, metadata-filtered hybrid with reranking
- Top-k: 1, 3, 5

## Best observed strategy at k=3

- Strategy: `dense_vector`
- Expected-source hit rate: 95.12%
- MRR: 0.9130

## Results

| Strategy | K | Hit rate | MRR |
|---|---:|---:|---:|
| dense_vector | 1 | 87.80% | 0.9130 |
| dense_vector | 3 | 95.12% | 0.9130 |
| dense_vector | 5 | 95.12% | 0.9130 |
| bm25_lexical | 1 | 70.73% | 0.8260 |
| bm25_lexical | 3 | 92.68% | 0.8260 |
| bm25_lexical | 5 | 100.00% | 0.8260 |
| hybrid_rrf | 1 | 80.49% | 0.8882 |
| hybrid_rrf | 3 | 95.12% | 0.8882 |
| hybrid_rrf | 5 | 97.56% | 0.8882 |
| hybrid_metadata | 1 | 68.29% | 0.7602 |
| hybrid_metadata | 3 | 82.93% | 0.7602 |
| hybrid_metadata | 5 | 82.93% | 0.7602 |
| hybrid_metadata_rerank | 1 | 70.73% | 0.7724 |
| hybrid_metadata_rerank | 3 | 85.37% | 0.7724 |
| hybrid_metadata_rerank | 5 | 85.37% | 0.7724 |

## Interpretation and limitations

- Historical baseline misses and this staged benchmark are separate measurements; do not combine their denominators.
- Unverified questions are excluded from expected-source hit-rate scoring. They must be assessed for safe abstention, not rewarded for retrieving unverified drafts.
- The staged corpus contains only the approved/staged documents currently present in `chunks.json`; missing source records cannot be retrieved.
- A higher hit rate does not by itself prove answer correctness or safe product instructions.
- The best strategy is an observed candidate on this 60-question evaluation set, not a guarantee of future performance.
- The comparison is a local retrieval benchmark, not an end-to-end chatbot or production-backend test.

## Generated artifacts

- `docs\evaluation\department3_retrieval_strategy_results.csv`
- `docs\evaluation\department3_retrieval_strategy_summary.csv`
- `docs\evaluation\department3_retrieval_strategy_comparison_matrix.md`
- `docs\evaluation\department3_final_retrieval_configuration.md`
- `docs\evaluation\department3_retrieval_performance_report.md`

## Threshold calibration results

A threshold sweep was conducted on dense-vector results for the 41 verified questions. At top-k=3, threshold 0.40 produced 33 true positives, 1 false positive and 6 false negatives (97.1% precision; 84.6% recall) under the expected-source-hit evaluation proxy. Raising the threshold to 0.50 produced 24 true positives, 0 false positives and 15 false negatives (100% precision; 61.5% recall). At top-k=1 and threshold 0.40, results were 31 TP, 3 FP and 5 FN (91.2% precision; 86.1% recall).

Decision: use dense top-k=3 and 0.40 as the provisional calibration candidate, combined with verified-source eligibility, intent-specific filtering and safe abstention. The zero-FP result at 0.50 is limited to this small evaluation sample and comes with a substantial recall reduction.

Metric limitation: these figures measure expected-source retrieval hits, not passage-level answer correctness. Threshold calibration must not be represented as a guarantee that retrieved text supports every generated answer.
