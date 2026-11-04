# Career Domain Day 7 Final Evaluation & Handover

**Owner:** Muhammad Daniyal  
**Date:** 4 November 2026  
**Repository archive evaluated:** `hisabdo-webapp-ai-main (3).zip`

## Package contents
- `Career_Day7_Final_Evaluation_Report.docx` and `.md` — full measured report.
- `Live_Chatbot_10_Query_Results.csv` — exact ten responses supplied from the live website chatbot.
- `Retrieval_Top5_Benchmark.csv` — top-five retrieval target ranks using the saved repository index.
- `Local_API_Performance_30_Requests.csv` and `Local_API_Performance_Raw.json` — 30 local mock-provider measurements.
- `Citation_Audit.csv` — link syntax, allow-list and relevance review.
- `Release_Clearance_Log.csv` — measured evidence and release status.
- `Day7_Measurement_Summary.json` — machine-readable summary and archive SHA-256.
- `day7_reproducible_local_check.py` — script for repeating local TestClient latency/repeatability checks.
- `Automated_Test_Evidence.txt` — exact automated test outcomes and environment limitations.

## Headline results
- Live chatbot answers: **5 pass, 1 partial, 4 fail** (10 manually supplied answers).
- Offline retrieval: **Hit@5 90%, Precision@5 18%, MRR@5 0.7333** on the ten target chunks.
- Local API: **30/30 HTTP 200**, **10/10 repeat groups identical** with `MockLLMProvider`.
- Local mock API latency: mean **7.75 ms**, median **3.98 ms**, p95 **34.56 ms**. These are local measurements, not production latency.
- XICTEK test folder: **107 passed, 1 failed, 3 warnings**. The failure is a stale test asserting the index is absent, while this ZIP includes 976 chunks and the endpoint reports the index built. Excluding that stale assertion: 107 passed, 1 deselected.


## Important measurement boundaries
The live chatbot responses are the actual responses pasted by the user. Repository checks are local/offline and use the saved index and mock LLM. `slowapi` and `openai` were unavailable in this offline runtime, so temporary import stubs were used for the XICTEK test folder and local TestClient checks. The slowapi decorator was not active in these runs; rate limiting was not tested. No real Groq/OpenAI-compatible generation, external website reachability, production latency, token telemetry, or live widget-to-repository integration was measured.

## Main blockers
1. Four of ten live answers fail the requested intent; one is incomplete.
2. Internship questions about eligibility, benefits and roadmap all received the same duration-only answer.
3. Q9's expected internship-benefits chunk (`faq-92`) is absent from top five and top eight retrieval results.
4. `metadata.json` claims a Sentence-Transformers model, while the current code and persisted vectorizer use TF-IDF. The vectorizer pickle warns it was produced with scikit-learn 1.5.2 and loaded under 1.8.0.
5. One repository test has an outdated expectation that the index is not built.
6. Repository README says the index has not been built and the live widget integration is deferred; this archive actually contains a 976-chunk index, but the widget integration remains unverified.

**Decision:** Do not mark the Careers domain release-cleared until the answer failures, retrieval miss, index metadata/version consistency, and production integration evidence are addressed.
