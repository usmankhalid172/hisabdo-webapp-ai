# Day 8 — About Us & Core Services Verification Package

Prepared for: Muhammad Daniyal  
Date: 16 November 2026  
Repository examined: `hisabdo-webapp-ai-main (3)(1).zip`

## Files
- `About_Us_Core_Services_Integration_Test_Log.docx` — integration findings, execution log, limitations and remediation priorities.
- `Service_Inquiry_Benchmark_Sheet.xlsx` — 22 query scenarios, observed results, source references, latency and status.

## Summary
- 22 service inquiry scenarios: 13 PASS, 2 PARTIAL, 7 FAIL.
- Assistant test suite: 107 passed, 1 deselected, 3 warnings.
- Index: 976 chunks; matrix shape 976 × 2,109.
- Mock API latency: median 3.44 ms; p95 25.31 ms; maximum 39.77 ms.
- No live Groq/API call was made.

## Important limitations
The environment lacked `slowapi` and `openai`; temporary import shims were used for the assistant test run. The `slowapi` shim was a pass-through, so rate limiting was not validated. The provider was `MockLLMProvider`; these timings do not represent live LLM latency.

The repository does not implement an actual sales handoff/CRM flow. The backend accepts and forwards caller-supplied history, but does not persist a conversation session keyed by `conversation_id`.

The embedding implementation uses TF-IDF, while the stored metadata and some README text still identify a multilingual SentenceTransformer. The current TF-IDF query path does not translate Urdu-script queries before retrieval.

## Submission note
This is an evidence-backed partial integration result. It should not be represented as a production-readiness pass until the high-priority findings are resolved and the benchmark is rerun with the real provider and dependencies.
