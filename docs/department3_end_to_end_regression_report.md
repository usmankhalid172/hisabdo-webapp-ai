# Department 3 End to End Regression Report

Date: 16 November 2026

## 1. Executive Summary

The local automated test suite passed with 341 passed, 4 skipped, and 1 warning. Selected chatbot, retrieval, grounded response, safety, adversarial, cross user boundary, and integration tests also passed.

However, end to end validation identified a high priority routing defect. The question "How do I export my expenses?" was incorrectly routed to the financial backend and returned synthetic account figures instead of the documented export instructions.

The local test results do not establish production readiness. The configured LLM and financial backend are mocks, and the active API retriever does not use the experimental hybrid benchmark strategy.

Overall result: Automated tests passed, but end to end release clearance is not granted.

## 2. Scope

The requested validation covered:

1. Day 1 golden questions
2. Retrieval benchmark and failed query cases
3. Grounded answers and source citations
4. Multi turn financial conversation tests
5. Adversarial and safety tests
6. Cross user financial data boundaries
7. Local endpoint response latency
8. Comparison with the Day 1 baseline

The complete 71 case retrieval dataset was evaluated offline. A five question live API smoke sample was also inspected. A complete manual API execution of all Day 1 golden questions was not performed.

## 3. Automated Test Results

Full test suite:

341 passed, 4 skipped, 1 warning, 6.85 seconds.

Selected test groups:

| Test group | Result |
|---|---:|
| Chatbot, retrieval, RAG pipeline, grounded response, safety, adversarial, cross user, integration readiness | 94 passed |
| Cross user, safety, adversarial | 37 passed |
| Chatbot, financial API security, integration readiness | 34 passed |
| Multi turn and safety focused tests | 13 passed |

These groups overlap and must not be added together.

The full suite has the same pass and skip counts as the previously recorded 13 November run. No automated test regression was observed in these runs.

## 4. Retrieval Benchmark

Dataset: 71 cases.
Corpus: 12 documents.
Answerable cases: 60.
No source cases: 11.

The best reported offline strategy was feature_intent_020:

| Metric | Result |
|---|---:|
| Hit at 1 | 95.00% |
| Hit at 3 | 98.33% |
| Hit at 5 | 100.00% |

The current offline TF IDF baseline scored 88.33% at 1, 95.00% at 3, and 96.67% at 5.

On the same 60 answerable cases, feature_intent_020 improved Hit at 1 by 6.67 percentage points, Hit at 3 by 3.33 points, and Hit at 5 by 3.33 points compared with the offline TF IDF baseline.

These results belong to the offline benchmark script. They do not prove that the experimental strategy is active in the chatbot API.

## 5. Day 1 Baseline Comparison

The Day 1 reference recorded 71 cases, 55 answerable cases, and 16 no answer or clarification cases. Its TF IDF results were Hit at 1 of 89.09% and Hit at 3 of 96.36%.

The current benchmark uses 60 answerable cases and 11 no source cases. Because the answerable case counts differ, direct before and after regression claims are not reliable. The current offline TF IDF results are 88.33% at 1 and 95.00% at 3.

The evaluation dataset composition must be reconciled before claiming a definitive Day 1 improvement.

## 6. Active Runtime Verification

The active FAQ retriever in src/financial_assistant/faq_rag.py uses scikit learn TF IDF and cosine similarity with a relevance threshold of 0.30.

The inspected active retriever does not implement dense embeddings, BM25, hybrid retrieval, chunking, or a learned reranker. The separate benchmark contains experimental BM25 and TF IDF combinations, but their integration into the active API was not established.

The benchmark reports that no dense embedding model was installed. Its BM25 implementation is local, and its reranker uses lexical overlap.

Therefore, the complete Phase 2 hybrid retrieval pipeline is not verified as active.

## 7. API Smoke Test and Citation Checks

Five FAQ questions were sent through the local chatbot API.

| Question | Observed result |
|---|---|
| What is HisabDo? | RAG response, faq 001 citation |
| How does automatic expense categorization work? | RAG response, faq 002 citation |
| What is a cash flow statement? | RAG response, faq 004 and faq 006 citations |
| How do I export my expenses? | Incorrectly routed to financial backend |
| What is revenue? | RAG response, finance 002 citation |

Four of five requests returned at least one citation. None of the five returned a nonempty source URL. The cash flow statement response included faq 005 evidence in its context, but faq 005 was absent from the returned citation list.

The knowledge base contains the export instructions in faq 005. The observed failure is therefore a routing issue, not a missing FAQ document.

## 8. Financial Privacy and Conversation Safety

The focused cross user, safety, and adversarial tests passed. The inspected service includes checks for authenticated customer identity and blocks third party financial requests before calling the LLM.

Multi turn tests also passed for the tested local cases.

These results verify the tested local behavior only. The financial backend is a deterministic mock, and production account ownership, real session isolation, and concurrent customer access have not been verified against a live backend.

The export question defect is important. A product instruction question returned synthetic financial account figures because the classifier treated the phrase "my expenses" as a personal financial data request. No cross user leak was demonstrated, but this behavior must be corrected and tested.

## 9. Latency Measurement

A local in process TestClient measurement used 10 warmup calls and 50 timed requests. The configured LLM provider was mock.

| Measurement | Result |
|---|---:|
| Mean | 8.79 ms |
| Median | 8.11 ms |
| P95 | 14.20 ms |
| Minimum | 6.41 ms |
| Maximum | 22.35 ms |

These figures are local mock environment measurements, not production network latency. A comparable Day 1 endpoint latency measurement was not available, so no before and after latency improvement can be claimed. Pytest execution time is not endpoint latency.

## 10. Defects and Risks

High priority: Export instructions are incorrectly routed to the financial backend. The response returns synthetic account values instead of export guidance.

Medium priority: The cash flow statement response does not cite every relevant FAQ item included in its evidence context.

Medium priority: All five sampled responses lacked a source URL. Approved source links and URL attribution need verification.

Release blocker: The active API retriever remains TF IDF only. Experimental hybrid results have not been shown to run in the active request path.

Release blocker: The production LLM and real financial backend contract are not configured and verified in this environment.

Release blocker: Production session isolation, real account ownership, and concurrent access tests remain outstanding.

## 11. Final Assessment

Automated regression status: Passed for the executed local suite.

Retrieval benchmark status: Experimental improvement demonstrated offline.

API smoke test status: One high priority functional routing defect found in five sampled questions.

Citation status: Partial. Citation presence was observed, but source URL attribution was absent and one relevant evidence item was not cited.

Production readiness: Not cleared.

The system must not be described as fully validated for production until the routing defect is fixed, the active hybrid pipeline is verified, source attribution is corrected, and the real backend and LLM integration are tested.

No application code was modified during this validation.