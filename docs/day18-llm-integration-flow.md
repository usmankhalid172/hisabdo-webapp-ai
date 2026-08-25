# Day 18 — LLM Request/Response Integration Flow

**Intern:** Muhammad Hamza Nawaz
**Subtask:** Define and validate the LLM request/response integration flow, validation, timeouts, errors and fallback behavior
**Branch:** `feature/muhammad-hamza-nawaz-llm-integration-day-18`
**Base:** `feature/muhammad-hamza-nawaz-llm-validation-use-cases-day-17`
**Module under documentation:** `src/financial_assistant/llm_service.py` (Day 15/16), validated against realistic use cases in Day 17

---

## 1. Purpose

Day 15–17 built and validated the LLM request/response layer in isolation. Day 18 defines
the **integration contract** — what a caller (the FastAPI service layer / Niha's
`src/integration/`) sends in and gets back — plus dependencies and blockers relevant to wiring
this module into the rest of the app. No behavioral changes to `llm_service.py` were needed;
this formalizes what already exists and fills in what Day 15–17 didn't need to specify yet.

## 2. Request Structure

The public entry point is `get_financial_assistant_response()`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `user_question` | `str` | Yes | Raw user text. Validated by `validate_user_input()`: must be a string, non-empty after `.strip()`, ≤ 1000 chars (`LLMConfig.max_input_chars`). |
| `config` | `LLMConfig` | No (has default) | `model`, `timeout_seconds` (15.0 default), `max_retries` (1 default), input length bounds. Caller can override per-request if needed. |
| `client` | `OpenAI` instance | No | Only used for test injection (mocking). Integration callers should omit this — the module creates its own client via `_get_client()`, which reads `FINANCIAL_ASSISTANT_LLM_API_KEY` from the environment. |

**What the integration layer does NOT need to send:** system prompt (owned by `prompts.py`,
injected internally), retrieved financial data / RAG context (not yet consumed by this module —
see Section 6), conversation history (not currently supported — single-turn only).

## 3. Response Structure

- **Success:** returns a plain `str` — the validated assistant reply, ready to show the user directly.
- **Failure (any kind):** never raises to the caller for expected failure modes (see Section 4)
  — returns `FALLBACK_MESSAGE`, also a plain `str`, safe to display as-is.
- **Exception raised (does propagate):** only `InvalidInputError`, and only for malformed input
  (empty, non-string, over length). This is treated as a client-side/caller bug, not a service
  failure, so the integration layer should validate/sanitize input before calling, or catch this
  specifically and return a 4xx-style response rather than a generic error.

## 4. Timeout, Failure, and Invalid-Response Handling

All of the following are already implemented and covered by the Day 15/17 test suites
(`tests/test_llm_service.py`, `tests/test_use_cases_day17.py`):

| Scenario | Handling |
|---|---|
| API timeout | `APITimeoutError` caught in `_call_llm_api`, wrapped as `LLMRequestError`, retried once (`max_retries=1`), then falls back. |
| Connection failure | `APIConnectionError` → same retry-then-fallback path. |
| API error response | `APIError` → same retry-then-fallback path. |
| Empty/no-content response | Raised as `LLMRequestError` internally, same retry-then-fallback path. |
| Response leaks system prompt / internal instructions | Caught by `validate_llm_response()` pattern check, same retry-then-fallback path. |
| Missing API key | Raised immediately as `LLMConfigurationError` at client construction — **not** currently caught by the retry/fallback loop, so this surfaces as an exception rather than the fallback message. Flagged in Section 7 as something the integration layer needs to handle explicitly (e.g. fail startup/health-check rather than fail per-request). |

Retry policy: exactly one retry, one-second backoff, then fallback — chosen to bound worst-case
latency (`timeout_seconds` × 2 + 1s ≈ 31s ceiling) rather than retry indefinitely.

## 5. Fallback Behavior

Single static fallback message (`FALLBACK_MESSAGE`) returned for all failure types. The specific
failure reason is logged server-side (`logger.warning`) but intentionally never included in the
user-facing message, to avoid leaking internal error detail. This is uniform across every failure
mode — the integration layer does not need per-error-type UI handling for this module's failures.

## 6. Cost, Rate-Limit, and Provider Dependencies

- **Provider assumption still open:** built against an OpenAI-compatible chat completions API
  (`_call_llm_api` isolates this call so swapping providers only touches one function). Still
  pending Asim's model/API research, which has no branch/PR as of Day 18.
- **No rate-limit handling implemented.** `APIError` is caught generically; a 429 (rate limit)
  response is currently treated the same as any other API error (retry once, then fallback) —
  there's no backoff-and-retry tuned specifically for rate limits, and no request queuing/throttling
  at this layer. If usage volume becomes a concern, this needs its own handling before production.
- **Cost control:** the only current cost guard is the 1000-character input cap. There's no
  per-user/per-session request limit — that would need to live in the integration layer (Niha's
  service layer), since this module has no concept of users or sessions.
- **No live API key available in this environment**, so timeout/rate-limit/cost behavior is
  validated against mocks only, not a real provider — recorded as a blocker (Section 7), not
  silently assumed correct.

## 7. Coordination Notes

- **Niha's service layer (`src/integration/`):** currently scaffold only — a README describing
  the folder's intended contents, no code yet. Nothing to integrate against as of Day 18. This
  document is written so that when that layer is built, the contract in Sections 2–3 is ready to
  code against without needing to re-derive it from `llm_service.py` directly.
- **Ahmed Ali Ghori's chatbot integration (PR #18):** his branch now includes its own
  `src/financial_assistant/llm.py` — a second, independently-designed LLM call/fallback
  implementation (deterministic-response-first, LLM as optional polish), alongside the existing
  `prompts.py` divergence flagged after Day 17. Flagging briefly here as a known overlap for
  Team Lead resolution before merge; not re-litigated in this document since it's already
  reported separately.

## 8. Blocked / Untested Areas

- Real-provider timeout/rate-limit/error behavior — mocked only, no live key.
- `LLMConfigurationError` (missing API key) is not exercised through the retry/fallback path —
  worth a Day 19/20 decision on whether that should also degrade to fallback or intentionally
  fail loud (currently: fails loud, by design, since a missing key is a deployment misconfiguration
  rather than a transient runtime failure).
- Integration against Niha's actual service layer — no code exists yet to integrate against.
- Multi-turn conversation support — out of scope for this module as currently designed; single
  question in, single answer out.

## 9. Evidence

- Branch: `feature/muhammad-hamza-nawaz-llm-integration-day-18`
- This document
- Underlying implementation: `src/financial_assistant/llm_service.py` (Day 15/16, unchanged)
- Test evidence: `tests/test_llm_service.py` (15 passed), `tests/test_use_cases_day17.py` (22 passed, 4 skipped-with-reason)