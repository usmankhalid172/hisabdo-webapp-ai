# Quality, Latency & Monitoring — Portfolio & Case Studies

**Owner:** Hassan Hussain 
**Prepared:** 3 November 2026  
**System:** XICTEK / HisabDo Portfolio & Case Studies chatbot

## Executive summary

This package consolidates the portfolio chatbot evaluation evidence previously supplied and calculates latency statistics from the 10 production timing samples.

### Key measured latency results

| Metric | Result |
|---|---:|
| Total-duration mean | 3,505.99 ms (3.51 s) |
| Total-duration median (p50) | 621.66 ms |
| Total-duration p95 (nearest-rank) | 29,430.00 ms (29.43 s) |
| Minimum | 420.02 ms |
| Maximum | 29,430.00 ms |
| Server-wait mean | 602.03 ms |
| Server-wait median | 597.99 ms |
| Server-wait p95 (nearest-rank) | 958.48 ms |
| Mean total excluding the 29.43 s outlier | 625.54 ms |

**Important outlier:** one request recorded 29,430 ms total duration while server waiting was 421.19 ms. The 29.01-second difference suggests the delay occurred outside the measured server-wait interval, but the available evidence does not identify whether it was browser/client, network, retry, streaming, or measurement-boundary delay. It must be traced rather than attributed to a specific component.

## Before / after scorecard

The before column records observed weaknesses from prior live chatbot evaluation. The after column defines recommended fixes and acceptance targets. **No post-tuning run was supplied**, so after results are correctly marked not re-tested; targets are not presented as achieved.

Observed quality issues:
- A portfolio query asking for project names/source links received only a generic “2+ projects completed” response.
- A follow-up included unsupported React/Next.js/TypeScript assertions.
- Citations were generic rather than tightly tied to the requested case study.
- Multi-turn follow-up did not consistently preserve project-specific grounding.
- The portfolio source material identifies HisabDo as a flagship product and lists Flutter, Supabase and PostgreSQL; these details should be drawn from the project record rather than inferred.

## Provider usage and cost

Provider/model usage, input/output tokens, retries, rate-card version and actual cost were **not present in the supplied evidence**. Therefore no provider cost has been fabricated. `Provider_Usage_Cost_Metrics.csv` lists the exact measurements needed for the next instrumented run.

Recommended cost calculation:
`estimated_cost = (input_tokens × input_rate + output_tokens × output_rate) / 1,000,000`
Use the verified provider rate card and record its effective date and currency. Include cached-token pricing or other provider-specific dimensions only if applicable and documented.

## Error tracking

The error log separates:
- Answer-quality defects (unsupported claims, incomplete answers, citation relevance, context drift)
- Performance anomaly (one 29.43-second total-duration outlier)
- Monitoring gaps (provider-cost and technical-error telemetry not available)

No technical error rate can be calculated from the current timing samples alone.

## Safe logging boundaries

Log only allowlisted operational metadata:
- Random request ID; timestamp; portfolio intent category; normalized outcome code
- Provider/model identifier where authorized; input/output token counts; retry count
- End-to-end, server-wait and provider-stage durations
- HTTP status and normalized error category
- Currency and rate-card version for calculated cost

Do **not** routinely log raw prompts, full conversation text, customer names, emails, phone numbers, account IDs, IP addresses, CVs, or other personal/customer content. Use bounded enums and aggregate metrics. If query deduplication is needed, use an approved keyed HMAC fingerprint rather than storing the raw query.

## Recommended tuning plan

1. Retrieve project-specific chunks using project name and portfolio metadata filters.
2. Require every factual technology, outcome, and numeric claim to be supported by a retrieved source chunk.
3. Return case-study-specific citations; reject generic links that do not substantiate the claim.
4. Preserve project entity and intent across multi-turn follow-ups.
5. Add an explicit fallback for unsupported metrics such as revenue percentages.
6. Instrument provider/model/token/retry/cost counters and stage-level latency.
7. Investigate the 29.43-second outlier using correlated request IDs and client/server timing spans.
8. Re-run the same query set after changes and fill the after column with measured results.

## Evidence and limitations

- Latency: 10 previously supplied production timing observations, including total duration and server waiting.
- Quality: qualitative outcomes from prior portfolio chatbot tests; no full labelled test corpus or retrieval top-five trace was available in this task context.
- Provider usage/cost: not measured.
- After-tuning performance: not measured.
- This package is a measurement-backed baseline and monitoring plan, not a claim that production code was changed or deployed.
