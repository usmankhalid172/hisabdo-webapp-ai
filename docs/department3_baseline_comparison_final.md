# Department 3 Baseline Comparison Report

Report date: 2026-11-04
Dataset version: 1.0.0

## 1. Purpose

This report compares the historical retrieval results with the current Department 3 retrieval evaluation. It also records limitations that prevent a controlled before and after comparison.

## 2. Historical Baseline

Historical evaluation dataset: 20 questions
Answerable questions: 16
No answer questions: 4
Knowledge records: 12 FAQ records

| Method | Hit at 1 | Hit at 3 |
|---|---:|---:|
| TF IDF baseline | 68.75% | 93.75% |
| Normalized query | 68.75% | 93.75% |
| Synonym expansion | 81.25% | 93.75% |
| Expansion with reranking | 81.25% | 87.50% |

## 3. Current Department 3 Results

Dataset: data/department3_evaluation_v1.json
Results: docs/department3_evaluation_v1_results.json
Evaluation date: 2026-11-01

| Metric | Result |
|---|---:|
| Total questions | 71 |
| Answerable questions | 55 |
| No answer or clarification questions | 16 |
| Hit at 1 | 89.09% |
| Hit at 3 | 96.36% |
| No answer cases with retrieved sources | 16 of 16 |

Retrieval method: TF IDF with unigram and bigram features, sublinear term frequency, and top 3 ranking.

## 4. Comparison

| Metric | Historical baseline | Department 3 evaluation |
|---|---:|---:|
| Dataset questions | 20 | 71 |
| Hit at 1 | 68.75% | 89.09% |
| Hit at 3 | 93.75% | 96.36% |

The numerical differences are 20.34 percentage points for Hit at 1 and 2.61 percentage points for Hit at 3.

These differences must not be presented as confirmed performance improvements. The datasets, question coverage, and evaluation setup are different.

## 5. Important Findings

1. The current dataset measures retrieval across common questions, paraphrases, misspellings, Roman Urdu, ambiguity, and no answer cases.
2. Current Hit at 3 is 96.36% for answerable cases.
3. All 16 no answer or clarification cases still retrieved a source.
4. Retrieval ranking does not establish whether the final assistant response is correct or safe.
5. Actual generated responses have not been scored using the full quality rubric.

## 6. Data Reconciliation

The baseline report states that the evaluation uses 12 knowledge documents. The inspected source files contain 12 FAQ records and 6 sample financial knowledge records.

The exact document count and evaluation corpus composition must be confirmed before the next evaluation release.

## 7. Missing Measurements

The following measurements are not available:

1. Generated response factual accuracy.
2. Citation correctness.
3. Answer completeness.
4. English, Urdu, and Roman Urdu language quality scores.
5. End to end safe abstention rate.
6. Production p50, p95, and p99 latency.
7. Verified production provider costs.
8. Real backend financial data retrieval and production session isolation.

## 8. Recommended Next Evaluation

Run both the historical and current methods against the same approved dataset version and settings. Save actual assistant responses, retrieved source IDs, per dimension scores, abstention decisions, safety failures, and response timings.

## 9. Conclusion

The current Department 3 retrieval evaluation records Hit at 1 of 89.09% and Hit at 3 of 96.36%. These are measured retrieval results, not complete answer quality scores.

A controlled comparison, production backend verification, and end to end response evaluation remain necessary before release clearance.
