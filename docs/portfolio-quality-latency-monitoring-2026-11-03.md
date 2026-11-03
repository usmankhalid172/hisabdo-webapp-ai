# Portfolio Quality, Latency & Monitoring Report

**Owner:** Muhammad Mohsin
**Task:** Quality, Latency & Monitoring — Portfolio & Case Studies
**Date:** 2026-11-03

## Changes

- Portfolio and case-study queries continue to filter to the public portfolio source before ranking and now use a dedicated `portfolio_top_k=2`. Other queries retain their general top-k setting.
- Added per-request JSON metrics for provider identity/call status, answer outcome, evidence-backed success, retrieved chunk count, retrieval/provider/total latency, and provider token usage when available.
- Groq prompt, completion, and total tokens are recorded from the provider usage response. The mock provider is explicitly marked as a word-count estimate. Failures are classified without logging exception text.
- The log event excludes visitor content, history, conversation ID, retrieved passages, provider response, IP address, and credentials. It writes no per-user or per-conversation identifiers.
- The retrieval benchmark now prints a same-ranker, same-top-k before/after scorecard. Its Windows console output safely escapes characters unsupported by the active code page.

## Portfolio before/after scorecard

Reproduced with `python scripts/evaluate_portfolio_retrieval.py`. The
benchmark contains 12 hand-labeled questions over 1,086 FAQ facts from
115 URLs. These are lexical benchmark scores, not live embedding-index
or generated-answer results.

| Setup | Candidate sources | Ranker and top-k | Hit rate | Precision@2 | MRR |
|---|---|---|---:|---:|---:|
| Before | All 115 URLs | Hybrid, top-k 2 | 0.417 | 0.208 | 0.417 |
| After | Portfolio URL only | Hybrid, threshold 0.15, top-k 2 | 0.583 | 0.292 | 0.500 |

Routing to the portfolio source therefore improves hit rate by 16.6
percentage points and MRR by 0.083 in this controlled comparison. The
threshold is specific to the benchmark's hybrid score; the application
continues to use its separately configured cosine threshold.

The application previously allowed up to 8 general-query chunks for
portfolio questions. The new limit allows at most 2, a 75% reduction in
the maximum retrieved chunk count. This is a context-size/cost-control
proxy, not a measured 75% reduction in prompt tokens or provider latency:
chunk lengths vary, and no live provider call was made for this report.

## Latency and cost metrics

| Metric | Measurement |
|---|---|
| Local live-index retrieval p50/p95 | Not measurable: the local `chunks.json` is empty, so no embedding-index query was run. |
| Live provider latency p50/p95 | Not measured: no production provider request was made. Runtime logs now capture per-request provider latency in milliseconds. |
| Total request latency | Runtime logs capture end-to-end milliseconds, including deterministic refusals and no-evidence responses. |
| Provider token usage | Logs capture prompt, completion, and total tokens when Groq reports them. Missing usage stays null; mock usage is labeled `mock_word_estimate`. |
| Billed/estimated cost | Not reported. No provider pricing schedule or billing response is available, so no cost is inferred from tokens. |
| Portfolio context limit | Reduced from up to 8 chunks to up to 2; 75% fewer maximum chunks, not a claim about exact token or dollar savings. |

## Error tracking log

The application emits one `xictek_query_metrics` JSON event per request.
`query_outcome` distinguishes `answered`, `no_evidence`, `small_talk`,
`declined_prompt_injection`, `declined_out_of_scope`, `provider_error`,
and unexpected `error`. `query_success` means an evidence-grounded answer
was returned; a safe refusal or no-evidence fallback is completed but not
counted as a grounded query success.

| Error category | Trigger | Recorded behavior |
|---|---|---|
| `provider_timeout` | Provider request times out | Friendly fallback; no exception text logged |
| `provider_rate_limited` | Provider returns HTTP 429 | Friendly fallback; no exception text logged |
| `provider_unavailable` | Provider returns HTTP 5xx | Friendly fallback; no exception text logged |
| `provider_http_error` | Other provider HTTP status error | Friendly fallback; no response body logged |
| `provider_configuration_error` | Provider configuration fails before a call | Error event; existing endpoint error handling remains in force |
| `provider_error` | Other provider-call failure | Friendly fallback; generic fixed error message only |
| `retrieval_error` | Index load, embedding, or retrieval fails | Error event and normal exception propagation |
| `request_processing_error` | Other unhandled processing failure | Error event and normal exception propagation |

No production incidents were observed in this run. A mocked provider
failure verifies the `provider_error` category and confirms that visitor
content, conversation ID, and exception text are absent from the metrics
event. A zero-chunk test verifies that missing evidence is logged as a
completed, unsuccessful query. These are local automated checks, not
production error-rate measurements.

## Verification and limitations

- `python -m pytest tests/xictek_website_assistant -q` — **126 passed**.
- `python scripts/evaluate_portfolio_retrieval.py` — benchmark completed over the 12-query set; UTF-8-unrepresentable console characters are escaped on Windows.
- The benchmark is a lexical proxy and does not measure application embeddings, generated-answer quality, live latency, or live billing.
- The checked-in working index is empty. Rebuild the index from approved public sources and run live-index evaluation before using these figures as production calibration.
