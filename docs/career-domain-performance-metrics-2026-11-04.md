# Career Domain Performance Metrics Log

**Owner:** Muhammad Mohsin
**Evaluation date:** 2026-11-04
**Scope:** XICTEK and HisabDo careers content in the XICTEK website assistant

## Summary

The assistant has request-level metrics for provider calls, token usage, retrieval/provider/total duration, outcome, and bounded error category. The local career smoke benchmark completed without runtime errors, but the current index has no chunk metadata. All requests therefore took the deterministic no-evidence path; these timings do not represent successful retrieval or generated career answers.

## Test inputs and source corpus

The checked-in FAQ source contains **17 career facts across 3 URLs**:

- `https://xicteksystems.com/careers` — 5 facts
- `https://xicteksystems.com/careers/internship` — 8 facts
- `https://hisabdo.app/careers` — 4 facts

The 10-question local smoke set covered active openings, internship information and duration, eligibility, application review time, HisabDo opportunities, desired qualities, application materials, and application steps. Each question was sent five times after one unrecorded warm-up pass (50 measured requests total).

## Measured local request metrics

| Metric | Result | Interpretation |
|---|---:|---|
| Requests | 50 | 10 questions × 5 measured repetitions |
| Total duration, p50 | 0.03 ms | Empty-index no-evidence path only |
| Total duration, p95 | 0.04 ms | Nearest-rank percentile; empty-index no-evidence path only |
| Total duration, max | 0.04 ms | Same limitation |
| Outcomes | 50 `no_evidence` | No source passages were available to answer |
| Retrieved chunks | 0 | `chunks.json` is empty |
| Provider calls | 0 | The service correctly skipped generation without evidence |
| Provider duration | 0 ms | No provider request was made |
| Provider tokens | Not applicable | No provider usage was generated |
| Provider cost | $0 for these 50 requests | No provider calls; not a per-answer model cost estimate |
| Runtime errors | 0/50 | No exception in this fallback-path sample |

The local index files at evaluation time were `chunks.json` (**0 bytes**) and `embeddings.npy` (**12,130,176 bytes**). The metadata file being empty means the embedding matrix cannot be used for career retrieval.

## Error handling and instrumentation status

The request metrics event is `xictek_query_metrics`. It records provider identity/call status, outcome, success/completion flags, retrieved chunk count, usage basis and token fields, retrieval/provider/total duration, and a bounded error category. It excludes visitor text, conversation identifiers, retrieved passages, provider responses, IP addresses, credentials, and exception details.

The focused QA and error-handling checks completed with **38 passed**:

```powershell
..\.venv\Scripts\python.exe -m pytest tests\xictek_website_assistant\test_qa_checklist.py tests\xictek_website_assistant\test_grounded_portfolio.py -q
```

The broader XICTEK assistant suite completed with **126 passed**. Automated checks cover safety refusals, safe behavior when the index is unbuilt, and provider-failure fallback/category behavior. These are local tests, not observed production error rates. No production incident or live-provider error-rate sample was available for this evaluation.

## Cost and release interpretation

- Provider-reported prompt/completion tokens are logged when the configured provider supplies them. The mock provider's word-count estimate is labeled `mock_word_estimate`, not provider billing usage.
- Dollar cost for model-backed career answers remains **not measured**: no live provider call, billing record, or approved pricing schedule was available. Do not extrapolate the $0 fallback-path cost to generated answers.
- Successful career-answer latency, live-index retrieval latency, and production error rate remain **not measured**.
- The empty-index response is safe, but a **100% no-evidence rate in this smoke sample is a release blocker for career-answer quality**.
- Rebuild the index from approved current career sources, verify its chunk count and source URLs, rerun the career questions against that index and target provider, and capture provider-reported usage before claiming release-ready career latency or cost.
