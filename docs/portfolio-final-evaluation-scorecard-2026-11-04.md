# Portfolio and Case Study Final Evaluation Scorecard

**Owner:** Muhammad Mohsin
**Evaluation date:** 2026-11-04
**Scope:** Portfolio/case-study retrieval, grounded response safeguards, citations, latency/cost instrumentation, and automated checks

## Retrieval benchmark

Reproduced with:

```powershell
python scripts\evaluate_portfolio_retrieval.py
```

This dependency-free lexical benchmark uses **12 hand-labeled questions** against **1,086 FAQ facts from 115 URLs**. It evaluates passage retrieval, not live embeddings or generated answers.

### Ranking comparison

| Ranker | Hit@3 | Precision@3 | MRR |
|---|---:|---:|---:|
| Baseline cosine | 0.250 | 0.083 | 0.250 |
| Query normalized | 0.417 | 0.139 | 0.417 |
| Hybrid | 0.417 | 0.139 | 0.417 |
| Hybrid + lightweight rerank | 0.417 | 0.139 | 0.417 |

### Routing comparison at top-k 2

| Setup | Candidate sources | Hit@2 | Precision@2 | MRR |
|---|---|---:|---:|---:|
| Before | All 115 URLs, hybrid ranker | 0.417 | 0.208 | 0.417 |
| After | Portfolio URL only, hybrid threshold 0.15 | **0.583** | **0.292** | **0.500** |

Portfolio source routing improved hit rate by **16.6 percentage points** and MRR by **0.083** on this benchmark. Threshold `0.15` is specific to the benchmark's hybrid score; it is not the vector store's cosine relevance threshold. The application's portfolio retrieval cap is 2 chunks instead of the prior general cap of 8, a **75% reduction in maximum chunk count**, not a measured token, latency, or dollar-cost reduction.

## Automated evaluation

| Area | Result | Scope |
|---|---:|---|
| XICTEK assistant test suite | **126 passed** | Focused module tests; includes retrieval boundaries, citation behavior, fallback, and metrics coverage |
| Career QA + portfolio/error focused tests | **38 passed** | Safety/content QA and grounded portfolio/provider-error checks |
| Portfolio lexical benchmark | **Completed** | 12 hand-labeled queries over the FAQ fact corpus |
| Live generated-answer evaluation | **Not run** | No live provider answer set was collected |
| Live embedding-index evaluation | **Not run** | Local `chunks.json` is empty |

The content QA checks confirm safe non-crashing behavior on an unbuilt index. They do **not** establish that each case-study question receives a correct generated answer or a citation from a rebuilt index.

## Runtime latency, cost, and errors

| Metric | Final status |
|---|---|
| Live portfolio retrieval latency p50/p95 | Not measurable against the empty local index |
| Live provider or end-to-end generated-answer latency | Not measured; no production provider request was made |
| Provider token usage | Runtime event records provider-reported usage when available; no live usage sample collected |
| Dollar cost | Not measured; no billing record or approved pricing schedule available |
| Error rate | No production sample available. Local tests verify bounded provider-error classification and safe fallback behavior. |
| Context-size control | At most 2 portfolio chunks versus the former general limit of 8; chunk-count proxy only |

No live performance, answer-quality, or billing claim is inferred from the lexical score or the unit tests.

## Release clearance

| Gate | Status | Evidence / remaining action |
|---|---|---|
| Portfolio-only routing and source-boundary checks | Pass in automated tests | Focused suite passed |
| Grounded-answer and citation safeguards | Pass in automated tests | Focused suite passed; no live model evaluation |
| Lexical retrieval benchmark | Pass as a reproducible offline benchmark | Portfolio-only top-k 2: hit@2 0.583, precision@2 0.292, MRR 0.500 |
| Rebuilt index with portfolio chunks | **Blocked** | `chunks.json` is 0 bytes; rebuild from approved sources and verify included URLs |
| Generated-answer benchmark against intended provider | **Blocked** | Run labeled questions, including unsupported-outcome queries, against the target provider |
| Live latency, token usage, cost, and error-rate sample | **Blocked** | Collect runtime metrics with a rebuilt index and configured provider; use approved pricing for cost |

**Decision: Not cleared for release as a live portfolio/case-study experience.** The offline retrieval and automated safeguards pass, but the empty index prevents application retrieval validation and no generated-answer, live-latency, or billing benchmark was run. Rebuild and validate the index, run the target-provider scorecard, and record live operational metrics before release clearance.
