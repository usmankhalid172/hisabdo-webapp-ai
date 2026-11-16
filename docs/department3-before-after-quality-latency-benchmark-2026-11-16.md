# Department 3 Before-vs-After Quality and Latency Benchmark Matrix

**Project:** HisabDo AI Business Assistant  
**Department:** Department 3  
**Benchmark date:** 16 November 2026  
**Branch:** purnoor-zafar-ai-intern

## 1. Benchmark method

The current benchmark used `tests/evaluation_question_set.json` and `HybridFaqRetriever`.

- Total golden questions: 10.
- Supported-source questions: 8.
- No-match questions: 2.
- Retrieval depth: top 3.
- Timing repetitions: 30 per question.
- Timing samples: 300 per run.
- Two independent benchmark runs were completed.

Precision@3 was calculated as the number of expected source IDs found in the returned top three divided by 3. Recall@3 was calculated as the number of expected source IDs found in the returned top three divided by the total expected source IDs for that query. Macro scores are the arithmetic mean across the eight supported questions.

Latency measures the local `retrieve()` operation only. It excludes LLM generation, network/API calls, backend financial-data access, and complete response rendering.

## 2. Historical baseline versus current results

| Metric | Historical evidence | Current evidence | Comparison |
|---|---:|---:|---|
| Golden retrieval top-1 | 10/10 (15 Oct evaluation report) | 10/10 | No top-1 regression |
| Day 1 security suite | 62 passed (2 Nov baseline) | 62 passed | Same pass count |
| Full test suite | Comparable historical final count not established | 387 passed, 4 skipped | Current result recorded |
| Precision@3 | Not recorded | 45.83% | No historical comparison available |
| Recall@3 | Not recorded | 95.83% | No historical comparison available |
| Retrieval latency | Not recorded | 1.186 ms average in Run 2 | No historical comparison available |
| End-to-end response latency | Not recorded | Not measured | Measurement gap |

The historical and current top-1 retrieval results are both 10/10. This establishes no observed regression on that metric, not an improvement. Historical precision, recall, and latency values were not available, so percentage improvement cannot be calculated.

## 3. Current per-query quality matrix

| Case | Expected source IDs | Retrieved top 3 | Precision@3 | Recall@3 | Result |
|---|---|---|---:|---:|---|
| EVAL-01 | faq-002 | faq-002, finance_003, faq-001 | 33.33% | 100% | Top-1 PASS |
| EVAL-02 | faq-002 | faq-002, finance_003, faq-001 | 33.33% | 100% | Top-1 PASS |
| EVAL-03 | faq-005 | faq-005, faq-003, faq-001 | 33.33% | 100% | Top-1 PASS |
| EVAL-04 | faq-005 | faq-005, faq-003, faq-002 | 33.33% | 100% | Top-1 PASS |
| EVAL-05 | faq-005 | faq-005, finance_006, finance_001 | 33.33% | 100% | Top-1 PASS |
| EVAL-06 | faq-002 | faq-002, faq-001, finance_003 | 33.33% | 100% | Top-1 PASS |
| EVAL-07 | faq-004, faq-006, finance_004 | finance_004, faq-004, faq-006 | 100% | 100% | Top-1 PASS |
| EVAL-08 | faq-006, finance_001, finance_004 | faq-006, finance_004, faq-004 | 66.67% | 66.67% | Top-1 PASS |
| EVAL-09 | No expected source | No results | N/A | N/A | No-match PASS |
| EVAL-10 | No expected source | No results | N/A | N/A | No-match PASS |

## 4. Macro quality summary

| Metric | Current result |
|---|---:|
| Macro Precision@3 | 0.4583 (45.83%) |
| Macro Recall@3 | 0.9583 (95.83%) |
| Supported-query top-1 accuracy | 8/8 (100%) |
| No-match checks | 2/2 |
| EVAL-08 recall@3 | 0.6667 (66.67%) |

EVAL-08 did not return expected source `finance_001` in the top three. EVAL-01 through EVAL-06 returned the expected top-ranked source but also returned two additional sources, lowering Precision@3.

## 5. Retrieval latency matrix

| Latency statistic | Run 1 | Run 2 |
|---|---:|---:|
| Average | 1.405 ms | 1.186 ms |
| Median | 1.406 ms | 1.345 ms |
| Minimum | 0.006 ms | 0.005 ms |
| Maximum | 9.157 ms | 3.685 ms |
| Samples | 300 | 300 |

The two runs show similar central latency values, with different observed maxima. These are local retrieval timings and must not be presented as complete chatbot response times.

## 6. Benchmark conclusion

The current golden set shows full expected-source top-1 accuracy for supported questions and correct no-match behavior for both unsupported/ambiguous cases. Recall@3 is high overall, but Precision@3 is comparatively low. EVAL-08 requires retrieval-ranking review because one expected source is missing from its top three.

There is no historical precision/recall or latency baseline in the inspected records. Therefore, those metrics are established as current measurements only; no before/after improvement claim is made. Full end-to-end response latency remains unmeasured.
