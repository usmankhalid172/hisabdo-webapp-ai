# Careers & Job Openings — E2E Pipeline Verification

**Date:** 30 October 2026  
**Owner:** Hassan Hussain  
**Repository branch:** `feature/hassan-hussain-core-services-formatting`  
**Scope:** Multi-turn dialogue handling, recruitment FAQs, citation/source links, and safe fallback behavior.

## Executive summary

The Careers code path was reviewed and the focused Careers grounding suite passed **13/13 checks** in an isolated run. The checks cover Careers routing and source filtering, numbered evidence passed to the response provider, citation-number validation, multi-turn history propagation, application-status fallback, conflict handling, and widget source-link rendering logic.

A concrete edge case was found during retrieval inspection: “Can you check whether my application was received?” retrieved a public FAQ about application review time. That FAQ cannot establish an individual applicant's receipt/status. The handler now detects personal application-status requests and returns the verified Careers-page fallback before retrieval or model generation. A focused regression test confirms the provider is not called for that request.

This is **not a claim of full production/browser E2E sign-off**. The environment's normal test setup lacks `slowapi` and `pydantic_settings`; the focused suite was run with temporary local compatibility shims and without loading the application's full root test configuration. An in-process HTTP TestClient smoke attempt did not complete in the installed FastAPI/Starlette/httpx combination. Live Groq behavior and an actual browser click on a citation link were not exercised.

## Pipeline and observable behavior

1. The widget creates a conversation ID and retains recent user/assistant turns; it sends the latest message, conversation ID, and up to the last 10 history turns to `POST /api/v1/xictek/chat`.
2. The Careers handler identifies recruitment messages and restricts evidence to XICTEK URLs under `/careers` on `xicteksystems.com`, excluding similarly named HisabDo pages.
3. Retrieved chunks are serialized as numbered source blocks with title, URL, and text. The response returns a source list in the same order, so citation `[1]` maps to `sources[0]`.
4. The widget renders the response's sources as numbered, clickable links opening a new tab.
5. Careers responses are rejected to a deterministic linked fallback when no evidence exists or the model produces missing/out-of-range citations. Private applicant-status queries now bypass retrieval and generation because public website content cannot verify an individual record.

The endpoint is protected by `X-Internal-Token`. The widget code sends this header; browser testing against a real deployment requires an approved test setup and must not expose a production service secret in public client-side code.

## Verification sheet

| ID | Scenario | Expected result | Observed result | Status |
|---|---|---|---|---|
| C-01 | Careers FAQ: “What internship roles are listed?” | Retrieve only XICTEK Careers evidence; include a numbered citation and matching source entry. | Service tests verified XICTEK host/path filtering and source-number context mapping. A direct local-index query returned Careers/internship chunks (top score 0.208). | PASS — retrieval/service-level; not live generated answer |
| C-02 | Follow-up: “What are the requirements for those internship roles?” with prior turns | Keep the same conversation ID; pass prior turns to the provider; return current retrieved source references. | Multi-turn service test verified the same ID, exact history propagation, numbered source context, and Careers source entry. Local-index retrieval returned internship FAQ passages, including duration/benefits text; this does not prove the requirement answer itself is present. | PASS — history path; answer entailment needs live-model review |
| C-03 | Career source separation | Never use HisabDo Careers or unrelated XICTEK sections as Careers evidence. | Vector-store test verifies the Careers path + XICTEK host filter and excludes HisabDo Careers and Services chunks. | PASS |
| C-04 | Dynamic citations and links | Citation numbers map to response sources; widget displays numbered links using each source URL. | Tests verify numbered citation/source ordering and widget code creates numbered anchors from API sources. | PASS — code-level; actual browser click not run |
| C-05 | Unsupported job-application instructions: “How do I apply for a job?” | If no supporting chunk is retrieved, do not invent steps; return the uncertainty fallback with the official Careers page link. | Local index returned no matches for this query. Existing no-evidence test confirms model generation is skipped and fallback source URL is returned. | PASS — no-evidence fallback |
| C-06 | Personal status: “Can you check whether my application was received?” | Do not infer receipt/status from public FAQs; return a concise linked fallback and skip generation. | Local index returned a nearby 3–5 business-day review FAQ, which is not proof of an individual status. New handler guard plus regression test verifies fallback even when such a nearby match exists; provider is not called. | PASS — deterministic guard |
| C-07 | Provider reply without citation or with an out-of-range citation number | Replace unsupported reply with the safe linked fallback. | Focused tests cover uncited and invalid citation numbers. | PASS |
| C-08 | Conflicting source passages | Report the conflict with citations to both sources; do not select a version without evidence. | Prompt policy and service test cover two numbered conflicting sources. No separate fact-level contradiction detector exists. | PASS — instruction/test behavior; not proof of live-model reliability |
| C-09 | Normal full-suite/API/browser execution | Run with project-pinned dependencies; verify HTTP auth, widget network call, and link click in a browser. | Blocked in this environment: `slowapi` and `pydantic_settings` are missing from the available Python environment; the isolated API TestClient smoke attempt stalled under the installed client stack. | NOT VERIFIED |

## Tested fallback response

The exact deterministic response returned by the handler is:

> I couldn't verify that recruitment detail from the available Careers content. Please check the official XICTEK Careers page for current information [1].

Fallback source:

- [1] [Official XICTEK Careers page](https://xicteksystems.com/careers)

This response is appropriate for unavailable application instructions, private application status, and unverified recruitment facts. It makes no claim that an application was received or that a vacancy is currently open.

## Changes made for this task

- Extended Careers-intent phrases to recognize application-received/status language.
- Added `is_personal_application_status_query` and a deterministic fallback before retrieval/model generation for individual application-status requests.
- Added regression checks for multi-turn history propagation, the individual-status fallback despite a nearby public FAQ match, and widget citation-link rendering.

## Test record and limitations

- Command used for focused tests (temporary local shims supplied for unavailable settings imports):

  ```powershell
  $env:PYTHONPATH = "<workspace>\\_reviewtmp\\compat"
  python -m pytest --confcutdir=tests/xictek_website_assistant tests/xictek_website_assistant/test_careers_grounding.py -q
  ```

- Result: **13 passed**.
- Direct local-index inspection used the checked-in Careers index and observed a scikit-learn pickle compatibility warning (index written with 1.5.2, inspected with 1.7.2). Treat those retrieval scores as diagnostic only until the project-pinned environment is restored and the index rebuilt or verified.
- No live LLM/Groq call, hosted endpoint, browser widget session, or actual clickable-link interaction was tested.
- Citation-number validation checks that a citation points to a returned source; it does not prove the source entails every generated claim. Human-reviewed answer/citation entailment remains required.

## Recommended acceptance follow-up

1. Restore the repository's pinned dependencies and run the documented focused command plus the full XICTEK test suite.
2. Run the endpoint with the approved internal token and configured test provider; validate C-01 through C-08 over actual HTTP.
3. In a non-production browser test environment, verify the widget sends conversation history and that each numbered source opens the expected Careers URL.
4. Review current Careers page contents and source freshness before asserting that any role is open or that a recruitment detail is current.
5. Test with a live model using reviewed expected answers and citation-entailment scoring before calling the flow production-ready.
