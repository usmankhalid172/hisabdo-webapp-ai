# Day 21 — Capstone Integration of the Chatbot / RAG POC (Superseded)

**Status date:** 2026-08-23 (supersession recorded when PR #34 was converged onto `main`)
**Branch:** `feature/ahmedali-ghori-capstone-chatbot-integration-day-21`

## Summary

The Day-21 deliverable connected the Chatbot/RAG POC to the application/service
layer through an application-facing `AssistantService` adapter and versioned
endpoints (`GET /v1/assistant/health`, `POST /v1/assistant/query`), verified the
response flow end to end (84/84 tests at the time), and published sample
inputs/outputs.

## Supersession

The repository's integration architecture has since been reworked on `main`
(Tasks 26-27, plus the LLM-readiness work):

| Day-21 concept | Current implementation on `main` |
|---|---|
| `AssistantService` app-facing adapter | `src/financial_assistant/service.py` (`handle_chat`) |
| Backend data seam / injected records | `src/integration/backend_client.py` (`BackendClient` ABC, `MockBackendClient`) |
| FastAPI surface (`/v1/assistant/*`) | `src/main.py` app + `src/financial_assistant/router.py` |
| Deterministic offline engine (`engine.py`, `rag.py`) | LLM-provider pipeline + `src/financial_assistant/rag/` package |
| Boundary rule: figures never from RAG | Restated in `service.py` (own-financial-data -> backend client, never RAG) |

Per the QA review of PR #34, the remaining blocking issue was mergeability.
This branch was merged with the latest `main` and the superseded Day-21 code
files were removed so the tree converges on the current architecture. The
Day-21 intent — a verified application/service-layer connection with recorded
dependencies — is carried forward by the files listed above.

## Remaining dependency (unchanged)

The production HisabDo transaction data contract is still pending (Day 15 §10
blocker). `MockBackendClient` is the clearly-labelled stand-in; swap in the real
HTTP client once the schema is approved.

## Evidence retained for the record

- QA review of PR #34: full suite passing on the Day-21 snapshot (87/87 as run
  by the reviewer), compilation clean, no conflict markers; only mergeability
  blocked approval.
- Sample request/response pairs generated at the time remain in the PR history
  (`docs/samples/capstone-sample-io.json`, removed here as it referenced the
  superseded endpoints).
