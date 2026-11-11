# Department 3 Retrieval Strategy Comparison Matrix

## Scope
Evaluation used 71 cases from `data/department3_evaluation_v1.json` and 12 approved corpus records from the current FAQ and financial knowledge files. There were 60 cases with expected source records and 11 cases with no approved retrieval source.

## Strategy comparison

| Strategy | Hit@1 | Hit@3 | Hit@5 | Decision |
|---|---:|---:|---:|---|
| TF IDF baseline | 88.33% | 95.00% | 96.67% | Baseline |
| Normalized TF IDF | 88.33% | 95.00% | 96.67% | No measurable gain |
| BM25 | 85.00% | 96.67% | 98.33% | Useful lexical recall |
| BM25 + TF IDF hybrid | 93.33% | 96.67% | 98.33% | Lexical hybrid baseline |
| Expanded hybrid | 91.67% | 96.67% | 100.00% | Improved recall at top 5 |
| Expanded hybrid + reranker | 90.00% | 95.00% | 98.33% | Lexical reranker reduced top 1 |
| Metadata filtered hybrid | 81.67% | 91.67% | 93.33% | Not recommended as a global filter |
| Feature intent boost 0.05 | 93.33% | 98.33% | 100.00% | Improved top 3 and top 5 |
| Feature intent boost 0.15 | 93.33% | 98.33% | 100.00% | Same aggregate result as 0.05 |
| Feature intent boost 0.20 | 95.00% | 98.33% | 100.00% | Best measured candidate |
| Feature intent boost 0.25 | 95.00% | 98.33% | 100.00% | No gain over 0.20 |
| Dense semantic vector search | Not tested | Not tested | Not tested | No dense embedding model installed |

## Corrected threshold calibration

The corrected hybrid score uses a fixed BM25 transformation rather than query wise maximum normalization.

| Strategy | Threshold | Accepted answerable | Precision at top 1 | False accepts |
|---|---:|---:|---:|---:|
| Feature intent 0.20 | 0.30 | 53/60 | 98.1% | 5/11 |
| Feature intent 0.20 | 0.35 | 47/60 | 97.9% | 1/11 |
| Feature intent 0.20 | 0.40 | 45/60 | 97.8% | 1/11 |
| Feature intent 0.20 | 0.45 | 40/60 | 97.5% | 0/11 |
| Feature intent 0.20 | 0.50 | 34/60 | 97.1% | 0/11 |
| Feature intent 0.20 | 0.55 | 25/60 | 96.0% | 0/11 |
| Feature intent 0.20 | 0.60 | 12/60 | 100.0% | 0/11 |

The feature intent 0.20 threshold of 0.45 is the preferred conservative operating point in this dataset. It accepts 40 of 60 answerable cases, achieves 97.5% top 1 precision, and has zero observed false accepts among 11 no source cases. This is a measured result, not a universal guarantee. D3E028 ranks faq-005 first at 0.4139 but is rejected by the 0.45 threshold, showing the coverage tradeoff.

## Day 1 failed question review

| Case | Expected source | Finding |
|---|---|---|
| D3E004 | faq-001 | BM25 and hybrid retrieve the expected source in top 1 |
| D3E014 | faq-003 | BM25 and corrected hybrid both retrieve the expected source in top 1 |
| D3E024 | faq-005 | BM25 and hybrid retrieve the expected source in top 1 |
| D3E028 | faq-005 | All tested strategies miss the expected source in top 3 |
| D3E042 | Multiple sources | All strategies retrieve finance_004 in top 1 |
| D3E043 | Multiple sources | All strategies retrieve faq-006 in top 1 |

## Decision
Use hybrid retrieval as the experimental candidate. Keep BM25 and TF IDF results available for comparison. Do not enable global metadata filtering or the current reranker as production defaults. Resolve D3E028 with an approved query rewrite and a new evaluation run before declaring the Day 1 failures resolved.
