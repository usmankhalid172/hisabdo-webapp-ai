# Day 19 — LLM/API Validation, Error Handling, Fallback & Production-Readiness

**Intern:** Muhammad Hamza Nawaz
**Subtask:** Document LLM/API validation, error handling, fallback behavior and current production-readiness status
**Branch:** `feature/muhammad-hamza-nawaz-llm-readiness-day-19`
**Base:** `feature/muhammad-hamza-nawaz-llm-integration-day-18`
**Consolidates:** Day 15 (`llm_service.py` implementation), Day 16 (provider assumption), Day 17
(realistic use-case validation), Day 18 (integration contract) — this document is the single
reference point for all of it, not new work.

---

## 1. Current LLM/API Request Flow

```
caller
  -> validate_user_input(question)         [rejects empty / non-string / >1000 chars]
  -> _call_llm_api(question)                [OpenAI-compatible chat completions call]
       -> on success: validate_llm_response(raw_text)
       -> on timeout/connection/API error: retry once (1s backoff)
       -> on repeat failure: get_fallback_response()
  -> returns: assistant text (success) or FALLBACK_MESSAGE (failure)
```

Entry point: `get_financial_assistant_response()` in `src/financial_assistant/llm_service.py`.
Single question in, single answer out — no conversation history, no retrieved financial data
injected (both explicitly out of this module's scope; see Day 15 module docstring).

## 2. Input Validation

`validate_user_input()`:
- Must be a `str` (rejects non-string types).
- Must be non-empty after `.strip()`.
- Must be ≤ 1000 characters (`LLMConfig.max_input_chars`, cost/abuse control).
- Raises `InvalidInputError` on any failure — propagates to the caller rather than being
  swallowed into a generic fallback, since bad input is a caller-side problem, not a service
  failure.

## 3. Response Validation

`validate_llm_response()`:
- Rejects empty/whitespace-only responses.
- Rejects responses containing system-prompt leak indicators (guards against prompt injection
  surfacing internal instructions — Rameesha's TC-19 scenario).
- Passing responses are `.strip()`'d and returned as-is; this layer does not otherwise inspect
  content (no grounding/fact-check — see Section 8, Limitations).

## 4. Error Handling

| Failure | Behavior |
|---|---|
| `APITimeoutError` | Wrapped as `LLMRequestError`, retried once, then fallback. |
| `APIConnectionError` | Same. |
| `APIError` (incl. rate limits, generic API failures) | Same — no rate-limit-specific handling yet (see Section 6). |
| Empty response content | Wrapped as `LLMRequestError`, same retry-then-fallback path. |
| Response fails validation (leak indicators) | `InvalidResponseError`, same retry-then-fallback path. |
| Missing API key | `LLMConfigurationError` raised immediately at client construction — does **not** go through retry/fallback; this is treated as a deployment misconfiguration, not a runtime failure, so it fails loud rather than silently degrading. |
| Malformed user input | `InvalidInputError`, raised to caller, never retried or masked. |

## 5. Timeout / Failure Behavior

- Per-call timeout: 15 seconds (`LLMConfig.timeout_seconds`).
- Retry policy: exactly one retry with a 1-second backoff, then fallback — bounds worst-case
  latency to roughly 31 seconds rather than retrying indefinitely.
- All retryable failures funnel through the same path regardless of cause (timeout, connection,
  API error, bad response) — uniform behavior, no special-casing per failure type.

## 6. Fallback Approach

- One static, user-safe message (`FALLBACK_MESSAGE`) returned for every retryable failure type.
- The actual failure reason is logged server-side (`logger.warning`) for debugging, never shown
  to the user — avoids leaking internal error/stack detail.
- Fallback is a plain string, same shape as a success response, so callers don't need
  failure-specific handling on their end.

## 7. API/Model Dependencies

- Built against an **OpenAI-compatible** chat completions API — an explicit, flagged assumption
  pending Asim Javed's model/API research, which as of Day 19 still has no branch or PR in the repo.
- Provider call is isolated in one function (`_call_llm_api`), so switching providers is a
  contained change, not a rewrite.
- No live API key available in this development environment — all validation (Days 15, 17, 18)
  has been against a mocked client. Real-provider timeout/rate-limit/latency behavior is
  unverified.

## 8. Privacy / Security Considerations

- API key is read from an environment variable (`FINANCIAL_ASSISTANT_LLM_API_KEY`), never
  hardcoded — consistent with repo-wide `.gitignore` exclusion of `.env` and Security-check
  guidance in the PR template.
- No user financial data is currently passed into this module at all (no RAG/retrieval wired
  in yet), so there is currently nothing sensitive in the request payload beyond the raw
  question text itself. This will change once retrieval is integrated (Ahmed's PR #18 /
  eventual `src/integration` work) — at that point, prompt construction needs review for what
  financial data gets sent to a third-party API.
- Fallback messages and logs deliberately exclude raw exception detail from user-facing output,
  reducing risk of leaking internal system information.
- System-prompt leak detection in response validation is a basic first line of defense against
  prompt injection, not a comprehensive one — no broader injection-resistance testing has been
  done at this layer.

## 9. Current Limitations

- No data grounding: as validated in Day 17, most realistic financial questions (expense
  totals, budgets, transaction lookups, comparisons, trends) cannot be answered correctly by
  this module alone, because it has no access to the user's actual financial data. Only the
  request/response/error-handling mechanics are proven, not answer correctness for those
  categories.
- No conversation history / multi-turn support.
- No rate-limit-specific handling — a 429 is currently treated like any other API error.
- No per-user/per-session request throttling — would need to live in the integration/service
  layer, not this module.
- Missing-API-key failure mode is not covered by the fallback path (fails loud instead) — a
  deliberate choice, documented but not yet confirmed with Team Lead as the intended behavior.
- Two known unresolved overlaps in `src/financial_assistant/`, flagged to Team Lead: a
  `prompts.py` divergence (static SYSTEM_PROMPT vs. Ahmed's per-intent grounded prompts) and an
  independent `llm.py` in Ahmed's PR #18 implementing the same request/fallback responsibility
  differently. Neither is resolved as of Day 19 — Team Lead has not yet responded.

## 10. Remaining Work Toward Integration Readiness

- Resolve the `prompts.py` / `llm.py` overlap with Ahmed's PR #18 — architectural decision
  needed from Team Lead, not something to resolve unilaterally.
- Finalize LLM provider once Asim's research/comparison is available.
- Wire in real financial data (from retrieval/RAG layer, once built) so grounded categories
  (5.1, 5.2 from Day 17) can be verified for correctness, not just mechanics.
- Add rate-limit-specific handling if usage volume warrants it.
- Validate real-provider behavior once a live API key is available.
- Decide and document intended behavior for missing-API-key at request time vs. startup/health-check time.

## 11. Evidence

- Branch: `feature/muhammad-hamza-nawaz-llm-readiness-day-19`
- This document
- Implementation: `src/financial_assistant/llm_service.py` (Day 15/16)
- Tests: `tests/test_llm_service.py` (15 passed), `tests/test_use_cases_day17.py` (22 passed, 4 skipped-with-reason)
- Integration contract: `docs/day18-llm-integration-flow.md`