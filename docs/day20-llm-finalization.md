# Day 20 — Finalize LLM/API Request-Response Validation, Error Handling & Fallback

**Intern:** Muhammad Hamza Nawaz
**Subtask:** Finalize LLM/API request-response validation, error handling and fallback behavior (continuing Day 15–19)
**Branch:** `feature/muhammad-hamza-nawaz-llm-finalize-day-20`
**Base:** `feature/muhammad-hamza-nawaz-llm-readiness-day-19`

---

## 1. Status

No new code or design changes since Day 19. The three open items that would justify a real
"finalization" have not moved:

- Asim Javed's model/API provider research — still no branch/PR in the repo as of Day 20.
- The `prompts.py` and `llm.py` overlap with Ahmed Ali Ghori's chatbot work — still present in
  his Day 20 branch (`ahmedali-ghori-chatbot-poc-finalize-day-20`), still awaiting a Team Lead
  decision. Flagged Day 17–19, unresolved.
- Niha's `src/integration/` service layer — still scaffold-only, nothing to integrate against.

Finalizing under these conditions means: confirm the existing implementation is complete and
correct on its own terms, and record clearly what is still blocked rather than mark anything
"done" that isn't.

## 2. Request Flow (final)

Unchanged from Day 18/19: `validate_user_input` → `_call_llm_api` (retry once on failure) →
`validate_llm_response` → return, or `get_fallback_response()` on exhausted failure. See
`docs/day18-llm-integration-flow.md` and `docs/day19-llm-production-readiness.md` for full
detail — not repeated here to avoid drift between documents.

## 3. Input Validation (final)

`validate_user_input()` — type check, non-empty after strip, ≤1000 chars. Unchanged, no gaps
identified since Day 15.

## 4. Response Validation (final)

`validate_llm_response()` — empty-response rejection, system-prompt-leak detection. Unchanged.

## 5. Error Handling (final)

Timeout, connection failure, API error, empty content, and failed response validation all
retry once then fall back, per Day 18/19 documentation. Missing API key still fails loud at
construction rather than falling back — documented, not yet confirmed by Team Lead as intended
final behavior (see Day 19, Section 9).

## 6. Fallback Behavior (final)

Single static `FALLBACK_MESSAGE`, uniform across failure types, reason logged server-side only.
Unchanged since Day 15.

## 7. Production-Readiness Limitations (final)

Carried forward from Day 19 without change, since nothing has resolved them:

- No data grounding — request/response mechanics are proven; answer correctness for
  data-dependent categories (expense totals, budgets, transactions, comparisons, trends) is
  not, and can't be until a retrieval layer is merged.
- No live-provider validation — mocked tests only, pending Asim's research and a real API key.
- No rate-limit-specific handling.
- No multi-turn/conversation-history support.
- Two unresolved overlaps in `src/financial_assistant/` (`prompts.py`, `llm.py`) with Ahmed's
  PR #18, now present across three of his day-branches (18, 19, 20) without a Team Lead
  decision — escalation risk is timing, not content: whichever PR merges first effectively
  decides the architecture for both, by default rather than by review.

## 8. Remaining Dependencies

- Provider decision (Asim).
- Retrieval/RAG layer merge (Ahmed / integration).
- Team Lead resolution on `prompts.py` / `llm.py` overlap.
- Niha's service layer build-out, to actually consume this module's request/response contract.

None of these are within this subtask's scope to resolve — they are cross-team dependencies,
recorded here as the definition of "not yet production-ready" rather than implied to be this
module's own shortcomings.

## 9. Evidence

- Branch: `feature/muhammad-hamza-nawaz-llm-finalize-day-20`
- This document
- Implementation: `src/financial_assistant/llm_service.py` (Day 15/16, unchanged through Day 20)
- Tests: `tests/test_llm_service.py` (15 passed), `tests/test_use_cases_day17.py` (22 passed, 4 skipped-with-reason)
- Prior docs: `docs/day18-llm-integration-flow.md`, `docs/day19-llm-production-readiness.md`