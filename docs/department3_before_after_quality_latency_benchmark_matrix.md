# Department 3 Before vs After Quality and Latency Benchmark Matrix

Date: 16 November 2026

## 1. Evaluation Scope

Day 1 reference dataset: 71 cases, 55 answerable, 16 no answer or clarification cases.

Current offline benchmark dataset: 71 cases, 60 answerable, 11 no source cases.

The different answerable case counts mean that direct Day 1 versus current retrieval comparisons are not fully equivalent.

## 2. Retrieval Quality Matrix

| Strategy | Hit at 1 | Hit at 3 | Hit at 5 | Evaluation |
|---|---:|---:|---:|---|
| Day 1 TF IDF reference | 89.09% | 96.36% | Not recorded | Original baseline |
| Current offline TF IDF | 88.33% | 95.00% | 96.67% | Current benchmark baseline |
| Normalized TF IDF | 88.33% | 95.00% | 96.67% | No change from TF IDF |
| BM25 | 85.00% | 96.67% | 98.33% | Lower first result, better wider ranking |
| BM25 and TF IDF hybrid | 93.33% | 96.67% | 98.33% | Experimental hybrid |
| Expanded hybrid | 91.67% | 96.67% | 100.00% | Experimental |
| Feature intent 020 | 95.00% | 98.33% | 100.00% | Best reported strategy |

## 3. Same Dataset Improvement

The fairest comparison is between strategies tested on the same current dataset of 60 answerable cases.

| Metric | Current TF IDF | Feature intent 020 | Difference |
|---|---:|---:|---:|
| Hit at 1 | 88.33% | 95.00% | +6.67 percentage points |
| Hit at 3 | 95.00% | 98.33% | +3.33 percentage points |
| Hit at 5 | 96.67% | 100.00% | +3.33 percentage points |

These are offline benchmark results, not active API results.

## 4. Day 1 Comparison Caveat

| Metric | Day 1 reference | Current offline TF IDF |
|---|---:|---:|
| Answerable cases | 55 | 60 |
| Hit at 1 | 89.09% | 88.33% |
| Hit at 3 | 96.36% | 95.00% |

The current figures are 0.76 percentage points lower at Hit at 1 and 1.36 points lower at Hit at 3. However, the answerable case count and no source classification differ. These figures should not be presented as a confirmed regression or improvement until the datasets are reconciled.

## 5. Active Pipeline Status

The active API retriever uses TF IDF and cosine similarity with a 0.30 relevance threshold.

The offline benchmark includes local BM25, normalized score combinations, synonym expansion, heuristic metadata filtering, and lexical overlap reranking.

No dense embedding model was installed or measured. The benchmark reranker is not a learned cross encoder. Active API integration of the experimental strategies has not been verified.

Consequently, the best offline benchmark score cannot be attributed to the current chatbot runtime.

## 6. Latency Matrix

| Measurement | Day 1 baseline | Current local measurement |
|---|---|---:|
| Mean response latency | Not recorded | 8.79 ms |
| Median response latency | Not recorded | 8.11 ms |
| P95 response latency | Not recorded | 14.20 ms |
| Minimum | Not recorded | 6.41 ms |
| Maximum | Not recorded | 22.35 ms |
| Measurement setup | Not available | 10 warmups, 50 timed calls |

Current latency was measured using an in process TestClient with the mock LLM provider. It is not production network latency. No before and after latency improvement can be calculated without a comparable Day 1 measurement.

## 7. API Smoke Test Quality

Five FAQ questions were checked through the local API.

| Check | Result |
|---|---:|
| Successful HTTP responses | 5 of 5 |
| Correct RAG route | 4 of 5 |
| Responses with at least one citation | 4 of 5 |
| Responses with a source URL | 0 of 5 |
| Incorrect export question route | 1 of 5 |

The export instructions question was routed to the financial backend and returned synthetic financial values. The cash flow statement response included faq 005 evidence in context but did not include faq 005 in its citations.

## 8. Automated Regression Matrix

| Validation area | Result |
|---|---|
| Full automated suite | 341 passed, 4 skipped, 1 warning |
| Selected Phase 2 test group | 94 passed |
| Cross user, safety, adversarial tests | 37 passed |
| Chatbot, financial security, integration readiness | 34 passed |
| Multi turn and safety focused tests | 13 passed |
| Production backend validation | Not performed |
| Production LLM validation | Not performed |
| Complete manual 10 question golden set API run | Not performed |

Focused test groups overlap and their counts are not additive.

## 9. Overall Assessment

Offline retrieval quality improved with feature_intent_020 compared with the current offline TF IDF baseline. The active API still uses TF IDF only, so this improvement is not yet verified in runtime.

The local automated suite passed, but the API smoke test found one high priority routing defect and incomplete citation attribution. Current latency is measured only in a local mock environment.

Final status: Local automated regression passed. Full Phase 2 production end to end validation remains incomplete.