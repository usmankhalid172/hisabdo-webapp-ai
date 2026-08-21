# Day 18 — Chatbot / RAG Integration into the HisabDo AI Service Flow

**Status date:** 2026-08-21
**Branch:** `feature/ahmedali-ghori-ai-chatbot` /
`feature/ahmedali-ghori-chatbot-rag-integration-day-18`
**Aligned with:** Niha Batool's AI service boundaries (`src/integration/`) and
Farheen's RAG/retrieval research (`research/rag-approach.md`).

---

## 1. Target flow (as defined by the team)

```text
User -> HisabDo App -> Backend/API -> AI Service -> Model/LLM -> Validated Response -> User
```

Mapping to the implemented chatbot:

```text
User question
  -> FastAPI POST /chat            (src/integration/app.py)
  -> FinancialAssistant.ask()      (src/financial_assistant/engine.py)
       intent detection            (intents.py)           [NLP: rule-based]
       period/category resolution  (processor.py)         [NLP entity extraction]
       financial computation       (transactions.py)      [backend, never LLM]
       RAG retrieval               (retriever.py + knowledge_base.py)
       response builder            (responders.py)        [grounded]
       response validation         (response_validator.py)[hallucination guards]
       optional LLM polish         (llm.py)               [soft dependency, offline fallback]
  -> validated ChatResponse        (schemas.py)
  -> User
```

## 2. Service / endpoint purpose

| Endpoint | Method | Purpose | Returns |
|---|---|---|---|
| `/health` | GET | Service + dependency status (intents supported, KB chunks, transactions loaded, LLM availability) | `HealthResponse` |
| `/chat` | POST | Full assistant pipeline with evidence trace (intent, facts, retrieved chunks, validation result) | `ChatResponse` |
| `/intents` | POST | Intent detection only (inspection/debugging; no response building) | `IntentInfo` |

Server entry point: `scripts/run_api_server.py` (default port 8000,
`--port` override; port 8010 used in evidence due to local port conflict).

## 3. Request / response structure

### `POST /chat` request (`ChatRequest`)
```json
{
  "question": "How much did I spend this month?",
  "reference_date": "2026-08-21"
}
```
- `question`: required, 1-2000 chars (Pydantic-validated).
- `reference_date`: optional `YYYY-MM-DD`, regex-validated; used to anchor
  relative periods ("this month"). A per-request instance is created so the
  shared stateless instance is never mutated (no race conditions).

### `POST /chat` response (`ChatResponse`)
```json
{
  "question": "...", "intent": "MONTHLY_EXPENSE", "confidence": 0.75,
  "response": "Your total spending for August 2026 was PKR 410.35 across 10 transactions.",
  "period": "2026-08", "category": null,
  "facts": {"period": "2026-08", "total": 410.35, "count": 10, "categories": {...}},
  "retrieved": [{"title": "...", "score": 0.29, "text": "..."}],
  "validation": "pass", "validation_notes": [],
  "llm_used": false, "matched": ["period anchor", "period=None", "category=None"]
}
```
Every response carries the full pipeline trace so integration and testing can
prove grounding (no hallucinated figures).

## 4. Retrieval / RAG dependencies

- `knowledge_base.py` — loads `data/saving_tips.md`, chunks on `##` headings,
  attaches `tags` metadata (5 chunks).
- `retriever.py` — keyword-overlap + tag-score retrieval (top-K default 3,
  `min_score` floor). Returns empty when nothing is relevant → safe fallback.
- `rag.py` — retriever abstraction and wiring (default keyword retriever;
  vector retriever scaffold present for the Day-30 embedding experiment).
- Dependency of the RAG step: only `data/saving_tips.md` (committed, safe).

## 5. Validation and error behavior (chatbot-relevant)

| Layer | Behavior |
|---|---|
| Schema validation (Pydantic) | Empty/oversized `question` → 422; malformed `reference_date` → 422 with explicit detail |
| Intent/entity resolution | Unknown period/category → clarification response (no guess) |
| Backend computation | Financial figures are computed from CSV data only; never from the LLM |
| Response validation | Guards: empty response, ungrounded numbers, over-length, out-of-scope → `validation` field + notes |
| LLM fallback | Any LLM failure/timeout (30 s) returns the deterministic answer; `llm_used: false` |
| Retrieval fallback | Below threshold → "could not find" message instead of fabricated tips |

## 6. Integration blockers / dependencies

1. **GitHub push still blocked (403)** on 2026-08-21 — branch/PR cannot be
   created remotely until the Team Leads add the collaborator account. All
   work is committed locally.
2. **AI service boundaries** — `src/integration/` is the agreed shared layer;
   no secrets/env-specific config are hard-coded there.
3. **Retrieval quality** — keyword+tag baseline; embeddings/rerank planned for
   Day-30 experiments (see `research/rag-approach.md`).
4. **Real user data** — integration with the HisabDo production backend
   (real transaction schema) is pending approval; synthetic data used today.
5. **Budgets dataset** — remaining-budget use cases need a budget dataset
   that does not exist yet.

## 7. Evidence

- Code: `src/integration/app.py`, `src/integration/schemas.py`
- API traces: `docs/evidence/terminal-and-api-output.txt`
- Tests: `tests/test_api.py` (health, chat monthly, saving tip, intents,
  invalid reference date, shared-state isolation) — all pass (63/63 total).