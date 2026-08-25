# Day 17 — Financial Assistant Use-Case Validation

**Intern:** Muhammad Hamza Nawaz
**Subtask:** Apply LLM request/response validation and error handling to realistic AI Assistant use cases
**Branch:** `feature/muhammad-hamza-nawaz-llm-validation-use-cases-day-17`
**Base:** `feature/muhammad-hamza-nawaz-llm-api-day16` (PR #9 and PR #39 not yet merged into `main`)

---

## 1. Work Completed

- Took Rameesha Zafar's Day 15 question categories (PR #4, sections 5.1–5.8) as the
  realistic use-case set, rather than generic placeholder strings.
- Ran each category through `llm_service.py`'s actual validation → call → response-validation
  → fallback flow (mocked client — see Section 4, Blockers).
- Classified each category as **Working**, **Partially working**, or **Blocked**, with a test
  or an explicit skip-with-reason recorded for each (`tests/test_use_cases_day17.py`).
- Re-confirmed the existing timeout/fallback and input-validation paths (Day 15/16) against
  realistic questions instead of placeholder strings.
- 22 passed, 4 explicitly skipped (documented as blocked, not silently omitted).

## 2. Use-Case Classification

| # | Category (Rameesha PR #4) | Status | Why |
|---|---|---|---|
| 5.1 | Expense summary ("How much did I spend this month?") | **Partially working** | Request/response mechanics work; the answer is not grounded in real transaction data (no retrieval layer wired in yet), so correctness can't be verified at this layer. |
| 5.2 | Category-based ("How much on groceries?") | **Partially working** | Same as above — highest hallucination risk without grounding. |
| 5.3 | Transaction lookup ("What was my most recent expense?") | **Blocked** | No transaction data source available to this module; any mocked "pass" would misrepresent the use case as working. |
| 5.4 | Budget ("How much budget do I have left?") | **Blocked** | No budget data source wired in. |
| 5.5 | Comparison ("Did I spend more this month than last?") | **Blocked** | Requires grounded multi-period data. |
| 5.6 | Trend/insight ("What category do I spend most on?") | **Blocked** | Requires grounded aggregate data. |
| 5.7 | Ambiguous ("How much did I spend?") | **Partially working** | Question passes validation and reaches the model; whether the model actually asks a clarifying question (spec section 3.3) is untestable without a live model/key. |
| 5.8 | Unsupported/out-of-scope ("Write me a Python program.") | **Working** | This layer correctly carries any well-formed input through regardless of topic; scope enforcement is a system-prompt/model-behavior concern, already covered structurally. |
| — | Model unavailable / timeout (any category) | **Working** | Fallback message returned correctly for a realistic question, not just a placeholder (Day 15/16 behavior reconfirmed). |
| — | Empty / overlong input (any category) | **Working** | Rejected before any API call, no wasted request. |

**Summary:** request/response validation and error-handling mechanics are fully working across
all categories. Full end-to-end correctness is currently blocked for 4 of 8 categories (5.3–5.6)
and partial for 2 more (5.1, 5.2, 5.7) — not because of a defect in this module, but because the
data-retrieval/RAG layer these categories depend on isn't wired in yet. That layer is Ahmed Ali
Ghori's PR #18 scope.

## 3. Work Still Remaining

- Once a retrieval/RAG layer is agreed and merged, re-run 5.1–5.6 with real financial-data
  fixtures instead of mocked free-text answers, to actually verify grounding/no-hallucination.
- Once Asim's model/API research lands, re-run the full suite against a live key to confirm
  real API timeout/error behavior matches the mocked assumptions.

## 4. Blockers

- **No live LLM API key** — Asim Javed's model/API research still has no branch/PR as of Day 17
  (confirmed via repo branch list). All tests remain mocked per Team Lead's Day 16 guidance.
- **No retrieval/RAG layer merged** — this is the direct cause of the 4 blocked / 2 partial
  categories above. Not a new blocker, but now backed by category-level test evidence rather
  than a general statement.
- **`prompts.py` collision with PR #18** — Ahmed Ali Ghori's branch
  (`feature/ahmedali-ghori-financial-assistant-use-cases-day-17`) contains a different
  `src/financial_assistant/prompts.py` (grounded, per-intent, RAG-context-injecting) than the
  one this module imports from (static `SYSTEM_PROMPT`, owned by Rameesha's Day 15 PR #4). Both
  branches now have active Day 17 commits on top of this divergence, so the conflict is no
  longer theoretical. Flagging for Team Lead resolution before either PR merges.

## 5. Evidence

- Branch: `feature/muhammad-hamza-nawaz-llm-validation-use-cases-day-17`
- New file: `tests/test_use_cases_day17.py` (22 passed, 4 skipped-with-reason)
- Existing file (reconfirmed): `tests/test_llm_service.py` (15 passed)
- This document