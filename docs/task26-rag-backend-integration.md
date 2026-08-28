# Task 26 — Chatbot / RAG Backend Integration (Application Service Layer)

**Assignee:** Ahmed Ali Ghori
**Status date:** 2026-08-28
**Branch:** `feature/task26-rag-backend-ahmed`
**Base branch:** `main`
**Deliverable:** working integrated Chatbot/RAG endpoint script + integration
verification logs + GitHub PR.

---

## 1. Goal

Integrate the ready Chatbot/RAG functionality into the main Capstone
application service layer, then:

- test **live API responses** over real HTTP (not the in-process TestClient),
- **resolve endpoint connection issues**,
- ensure **error handling prevents backend crashes when fetching document
  contexts**.

The chatbot/RAG surface here is the FastAPI service in `src/` (entrypoint
`src/main.py`) and its service-layer adapter
`src/financial_assistant/service.py` (`handle_chat`), exposed by
`POST /api/v1/chatbot`.

## 2. What was done

### 2a. Resolved endpoint-connection issue: RAG module/package name collision

`main` carried BOTH a module `src/financial_assistant/rag.py` (the chatbot's
`FaqRetriever` / `get_retriever`) AND a package
`src/financial_assistant/rag/` (holding `knowledge_base.py`,
`retriever.py`). When a package and a module share a name, Python imports the
**package**, so `from .rag import get_retriever` in `service.py` failed and
the whole chatbot router could not be imported - the service never started
for the chatbot route.

Fix: the package `rag/` is now the single canonical RAG namespace. The
chatbot's `FaqRetriever` + `get_retriever` were moved into
`rag/faq.py`, all RAG symbols are re-exported from `rag/__init__.py`, and the
colliding `rag.py` module was deleted. `service.py`'s existing
`from .rag import get_retriever` import still works (resolved by the package
re-export), and `tests/test_retrieval.py` (which imports the package's
`knowledge_base`/`retriever`) is unchanged.

### 2b. Error handling: document-context fetch must never crash the backend

`src/financial_assistant/service.py` now wraps every external dependency so a
failure degrades gracefully instead of raising up to the HTTP layer (a 500):

| Dependency | On failure |
|---|---|
| RAG / document-context retrieval (`get_retriever().retrieve`) | falls through to the general reply path (`source="llm_general"`), logged, never a 500 |
| Backend financial API (`get_user_financial_summary`) | returns a user-safe fallback with `source="backend_unavailable"`, logged |
| LLM provider (`generate_reply`) | returns `FALLBACK_REPLY`, logged |

In addition, `rag/faq.py`'s `FaqRetriever` is resilient to a **missing,
unreadable, or malformed** FAQ corpus (`data/faq_docs.json`): `retrieve`
returns an empty list (``loaded is False``) instead of raising
`FileNotFoundError`/`JSONDecodeError`, so the service layer can always fall
back cleanly.

Failures are emitted to a module logger for observability and are never leaked
to the client (the shared `{error_code, message, request_id}` contract is
preserved for the 401/404/422 paths).

## 3. Verification (evidence, not estimates)

### 3a. Live API responses (real uvicorn over HTTP)

`scripts/task26_live_api_verification.py` starts the real server on a free
port, waits for readiness (connection retry), and exercises
`/api/v1/*` over genuine HTTP. All checks pass:

```text
[PASS] endpoint connection / server readiness
[PASS] GET /api/v1/health -> 200 | status=ok
[PASS] GET /api/v1/version -> 200 | service=hisabdo-ai-service
[PASS] POST /api/v1/chatbot (RAG document-context query)    | source=rag   intent=product_faq
[PASS] POST /api/v1/chatbot (own-financial-data query)      | source=backend_financial_api intent=own_financial_data
[PASS] POST /api/v1/chatbot (general, no RAG match)         | source=llm_general intent=general
[PASS] bad auth token -> 401 (no crash)
[PASS] invalid body (empty message) -> 422 (no crash)
[PASS] unknown path -> 404 (no crash)
[PASS] server still healthy after error cases
TASK 26 RESULT: ALL CHECKS PASSED
```

Full log: `docs/evidence/task26-live-api-log.txt`.

### 3b. Robustness tests (never crash on failure)

`tests/test_task26_chatbot_robustness.py` covers:

- RAG retriever raises  -> graceful `llm_general` reply, no crash
- malformed KB corpus   -> `FaqRetriever.loaded is False`, empty retrieve
- missing KB corpus     -> same graceful degradation
- backend API raises    -> `source="backend_unavailable"`, safe reply
- LLM provider raises   -> `FALLBACK_REPLY`, no crash
- live endpoint         -> 200 for a valid query; 422 for an empty message

### 3c. Test suite

The Chatbot/RAG/API test groups pass (`tests/test_chatbot.py`,
`test_retrieval.py`, `test_integration_api.py`,
`test_health_version.py`, `test_llm_service.py`,
`test_task26_chatbot_robustness.py`). The pre-existing expense-categorization
failures (missing committed ML model file) are unrelated to this task and
unchanged.

## 4. Endpoint contract (unchanged for consumers)

| Endpoint | Success | Errors (never crash) |
|---|---|---|
| `GET /api/v1/health` | 200 `{status}` | — |
| `GET /api/v1/version` | 200 `{service, version, model_provider}` | — |
| `POST /api/v1/chatbot` | 200 `{reply, conversation_id, intent, source, tokens_used}` with `source in {rag, backend_financial_api, llm_general, backend_unavailable}` | 401 bad token, 422 validation |

## 5. Files changed

- `src/financial_assistant/rag/faq.py` (new) - chatbot FAQ retriever, moved
  from the deleted `rag.py`, with missing/corrupt-corpus resilience.
- `src/financial_assistant/rag/__init__.py` - re-exports the unified RAG
  namespace (fixes the collision).
- `src/financial_assistant/rag.py` (deleted) - removed to fix the
  module/package collision.
- `src/financial_assistant/service.py` - graceful error handling for RAG,
  backend client, and LLM provider.
- `tests/test_task26_chatbot_robustness.py` (new) - no-crash guarantees.
- `scripts/task26_live_api_verification.py` (new) - live HTTP verification.
- `docs/evidence/task26-live-api-log.txt` (new) - live API evidence.
- `docs/task26-rag-backend-integration.md` (this file).
