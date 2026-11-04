# Career Domain Final Evaluation & Handover Report

**Owner:** Muhammad Daniyal  
**Date:** 4 November 2026  
**Repository:** latest supplied archive `hisabdo-webapp-ai-main (3).zip`  

## 1. Executive summary

The ten live website-chatbot responses supplied during this evaluation were assessed against the Careers and Internship FAQ facts. Results: **5 pass, 1 partial, 4 fail**. The most serious pattern is that four different internship questions (Q6, Q7, Q9 and Q10) all received the same duration-only answer. Q6 is partial because duration was asked; Q7, Q9 and Q10 fail because eligibility, benefits and roadmap details were omitted. A first UI/UX question failed with a generic job list, while its paraphrase retest passed.

The saved repository index was independently benchmarked with the same ten questions. It contains 976 chunks. The expected target chunk appeared in top five for 9/10 queries (**Hit@5 90%, Precision@5 18%, MRR@5 0.7333**). The internship-benefits chunk `faq-92` was missed, and Q1's expected role-list chunk ranked third behind an unrelated HisabDo careers result.

A local FastAPI TestClient run using the saved index and `MockLLMProvider` produced 30/30 HTTP 200 responses and identical output/source tuples across all ten three-repeat groups. Local mean latency was 7.75 ms, median 3.98 ms, and nearest-rank p95 34.56 ms. These are **local mock-provider timings**, not production latency.

The XICTEK test folder produced 107 passes and one failure. The failure is an outdated test expecting an unbuilt index, despite the supplied archive containing 976 chunks and the endpoint reporting `index_built=true`. With that one stale assertion deselected, 107 tests passed. Dependency stubs were used because `slowapi` and `openai` were not installed and package installation was blocked by unavailable network access. Rate limiting and real LLM provider behavior were therefore not tested.

## 2. Live chatbot results (user-supplied production transcripts)

| Query | Result | Main finding |
|---|---|---|
| Q1 Current positions | PASS | Four job roles correct; “Student or Recent Graduate” is internship audience wording. |
| Q2 Senior Full-Stack skills | PASS | React, Next.js, .NET, PostgreSQL correct; generic blog citation is only partial support. |
| Q3 Mobile App skills | PASS | Flutter, React Native, iOS, Android correct; general mobile articles rather than job listing. |
| Q4 Cloud Architect skills | PASS | Azure, AWS, DevOps, Terraform correct; Careers source relevant. |
| Q5 UI/UX skills | FAIL | Generic role list returned instead of Figma, Design Systems, Prototyping. |
| Q6 Internship offer + duration | PARTIAL | Correct 12-week duration, but offer/benefits omitted. |
| Q7 Internship eligibility | FAIL | Duration repeated; eligibility omitted. |
| Q8 UI/UX paraphrase retest | PASS | Figma, Design Systems, Prototyping correctly returned. |
| Q9 Internship benefits | FAIL | Duration repeated; benefits omitted. |
| Q10 Internship roadmap | FAIL | Duration repeated; stages omitted. |

**Live answer score:** 5/10 pass (50%), 1/10 partial (10%), 4/10 fail (40%). No production response latency was supplied in the transcripts.

### Live citation review

All ten answers supplied source links (eleven URL instances because Q3 supplied two). All eleven passed static HTTPS and approved-host checks. This does not establish that each URL was reachable during this evaluation. Relevance grading: 7 strong, 2 partial, 1 weak for the exact requested detail. Q2 and Q3 cite general technical articles rather than role requirements. Q5's Careers link is broadly related but does not support the requested skills in the returned answer.

## 3. Offline retrieval benchmark

Method: loaded the exact persisted `embeddings.npy`, `chunks.json`, and TF-IDF vectorizer from the supplied ZIP; used the repository query-expansion and MMR retrieval behavior, `top_k=8`, relevance threshold 0.20; checked whether the expected target FAQ chunk appeared within the first five returned results. One target chunk was designated per query.

| Query | Expected chunk | Rank | Hit@5 |
|---|---|---:|---|
| Q1 | faq-74 | 3 | Yes |
| Q2 | faq-75 | 1 | Yes |
| Q3 | faq-76 | 1 | Yes |
| Q4 | faq-77 | 1 | Yes |
| Q5 | faq-78 | 1 | Yes |
| Q6 | faq-89 | 1 | Yes |
| Q7 | faq-93 | 2 | Yes |
| Q8 | faq-78 | 1 | Yes |
| Q9 | faq-92 | Not in top 8 | No |
| Q10 | faq-94 | 2 | Yes |

