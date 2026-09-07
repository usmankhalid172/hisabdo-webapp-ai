# Task 27 — Chatbot / RAG Backend Integration: Payload Finalization & Service-Layer Optimization

**Assignee:** Ahmed Ali Ghori
**Status date:** 2026-08-28
**Branch:** `feature/task27-rag-backend-ahmed`
**Base branch:** `feature/task26-rag-backend-ahmed` (PR #74 pending)
**Deliverable:** finalized chatbot/RAG response payload, optimized
backend-to-vector service-layer calls, integration test log + GitHub PR.

---

## 1. Goal

For the Chatbot/RAG backend integration surfaced in Task 26
(`POST /api/v1/chatbot` on `src/main.py`, service layer
`src/financial_assistant/service.py` → `handle_chat`), finalize and optimize:

1. **Payload formatting** — make the response self-describing and
   session-aware for the MERN/consumer backend, and type the conversation
   history so malformed payloads are rejected instead of passed through.
2. **Backend-to-vector service-layer calls** — avoid reconstructing costly
   objects per request (backend client, RAG/vector retriever) and reuse them
   across calls.

---

## 2. Payload formatting finalization

### 2a. Self-describing, session-aware `ChatbotResponse`

`src/schemas.py` — added three optional (non-breaking) fields to
`ChatbotResponse` so the consumer gets everything it needs from one reply:

| Field | Meaning | Populated |
|---|---|---|
| `user_id` | echoed back for session identity | every path |
| `model` | which provider/model answered (demo visibility) | every path |
| `matched_context` | retrieved FAQ doc *title* when `source=="rag"`, else `null` | RAG path only |

`src/financial_assistant/llm_providers.py` — each provider now exposes a
`model_name` label (`mock-llm`, `anthropic:claude-sonnet-4-6`,
`openai:gpt-4o-mini`) surfaced in `response.model`. Access is resilient
(`getattr(provider, "model_name", None)`) so stub/failing providers never
crash the reply path.

`src/financial_assistant/service.py` — `handle_chat` now builds every response
through a single `base(...)` helper that echoes `user_id`, sets `model`, and
fills `matched_context` only on the RAG path (from `matches[0].get("title")`).

### 2b. Typed conversation history

`ChatbotRequest.history` was `list[dict]` — an untyped hole where a consumer
could pass arbitrary payloads that Pydantic would not validate. Added a typed
`ChatHistoryEntry` model:

- `role`: `str` constrained to `user|assistant`
- `content`: `str` with `min_length=1`

`ChatbotRequest.history` is now `list[ChatHistoryEntry]`. Malformed entries
(e.g. `role="system"`, empty `content`) are rejected with **422
(no crash)** rather than silently forwarded to the LLM.

---

## 3. Backend-to-vector service-layer optimization

The chatbot service makes two expensive service-layer calls which previously
reconstructed state per request:

| Call | Before (Task 26) | After (Task 27) |
|---|---|---|
| Backend client (`get_backend_client`) | new client built on **every** call | process-wide singleton via `@lru_cache(maxsize=1)` in `src/integration/backend_client.py` |
| RAG/vector retriever (`get_retriever`) | already singleton via `@lru_cache` | kept + documented: TF-IDF matrix / vectorizer built **once** at construction; warm `retrieve()` only transforms the query |

Effect: the backend→service handshake and the backend→vector (retriever)
handshake now reuse a single client/matrix per process instead of rebuilding
per request. `FaqRetriever` state (vectorizer + tfidf matrix built at
construction) is reused across all warm queries.

---

## 4. Verification (evidence, not estimates)

### 4a. Live API payload (real uvicorn over HTTP)

`scripts/task27_live_api_verification.py` starts the real server on a free
port and verifies the finalized payload over genuine HTTP. All checks pass:

```text
TASK 27 LIVE API EVIDENCE - finalized chatbot/RAG payload
[PASS] endpoint connection / server readiness
[PASS] RAG reply carries user_id echo + model + matched_context
       | source=rag user_id=user-27 model=mock-llm ctx="What is a cash flow statement?"
[PASS] own-financial-data reply user_id + model, no context
       | source=backend_financial_api model=mock-llm
[PASS] general reply user_id + model, no context | source=llm_general model=mock-llm
[PASS] typed history (valid role/content) accepted
[PASS] typed history bad role -> 422 (no crash)
[PASS] typed history empty content -> 422 (no crash)
[PASS] server still healthy after all cases
TASK 27 RESULT: ALL CHECKS PASSED
```

Full log: `docs/evidence/task27-live-api-log.txt`.

### 4b. Integration test log

`tests/test_task27_payload_and_optimization.py` (9 tests) plus the existing
Task 26 Chatbot/RAG/API groups — **25 passed**:

- payload: `user_id` / `model` present on RAG, general, and own-financial-data
  paths + `matched_context` set only on RAG;
- typed history: valid entries accepted; bad role & empty content rejected;
- singletons: `get_backend_client()` and `get_retriever()` are process-wide
  singletons; retriever matrix built once and reused (deterministic warm
  retrieve).

Full run: `docs/evidence/task27-integration-test-log.txt`.

---

## 5. Endpoint contract (backward compatible)

`POST /api/v1/chatbot` success payload:

```json
{
  "reply": "...",
  "conversation_id": "...",
  "user_id": "...",          // NEW (echoed)
  "intent": "product_faq",
  "tokens_used": 12,
  "model": "mock-llm",       // NEW
  "matched_context": "...",  // NEW (doc title, RAG only)
  "source": "rag"
}
```

`history` now accepts `[{"role": "user"|"assistant", "content": "<len>=1"}]`;
any other entry shape → 422.

---

## 6. Files changed

- `src/schemas.py` — `ChatHistoryEntry` model; typed `ChatbotRequest.history`;
  added `user_id` / `model` / `matched_context` to `ChatbotResponse`.
- `src/financial_assistant/llm_providers.py` — `model_name` on `LLMProvider`
  and each concrete provider.
- `src/integration/backend_client.py` — `get_backend_client()` is now a cached
  singleton (`@lru_cache`).
- `src/financial_assistant/service.py` — `base(...)` helper in `handle_chat`
  populates `user_id` / `model` / `matched_context`; resilient `model` read.
- `tests/test_task27_payload_and_optimization.py` (new) — payload-formatting &
  singleton/optimization tests.
- `scripts/task27_live_api_verification.py` (new) — live HTTP payload proof.
- `docs/evidence/task27-live-api-log.txt` (new) — live evidence.
- `docs/evidence/task27-integration-test-log.txt` (new) — test evidence.
- `docs/task27-rag-backend-integration.md` (this file).
