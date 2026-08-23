# Day 21 — Capstone Integration of the Chatbot / RAG POC

**Status date:** 2026-08-23
**Branch:** `feature/ahmedali-ghori-capstone-chatbot-integration-day-21`
**Base branch:** `main`
**Goal:** move the finalized POC (Day 20) toward capstone integration where
technically possible: connect it to the application/service layer, verify the
response flow end to end, and record what still depends on other teams.

---

## 1. What was integrated

| Piece | File | Purpose |
|---|---|---|
| Application-facing service adapter | `src/integration/service.py` | One stable entry point (`AssistantService`) between the HisabDo app/backend and the assistant pipeline |
| Versioned app-facing endpoints | `src/integration/app.py` | `GET /v1/assistant/health`, `POST /v1/assistant/query` |
| App-layer response models | `src/integration/schemas.py` | `AssistantQueryResponse` (adds `status`, `latency_ms`), `ServiceHealthResponse` (adds `service`, `version`, `data_source`) |
| Integration tests | `tests/test_integration_service.py` | Adapter + HTTP flow + regression guards |
| Verification script | `scripts/run_capstone_verification.py` | End-to-end evidence; writes sample IO |

Call chain (verified):

```text
HisabDo App / Backend
  -> POST /v1/assistant/query            (app.py)
       -> AssistantService.ask()          (service.py)
            input validation (question, reference_date)
            per-request FinancialAssistant (engine.py)
              intent -> facts -> RAG retrieval -> grounded response -> validation
       -> AssistantQueryResponse {status, intent, response, facts,
                                  retrieved[], validation, latency_ms}
  <- plain JSON consumed by the application
```

## 2. Data-source connection (backend hand-over path)

`AssistantService(transactions_source=...)` accepts three sources so the
production backend can plug in without touching engine code:

| Source value | Meaning | `data_source` label |
|---|---|---|
| `None` (default) | bundled `data/sample_transactions.csv` | `default_csv` |
| CSV file path | backend-provided export file | `csv:<filename>` |
| list of dicts | records served by the HisabDo backend (`{date, category, description, amount}`) | `injected_records` |

Malformed injected records raise a precise `ServiceInputError` (mapped to
HTTP 422 by the route) instead of leaking an internal traceback.

## 3. Verified response flow (evidence, not estimates)

Verified on 2026-08-23 (Python 3.14.5 venv):

| Check | Result |
|---|---|
| Full unit/API suite | **84/84 pass** (`python -m unittest discover -s tests -t .`) — 63 baseline + 21 new integration tests |
| Lint (`pyflakes` over `src tests scripts`) | **clean** (exit 0) |
| `scripts/run_capstone_verification.py` | both scenarios pass; every query returns `status: ok`, `validation: pass`, latency recorded; **empty stderr** |
| Regression guard | legacy POC routes `GET /health`, `POST /chat`, `POST /intents` unchanged; their original tests still pass |

Scenarios exercised by the script:

- **A — in-process adapter with injected backend records**: a simulated
  HisabDo payload (4 records, July + August 2026) is passed directly to
  `AssistantService`; monthly/last-month totals, highest category, summary,
  RAG saving tips and the out-of-scope fallback are asserted by tests and
  printed as terminal evidence.
- **B — HTTP flow**: the same queries go through
  `GET /v1/assistant/health` and `POST /v1/assistant/query` via TestClient,
  confirming status codes (200 ok, 422 invalid input) and JSON contracts.

## 4. Endpoint contract

| Endpoint | Method | Request | Success | Errors |
|---|---|---|---|---|
| `/v1/assistant/health` | GET | — | `ServiceHealthResponse` (status, service, version, intents, kb chunks, transactions_loaded, llm_available, data_source) | 500 |
| `/v1/assistant/query` | POST | `{question, reference_date?}` (same schema as POC `/chat`) | `AssistantQueryResponse` = pipeline trace + `status:"ok"` + `latency_ms` | 422 empty/whitespace question, bad `reference_date`, malformed data records |

## 5. Sample inputs / outputs

- Committed file: `docs/samples/capstone-sample-io.json` — request/response
  pairs from both scenarios.
- Regenerate any time:
  `python scripts/run_capstone_verification.py --write-samples docs/samples/capstone-sample-io.json`

Example (HTTP):

```json
// request -> POST /v1/assistant/query
{"question": "How much did I spend this month?", "reference_date": "2026-08-20"}
// response (200)
{"status": "ok", "intent": "MONTHLY_EXPENSE", "period": "2026-08",
 "response": "Your total spending for August 2026 was PKR 57.00 across 1 transactions.",
 "validation": "pass", "latency_ms": 0.6}
```

## 6. Remaining dependency (recorded blocker)

1. **Production HisabDo transaction schema approval** — the adapter already
   accepts backend-shaped records (`injected_records`) and CSV paths, but the
   real field names/auth/data feed need Team Lead + backend approval before
   live cutover. Until then the flow runs on synthetic sample data only.
2. Budget dataset still missing -> budget use cases remain out of scope.
3. Optional LLM polish unverified live (no API key in dev env); deterministic
   flow is primary and fully tested.
4. Embedding/vector retrieval and multi-turn memory remain Day-30 roadmap
   items (see `roadmap-day19.md`).

## 7. Files changed

- Added: `src/integration/service.py`, `tests/test_integration_service.py`,
  `scripts/run_capstone_verification.py`, `docs/capstone-integration.md`,
  `docs/samples/capstone-sample-io.json`
- Modified: `src/integration/app.py` (+2 versioned endpoints),
  `src/integration/schemas.py` (+2 response models), `docs/README.md` (index),
  `docs/blockers-and-dependencies.md` (dependency record),
  warning-filter hygiene in test/script entry points for clean output.

