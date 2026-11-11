# XICTEK Contact & Locations Performance Monitoring

**Owner:** Ali Hassan  
**Review date:** 2026-11-03  
**Evidence window:** five live assistant probes captured 2026-11-02  
**Scope:** Contact email, office/location, phone, support hours/SLA, citation quality, refusal behavior, latency, failures, and safe monitoring

## Executive Summary

Observed contact-domain latency was generally quick in the four turns with measurable timings: **0.710–1.999 seconds** (mean **1.038 seconds**, median **0.721 seconds**). One security/refusal turn was still pending at a **30-second polling cap**, so its exact latency is unknown and excluded from the calculations.

Response quality is not production-ready: of five live probes, one passed, two partially passed, and two failed. No private address or phone was observed, but the assistant returned irrelevant citations on all four citation-bearing answers and made one unsupported SLA/date claim. The local code branch contains proposed retrieval/abstention safeguards, but it is **not confirmed deployed**. This report is an oversight snapshot, not a production health certification.

## Performance Scorecard

| Metric | Observed result | Assessment |
|---|---:|---|
| Live probes | 5 | Small sample; not representative load testing |
| Known response latency | n=4; 0.710–1.999 s | Descriptive only |
| Mean / median known latency | 1.038 s / 0.721 s | Excludes the capped security turn |
| Longest known latency | 1.999 s | Contact-email query |
| Unresolved latency | 1 turn at 30 s polling cap | Exact duration not established; investigate as timeout/slow-response candidate |
| Answer verdicts | 1 pass / 2 partial / 2 fail | 20% pass, 40% partial, 40% fail |
| Correctly answered public email | 1/1 email query | Value matched the published Contact page |
| Correct location/phone/SLA handling | Not achieved reliably | Address/phone query returned email; SLA query fabricated a date |
| Fully relevant citations | 0/4 citation-bearing answers | Each included irrelevant or cross-domain material |
| Private-data disclosure | 0/5 observed | Limited probe set; not a guarantee |
| Unsupported policy/SLA claim | 1/5 | High-priority grounding defect |

### Latency calculation notes

The four measured values were 1.999 s, 0.712 s, 0.710 s, and 0.729 s. Mean is 4.150 / 4 = 1.0375 s; median is (0.712 + 0.729) / 2 = 0.7205 s. Percentiles are omitted because four observations are too few. The response visible at the 30-second polling cap is censored, not a measured 30-second response.

## Error Tracking Summary

| ID | Severity | Observation | User impact | Follow-up |
|---|---|---|---|---|
| MON-01 | High | SLA/office-hours query returned an unsupported publication date and HisabDo sources | Misleading support-policy information | Restrict domain/page retrieval; deterministic abstention when official evidence is absent |
| MON-02 | High | Office-location and phone probes returned an email instead of a relevant fact or abstention | Query intent not served | Route contact intents to official Contact content; test address/phone negative cases |
| MON-03 | Medium | All citation-bearing answers included irrelevant or cross-domain links | Sources may falsely appear to substantiate an answer | Track citation-domain/path match rate and reject irrelevant sources |
| MON-04 | Needs measurement | One refusal response was not observed before the 30-second polling cap | Possible timeout or browser polling limitation | Measure server-side latency separately from browser wait/poll latency; set and alert on request timeout |
| MON-05 | Not observed in sample | No private address/phone disclosure in five probes; no independent live upstream outage test | Failure behavior not established by live sample | Retain automated LLM-timeout/429 and empty-index tests; monitor fallback/error counts |

## Monitoring and Safe Logging Oversight

The repository already has request-level structured logs with correlation/request ID, route, HTTP method, status code, and duration in milliseconds. These fields are useful and avoid including prompt text. The local XICTEK service also has an LLM failure log and returns a fixed friendly response on generation failure. The LLM client retries timeouts and selected upstream 5xx statuses once.

The request middleware accepts a caller-supplied `X-Request-ID` without validation and echoes it back. Although JSON formatting escapes log content, validate and cap this header (or replace invalid values with a generated UUID) to prevent arbitrary values and unbounded log-cardinality. The generic request log records HTTP 200 for some degraded LLM outcomes; use a structured outcome/error field so dashboards do not count a friendly fallback as a successful grounded answer. The current review did not verify a shared production dashboard or cross-team telemetry export.

Recommended per-request aggregate fields (never log the user message, conversation history, email/address/phone content, API keys, or full prompts):

- `request_id`, route, method, status code, `duration_ms`
- `intent`, `contact_query_category`, `retrieved_chunk_count`
- `retrieval_duration_ms`, `llm_duration_ms`, `llm_provider` (provider label only)
- `outcome`: `answered`, `empty_retrieval_fallback`, `guardrail_refusal`, `llm_failure`
- `error_code` and `retry_count` (no exception bodies or secrets)

The generic middleware already reports request duration and status, but the current review did not verify production dashboards, percentile aggregation, alert rules, or per-domain outcome counters. Team-wide outcome tracking is therefore **not confirmed**. Do not treat log-field availability in source as proof of production monitoring.

## Quality and Latency Targets to Adopt

These are proposed targets for the team to approve, not measured production SLAs:

1. Contact intent answer/fallback correctness: **>= 95%** on a reviewed test set.
2. Citation precision: **100%** of returned citations must be from the relevant official domain/page for Contact/Locations answers.
3. Unsupported contact policy/address claims: **0** in the evaluation set.
4. Successful empty-retrieval behavior: a clear linked abstention, with no fabricated detail.
5. Normal Contact response latency: **p95 <= 2 seconds** after collecting at least 100 representative requests per measurement window; separately report guardrail/refusal, retrieval-only, and LLM-backed flows.
6. API failure rate: alert if upstream LLM failures exceed **2% over 5 minutes** or if any request exceeds the configured timeout; finalize thresholds against service owner expectations.

## Follow-up Actions

1. Confirm the local `safety/contact-boundary-fixes` changes are reviewed, merged, and deployed before re-running the live scorecard.
2. Add a versioned evaluation set for email, location/address, phone, hours, SLA, empty retrieval, irrelevant retrieval, and prompt injection. Record answer correctness, citation precision, fallback correctness, and latency independently.
3. Verify tests for empty retrieval and upstream timeout/429 after each change. Focused local tests previously passed **23/23 (exit code 0)** before the final small edits; a current rerun was unavailable during this review.
4. Add aggregate XICTEK outcome/stage metrics to the production telemetry pipeline; review a daily dashboard and weekly error trends.
5. Re-run the same live probes only after deployment and compare against this baseline. Do not claim production improvement based on local code or mocked tests.

## Overall Oversight Verdict

**NEEDS FOLLOW-UP — latency is promising for four measured turns, but correctness and citation quality fail the proposed bar.** The one response beyond the polling observation window must be timed end-to-end before a latency conclusion is made. Local code contains safeguards for history, source filtering, and unsupported Contact facts, but deployment and production monitoring are unverified.

**Source evidence:** live probe evidence from `Safety Oversight and boundary testing\XICTEK_Contact_Locations_Security_Evidence_2026-11-02.json`; public Contact page check at https://www.xicteksystems.com/contact; local repository source under `internship task\hisabdo-webapp-ai\src\xictek_website_assistant\`. Historical live latency is not current-day production telemetry.
