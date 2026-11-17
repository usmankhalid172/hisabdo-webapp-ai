# Department 3 — Production Configuration Freeze

## 1. Purpose
This document records the verified local configuration for the HisabDo Department 3 AI assistant. It is a configuration record, not production deployment approval.

## 2. Verified Runtime
- Python: 3.12.10
- FastAPI: 0.115.0
- Starlette: 0.38.6
- scikit-learn: 1.5.2

## 3. FAQ Retrieval Configuration
- Relevance threshold: 0.30
- Embedding model: text-embedding-3-small
- Default retrieval top_k: 1
- FAQ encoding: UTF-8
- Embedding provider: OpenAI when configured
- Fallback: TF-IDF when embedding initialization fails
- Empty queries and invalid top_k values return no results.
- Ambiguous balance queries are guarded.
- Query embedding failures return no matches.

## 4. Service Integration Boundary
The service currently calls the FAQ retriever directly with top_k=1.
Hybrid retrieval and reranking components have tests, but their use in the production service path has not been verified.

## 5. Verification Evidence
- Focused regression tests: 39 passed.
- Full test suite: 389 passed, 4 skipped.
- Full suite warnings: 69.
- No production deployment was performed as part of this verification.

## 6. Known Risks and Open Items
1. EVAL-08 retrieval coverage requires further review.
2. Precision@3 requires improvement for selected evaluation queries.
3. Production financial backend connectivity is unverified.
4. Production session isolation is unverified.
5. Complete multi-turn financial workflows require independent verification.
6. Citation rendering and source-conflict handling require verification.
7. End-to-end latency and provider costs have not been measured.
8. Persisted scikit-learn artifacts were created with version 1.7.2 while the current runtime is 1.5.2.
9. pytest-asyncio fixture loop scope is not explicitly configured.
10. Starlette/AnyIO deprecation warning remains.

## 7. Freeze Decision
Local configuration is documented for reproducible testing. Production readiness is NOT approved until the open items are verified, resolved, or formally accepted by the responsible team.

## 8. Change Control
Any future change to embedding model, threshold, retrieval strategy, dependencies, or service integration must be tested and documented before deployment.
