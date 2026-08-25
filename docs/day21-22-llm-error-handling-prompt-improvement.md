# Day 21-22 — LLM Error Handling & Prompt Improvement

**Intern:** Muhammad Hamza Nawaz
**Subtask:** Improve prompt handling and LLM/API error behavior for the integration-ready AI flow
**Focus:** invalid inputs, API failures, inconsistent responses, graceful fallback
**Branch:** `feature/muhammad-hamza-nawaz-llm-error-handling-prompt-improvement-day-21-22`
**Base:** `feature/muhammad-hamza-nawaz-llm-finalize-day-20`

---

## 1. What Changed

### `prompts.py` (prompt improvement)
Added a "Response consistency guidelines" section to `SYSTEM_PROMPT`, directly targeting the
inconsistent-response variance Day 17's use-case validation surfaced (models restating the
question, opening with filler like "Great question!", asking multiple clarifying questions at
once, or replying with near-empty content). No existing instructions were removed — this is
additive, so Rameesha's original Day 15 prompt content is unchanged.

### `llm_service.py` (error-handling improvement)
Two additions, both covering gaps explicitly named in this subtask's focus list:

1. **Rate-limit-specific handling** — previously `RateLimitError` (a 429) was caught by the
   generic `APIError` handler and treated identically to any other API failure. Now raises a
   dedicated `LLMRateLimitError` (subclass of `LLMRequestError`, so anything already catching the
   base class still works) and retries with a longer, configurable backoff
   (`rate_limit_backoff_seconds`, default 3s vs. the standard 1s) before falling back. Closes the
   gap flagged in the Day 19 readiness doc.

2. **Inconsistent-response detection** — `validate_llm_response()` now also rejects:
   - a response that's a bare echo of the user's question (ignoring trailing punctuation),
   - a response containing no alphanumeric content (punctuation/symbols only).

   Both funnel through the existing retry-then-fallback path, so a bad response on attempt 1
   still gets a real chance to succeed on retry rather than immediately failing the request.
   A guardrail test confirms genuinely short-but-valid answers (e.g. `"$85."`) are **not**
   rejected — the checks target degenerate output, not brevity.

## 2. Sample Failure/Recovery Behavior (evidence)

All in `tests/test_day21_22_error_handling.py`:

| Scenario | Behavior |
|---|---|
| Rate limit on attempt 1, succeeds on retry | Recovers, returns the real answer, confirmed 2 API calls made. |
| Rate limit persists through retry budget | Falls back to `FALLBACK_MESSAGE`, no exception, no raw 429 surfaced to the user. |
| Model echoes the question on attempt 1, real answer on retry | Recovers, returns the real answer. |
| Model echoes the question on every attempt | Falls back gracefully. |
| Response is punctuation-only (`"..."`) | Rejected directly by `validate_llm_response`. |
| Short-but-valid response (`"$85."`) | **Not** rejected — confirms the new checks don't over-block legitimate short answers. |

## 3. Test Results

- `tests/test_day21_22_error_handling.py`: 7 passed (new, this cycle)
- `tests/test_llm_service.py`: 15 passed (Day 15, unchanged — confirms no regression)
- `tests/test_use_cases_day17.py`: 22 passed, 4 skipped-with-reason (unchanged — confirms no regression)
- Full suite: **29 passed, 4 skipped, 0 failed**

## 4. Work Still Remaining

- Missing-API-key behavior (fails loud rather than falling back) is still an open design
  question from Day 19 — not addressed this cycle, out of this subtask's specific focus list.
- Prompt consistency guidelines are untested against a live model (still no API key available)
  — validated only insofar as the retry/fallback mechanics around inconsistent responses work
  correctly with mocked data.

## 5. Blockers

- Still no live LLM API key — all evidence above is against a mocked client, consistent with
  every prior day's evidence.
- Still no branch/PR from Asim Javed (provider research) as of Day 21-22.
- `prompts.py`/`llm.py` overlap with Ahmed Ali Ghori's chatbot work remains unresolved — this
  change modifies the same `prompts.py` file that already diverges from his branch, so the merge
  conflict surface has grown slightly, not shrunk. Flagged previously (Day 17-20); not re-raised
  in detail here per prior decision to flag once and not dwell on it repeatedly.

## 6. Evidence

- Branch: `feature/muhammad-hamza-nawaz-llm-error-handling-prompt-improvement-day-21-22`
- Modified: `src/financial_assistant/prompts.py`, `src/financial_assistant/llm_service.py`
- New: `tests/test_day21_22_error_handling.py` (7 passed)
- This document