- **Hit Rate@5:** 9/10 = 90%
- **Precision@5:** 9 relevant target hits / 50 returned positions = 18% (single expected target per query)
- **MRR@5:** 0.7333
- **Miss:** Q9 benefits target `faq-92` did not appear in top eight. Top results included duration (`faq-89`), a HisabDo careers eligibility chunk (`faq-187`), roadmap (`faq-94`), and other unrelated material.
- **Cross-domain noise:** Q1 placed a HisabDo careers chunk at rank 2, ahead of the correct XICTEK roles chunk at rank 3.

These are local retrieval metrics on the supplied index, not metrics from the production chatbot endpoint.

## 4. Local API performance and repeatability

A local FastAPI TestClient run sent the ten benchmark questions three times each to `POST /api/v1/xictek/chat`, using the saved index and repository `MockLLMProvider`.

| Metric | Measured value |
|---|---:|
| Requests | 30 |
| HTTP 200 | 30/30 (100%) |
| Identical repeated output groups | 10/10 (100%) |
| Mean latency | 7.75 ms |
| Median latency | 3.98 ms |
| p95 (nearest rank) | 34.56 ms |
| Minimum / maximum | 3.02 / 50.78 ms |

**Boundary:** This is local TestClient + local retrieval + deterministic mock generation. It excludes public network, website widget, real provider latency, rate limiting, and production load. It must not be reported as live website performance.

## 5. Automated tests

- Initial XICTEK test-folder run: **107 passed, 1 failed, 3 warnings**.
- The sole failure is `test_index_status_reports_unbuilt_index_by_default`, which asserts `index_built is False`; actual API response is true and reports 976 chunks. The test expectation conflicts with the supplied archive contents.
- Rerun excluding only that stale assertion: **107 passed, 1 deselected, 3 warnings**.
- Runtime lacked `slowapi` and `openai`; temporary import stubs outside the repository allowed test collection and local TestClient execution. The slowapi decorator was a no-op, so rate limiting was not tested. The OpenAI-compatible provider was not called; `MockLLMProvider` was used.
- scikit-learn emitted a pickle compatibility warning: the saved TF-IDF objects were created with version 1.5.2 and loaded under runtime 1.8.0.

## 6. Repository and index audit

| Check | Result |
|---|---|
| Persisted chunks | 976 |
| Embedding matrix | 976 × 2,109 |
| TF-IDF vocabulary | 2,109 features |
| XICTEK Careers FAQ chunks | 10 |
| XICTEK Internship FAQ chunks | 8 |
| HisabDo Careers chunks | 13 |
| Chunk URLs with HTTPS + allow-listed host | 976/976 |

**Important inconsistency:** `metadata.json` names `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, but the current `embeddings.py` implementation is TF-IDF and the archive contains `tfidf_vectorizer.pkl`. The persisted matrix is 2,109-dimensional, consistent with the TF-IDF vectorizer rather than the stated 384-dimensional sentence-transformer. This stale metadata makes the index provenance unclear and should be corrected/rebuilt.

The repository README also says the index has not been built and that `data/index/` does not exist. That statement is stale for this ZIP: the index is present and the API reports 976 chunks. The live website widget integration is described as deferred in the module README; local route availability does not prove the production widget calls this endpoint.

## 7. Release clearance decision


Reasons:
1. Four of ten live answers fail and one is incomplete.
2. Internship eligibility, benefits and roadmap questions collapse to the same duration-only answer.
3. Q9 expected benefits chunk is not retrieved in top eight.
4. Embedding model metadata conflicts with the actual TF-IDF implementation and vectorizer artifact.
5. One automated test has an outdated index-state assertion.
6. Production latency, real provider telemetry, rate-limit behavior, external link reachability and website-widget integration remain unmeasured/unverified.

## 8. Recommended corrective actions

1. Fix intent-specific internship answer generation and add regression tests for eligibility, benefits, roadmap and duration.
2. Add query-focused retrieval/reranking or FAQ intent filters so the benefits chunk `faq-92` ranks in top five and HisabDo content does not outrank XICTEK Careers content.
3. Correct `metadata.json`, pin the scikit-learn version used to build the vectorizer, and rebuild/revalidate the index.
4. Update the stale index-status test to validate the actual fixture/index state rather than hard-code `false`.
5. Run the suite in CI with real `slowapi` dependency; exercise rate-limit behavior.
6. Obtain a production trace from the actual website widget and record request IDs, timings, provider/model, token usage and returned citations before claiming production latency or release clearance.

## 9. Reproduction

From repository root, with project dependencies installed and mock provider selected, run `day7_reproducible_local_check.py` from this package. It performs 30 local requests and reports repeatability and local latency. See `Automated_Test_Evidence.txt` for the exact test commands and limitations.
