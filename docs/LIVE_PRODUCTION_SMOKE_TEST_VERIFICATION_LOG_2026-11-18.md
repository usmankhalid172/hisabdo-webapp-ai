# Live Production Smoke-Test Verification Log

**Date:** 18 November 2026  
**Branch:** `feature/hassan-hussain-core-services-formatting`  
**Status:** PARTIAL — public health and route discovery verified; authenticated checks blocked

## Verification decision

The API docs link supplied for this project identifies `https://hisabdo-ai-api.hisabdo.app` as the production API origin. A live `GET /api/v1/health` returned HTTP 200 with `status: "ok"`; the smoke script recorded a response latency of **1,373.07 ms** in one sample. The OpenAPI document at the same origin lists the health, XICTEK index-status, and XICTEK chat routes. This confirms basic API availability and route registration, but it is not a complete smoke-test sign-off.

The required `SMOKE_INTERNAL_SERVICE_TOKEN` is not available here. A chat request and adversarial probes without a token returned HTTP 401, as expected from the endpoint's auth boundary; these requests did not verify chat handling or guardrail behavior. Protected index status and authenticated chat/guardrail checks remain blocked. Repository docs also say that the XICTEK widget/hosting integration is deferred, so the docs host must be treated as the API under test and not proof that the website widget is wired to it.

## Check log

| Check | Expected result | Status | Evidence / next step |
|---|---|---|---|
| OpenAPI route registration | Health, XICTEK index-status, and chat routes listed | PASS | Fetched `/openapi.json` from the supplied API origin. Route registration does not establish endpoint health. |
| `GET /api/v1/health` | HTTP 200 and `status: "ok"` | PASS | Health-only smoke JSON records HTTP 200 and 1,373.07 ms for one request. No latency SLO was supplied. |
| Authenticated `GET /api/v1/xictek/index-status` | HTTP 200, built index, positive chunk count | BLOCKED | Requires the authorized `SMOKE_INTERNAL_SERVICE_TOKEN`. |
| Authenticated `POST /api/v1/xictek/chat` | HTTP 200, non-empty reply, conversation ID echoed, sources array | BLOCKED | Unauthenticated attempt returned 401; authenticated behavior remains unverified. |
| Domain source checks | Expected sources and citations across all seven domains | BLOCKED | Needs authenticated chat access and the benchmark query set. |
| Guardrail probes | Safe refusal for injection and PII/confidential-data probes across seven domains | BLOCKED | Unauthenticated probes returned 401 before chatbot guardrails ran. |
| Live latency | Report health/chat p50 and p95 from production samples | PARTIAL | One health latency sample only; no authenticated chat samples or agreed production latency target. |

## Why this is not a release sign-off

The smoke script's health-only mode was run against the supplied API origin. A prior local benchmark found the Blog & News expected-source recall at 0% for its three-query sample; that known issue remains open. See `POST_FIX_AUTOMATED_REGRESSION_REPORT_2026-11-17.md` for those results. Production regression status is therefore **unverified**, not “zero regressions.”

## Required inputs to complete

1. An authorized `SMOKE_INTERNAL_SERVICE_TOKEN` made available through an approved secure channel or set in the execution environment. Do not commit or send it in WhatsApp/chat.
2. Run the authenticated smoke mode and the same-query-set production benchmark; save outputs with secrets removed.

Run instructions are in `PRODUCTION_SMOKE_TEST_EXECUTION_GUIDE_2026-11-17.md`. The provided API origin has been used for the public health check. Once the secure token is available, execute the authenticated smoke checks and production benchmark with the same 21 queries, then update this partial status with recorded HTTP statuses, source metrics, latency samples, and guardrail outcomes.
