# Department 3 Baseline vs Optimized Retrieval Results

## Executive summary

The feature intent 0.20 strategy achieved the best measured aggregate result, with 95.00% Hit@1, 98.33% Hit@3, and 100.00% Hit@5. Its threshold calibration at 0.45 accepted 40 of 60 answerable cases, achieved 97.5% top 1 precision, and produced zero false accepts among 11 no source cases.

## Evaluation setup

- Evaluation cases: 71
- Cases with expected source records: 60
- Cases without expected source records: 11
- Corpus records: 12
- Evaluation source: `data/department3_evaluation_v1.json`
- Corpus source: current FAQ and sample financial knowledge records

A hit means at least one expected source record appears in the requested top k results. It does not mean the generated answer was factually correct.

## Baseline and optimized results

| Metric | TF IDF baseline | BM25 + TF IDF hybrid |
|---|---:|---:|
| Hit@1 | 88.33% | 93.33% |
| Hit@3 | 95.00% | 96.67% |
| Hit@5 | 96.67% | 98.33% |

The hybrid improved Hit@1 by 3.34 percentage points and Hit@5 by 1.66 percentage points. Hit@3 remained unchanged.

## Threshold findings

At feature intent 0.20 threshold 0.45:
- 40 of 60 answerable cases were accepted.
- Top 1 precision among accepted cases was 97.5%.
- None of the 11 no source cases was accepted.

At feature intent 0.20 threshold 0.50:
- 34 of 60 answerable cases were accepted.
- Precision was 97.1%.
- Zero of 11 no source cases were falsely accepted.
- None of the 11 no source cases was accepted.

Threshold 0.45 is the preferred conservative experimental setting because it produced zero observed false accepts in this small test set. It still rejects 20 answerable cases. D3E028 has the correct faq-005 source ranked first at 0.4139, but falls below the threshold. Fallback handling remains essential.

BM25 raw scores alone were not suitable for rejection decisions. Even high thresholds continued to accept most no source cases. Query wise score normalization was also rejected because it made the highest candidate score comparable across unrelated queries and caused misleading threshold results.

## Known unresolved cases

D3E028, asking where the FAQ says expense exports are available, still retrieves expense categorization content above the expected export FAQ. This is a known retrieval failure and requires a tested query rewrite or better approved source wording.

D3E014 is retrieved correctly by both BM25 and the corrected hybrid. D3E004 and D3E024 are also retrieved correctly by the hybrid. Roman Urdu cash flow and profit questions D3E042 and D3E043 retrieve relevant sources in top 1.

## Conclusions

The hybrid is the best current candidate for top 1 retrieval. BM25 remains useful for recall. Global metadata filtering, broad query expansion and the tested reranker did not improve the overall result and should not be enabled by default.

Dense vector search remains untested. No production claim should describe this benchmark as a dense semantic comparison.

## Release limitations

The benchmark does not establish a guarantee that every returned passage contains all relevant rules or specifications. Production use still requires approved source ownership, stronger negative and adversarial test coverage, answer level evaluation, real backend verification and a larger independently reviewed dataset.
