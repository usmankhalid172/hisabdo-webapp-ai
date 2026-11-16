# Department 3 Final Defect Triage Log

**Project:** HisabDo AI Business Assistant  
**Department:** Department 3  
**Triage date:** 16 November 2026  
**Branch:** purnoor-zafar-ai-intern

## 1. Triage summary

The local full regression suite completed with 387 passed, 4 skipped, and 69 warnings. The expanded security/adversarial suite completed with 70 passed. No automated test failures were reported in the recorded runs.

The items below distinguish observed benchmark issues from verification gaps and environment warnings. A verification gap is not automatically a confirmed production defect.

## 2. Defect and follow-up register

| ID | Priority | Area | Finding | Evidence/status | Recommended action |
|---|---|---|---|---|---|
| D3-01 | P2 | Retrieval ranking | EVAL-08 missed expected source `finance_001` in top 3 | Observed in current benchmark; recall@3 66.67% | Inspect source content, lexical/semantic scores, and ranking/fusion behavior for profit-versus-cash-flow queries; add a regression case before changing ranking |
| D3-02 | P2 | Retrieval precision | EVAL-01 to EVAL-06 each returned the correct top-1 source but two additional top-3 sources | Observed; each query Precision@3 33.33% | Review chunk relevance, score separation, and retrieval threshold; avoid tuning that harms recall or no-match behavior |
| D3-03 | P1 verification gap | Financial backend and privacy | Production financial-data correctness and live session isolation are not established by local tests; existing documentation describes demo financial figures | Not verified in production | Validate with authorized production-like accounts and explicit cross-user isolation tests before production sign-off |
| D3-04 | P2 verification gap | Multi-turn UX | History forwarding and integration workflow tests passed, but a complete multi-turn financial transaction dialogue was not independently exercised | Partially validated | Add an end-to-end scenario: create an expense, ask a follow-up about it, correct it, and verify the final response uses the right authorized data |
| D3-05 | P2 verification gap | Citations and grounding | Grounded prompt rules and targeted tests passed; dedicated citation rendering and automatic source-conflict detection were not independently verified | Partially validated; some source URLs are null and some source verification metadata is pending | Add response-level tests for source ID/title/link rendering, missing URLs, conflicting sources, and unsupported claims |
| D3-06 | P2 verification gap | Performance | Local retrieval latency was measured, but full LLM/API/backend end-to-end response latency and provider usage costs were not measured | Retrieval-only timings available; end-to-end metrics unavailable | Instrument request start/end, retrieval duration, provider duration, backend duration, total response duration, and token/cost metadata without logging secrets or private financial content |
| D3-07 | P2 compatibility risk | ML model persistence | Persisted scikit-learn artifacts report version 1.7.2 while current environment is 1.5.2 | Compatibility warnings in full test run; tests still passed | Align runtime and artifact versions or rebuild artifacts in the approved environment; validate predictions before release |
| D3-08 | P3 maintenance | Test configuration | pytest-asyncio reports that the default fixture loop scope is not explicitly configured | Warning observed | Set an explicit fixture loop scope after checking test fixture requirements |
| D3-09 | P3 maintenance | Framework deprecation | Starlette/AnyIO reports a BlockingPortal deprecation warning | Warning observed | Review dependency compatibility and migrate affected usage before the deprecated behavior is removed |

## 3. Passed controls — no open failure observed in this run

- Day 1 security suite rerun: 62 passed.
- Expanded security/adversarial suite: 70 passed.
- Cross-user boundary and third-party financial-data policy probes passed in the executed test set.
- Targeted chatbot, retrieval, hybrid retrieval, and grounded-generation tests: 28 passed.
- Integration workflow tests: 24 passed.
- Full test suite: 387 passed, 4 skipped.
- Golden supported-query top-1: 8/8.
- Unsupported/ambiguous no-match checks: 2/2.

These are local automated test outcomes, not a substitute for production environment verification.

## 4. Release-readiness assessment

**Local regression:** Passed.

**Security regression:** Passed in the tested local environment.

**Retrieval quality:** Top-1 and recall results are strong on the current small golden set; Precision@3 and EVAL-08 ranking require follow-up.

**Production readiness:** Not fully established. Production backend/session isolation, full multi-turn financial flows, end-to-end latency, and response-level citation behavior remain verification gaps.

## 5. Closure criteria

The triage items should be closed only when their corresponding evidence is available:

1. EVAL-08 retrieves all expected sources in the approved top-k benchmark, or the expected set is reviewed and corrected with documented justification.
2. Precision@3 is reviewed against a representative relevance-labelled dataset.
3. Production-like financial backend tests demonstrate account isolation and correct ownership enforcement.
4. Multi-turn financial dialogue tests verify state continuity and authorization.
5. Response-level citation tests verify accurate source attribution and safe handling of missing/conflicting metadata.
6. End-to-end latency and provider usage measurements are collected with privacy-safe telemetry.
7. The scikit-learn artifact/runtime version mismatch is resolved and prediction behavior is revalidated.

**Final status:** No automated test failures were observed in this validation run. The above items remain open follow-ups or verification gaps; they are not represented as completed fixes.
