# Portfolio & Case Studies — Quality and Latency Report

**Prepared:** 4 November 2026  
**Coordinator:** Hassan Hussain  
**Domain evaluation source:** Muhammad Mohsin, Portfolio final evaluation scorecard  
**Status:** Evidence consolidated; production release not cleared

## Executive summary

The latest Portfolio evaluation is a 12-query offline lexical retrieval benchmark. Portfolio-only URL filtering improved Hit@2 from 41.7% to 58.3% and MRR from 0.417 to 0.500. This is a useful relevance improvement, but the scorecard explicitly did not run live embeddings, generated-answer evaluation, or a live production test. The current local `chunks.json` was reported empty, so the latest scorecard does not establish a functioning end-to-end production pipeline.

Historical latency observations from the earlier Portfolio monitoring submission show a 3.506-second mean and 0.622-second median across 10 samples, with a 29.430-second p95/max outlier. Those observations have no verified build identity and cannot be tied to the final retrieval candidate. They are historical signals, not a release-quality latency result. No end-to-end latency, provider cost, or error rate is established for the current candidate.

## Quality and retrieval measurements

The latest scorecard used 12 hand-labeled queries over 1,086 FAQ facts and 115 URLs. It evaluated lexical retrieval; the reported hybrid and reranking configurations used the same offline lexical data and did not demonstrate a live vector/LLM pipeline.

| Configuration | Hit@3 | Precision@3 | MRR |
|---|---:|---:|---:|
| Baseline cosine | 0.250 | 0.083 | 0.250 |
| Query normalized | 0.417 | 0.139 | 0.417 |
| Hybrid | 0.417 | 0.139 | 0.417 |
| Hybrid + rerank | 0.417 | 0.139 | 0.417 |
| Portfolio-only URL filter, hybrid, top-k 2, threshold 0.15 | 0.583 | 0.292 | 0.500 |

The filtered configuration improves Hit@2 by 16.6 percentage points and MRR by 0.083 versus the unfiltered top-k 2 hybrid comparison. The 0.15 value is a hybrid score cutoff in this evaluation; it must not be described as a cosine-similarity threshold. At 12 queries, the result is directional and should be confirmed on a larger held-out set.

The scorecard reports a maximum chunk cap comparison of 2 versus 8 (75% fewer maximum chunks). This is a configuration/capacity reduction, not a measured latency or token-cost saving. The scorecard records 126 passing full XICTEK tests and 38 passing focused Careers/Portfolio/error tests; these are test-suite results, not query-level live answer accuracy.

## Latency and operational evidence

The previous monitoring submission contains 10 historical production timing observations:

| Measure | Total response time | Server wait |
|---|---:|---:|
| Mean | 3,505.986 ms | 602.027 ms |
| Median | 621.66 ms | 597.99 ms |
| p95 (nearest rank, n=10) | 29,430 ms | 958.48 ms |
| Minimum / maximum | 420.02 / 29,430 ms | — |

One sample took 29,430 ms total while server wait was 421.19 ms, leaving approximately 29,008.81 ms outside the recorded server-wait measure. Its cause was not established; it must not be attributed to a specific component. The small sample makes p95 highly sensitive to this outlier. The prior report proposed mean/p50 ≤1 second and p95 ≤4 seconds as targets; it did not show those targets were met after tuning.

The historical timing data lacks provider/model/token/cost telemetry, consistent build identity, and a post-tuning rerun. Thus it cannot support a current release latency or cost claim. The latest scorecard says the local Portfolio index is empty and successful retrieval was not available. There are no current-candidate production latency, provider cost, or production error-rate measurements.

## Release assessment

**Decision: Not cleared for production release on the evidence provided.**

Before clearance, the team should rebuild a non-empty index from the approved Portfolio content, record a commit/build/index identifier, rerun the 12-query set plus a held-out suite through the actual API and configured embedding/model provider, verify each answer and source link, and collect warmed and cold latency, HTTP/error, token, and cost telemetry. Recheck the top-k and 0.15 hybrid cutoff on the expanded set and document false positives and misses. Validate that the historical latency outlier is understood or excluded with a documented reason.

## Evidence boundaries

- Latest relevance numbers are offline retrieval measurements; no generated-answer accuracy is claimed.
- Historical timing is a separate, earlier sample with unknown build association; do not combine it statistically with the latest benchmark.
- `top-k 2` and the 0.15 hybrid threshold belong to the reported filtered comparison, not a universal vector-store setting.
- A reduced chunk cap does not itself prove lower latency, cost, or improved answer quality.
- This report consolidates supplied evidence; it does not represent a deployment or sign-off by the product/release owner.
