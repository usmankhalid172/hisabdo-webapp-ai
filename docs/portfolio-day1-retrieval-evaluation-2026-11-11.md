# Portfolio Domain Retrieval Evaluation — Day 1

**Owner:** Muhammad Mohsin
**Evaluation date:** 2026-11-11
**Scope:** Previously failed portfolio questions, industry and technology query expansion, and threshold selection

## Executive result

The repeatable offline comparison favors portfolio-only routing and the
historical lexical hybrid threshold of **0.15 with top-k 2**. On the existing
12-query benchmark this gives hit@2 **0.583**, precision@2 **0.292**, and MRR
**0.500**. Raising the threshold to 0.20 or 0.25 lowers hit rate.

The targeted rewrite test found **no improvement** from adding industry aliases
to the three case-study queries. Explicit framework/database expansion matched
one historical HisabDo fact, but that technology statement is excluded from the
current approved HisabDo source. It is a stale-source retrieval warning, not a
valid answer hit. Do not add guessed industries or stack names to production
rewrites.

These are lexical diagnostics, not measurements of the application's embedding
retriever. The local application index has an empty `chunks.json`; therefore
no production-vector evaluation or production threshold calibration was
possible.

## Evaluation setup

- The existing benchmark reads 1,086 FAQ facts across 115 URLs and uses 12
  previously labeled portfolio questions.
- The new rewrite test reads the same historical corpus and restricts candidate
  facts to the `/portfolio` URL. It tests three industry queries and one
  technology query; labels are keyword anchors, not human-judged answer
  relevance.
- “Vector” in these scripts means cosine over bag-of-words term-count vectors.
  “Hybrid” means 65% normalized term-vector cosine plus 35% exact-token
  coverage. Neither is the configured multilingual embedding model.
- The current approved local source is
  [`hisabdo.md`](../src/xictek_website_assistant/data/portfolio/hisabdo.md).
  It does not attribute a technology stack to HisabDo and excludes client
  case-study details pending authorization. The historical FAQ corpus is for
  retrieval diagnostics only, not a source for current answers.

## Results

### Previously failed 12-question benchmark

| Setup | Candidate scope | Cutoff | Hit | Precision | MRR |
|---|---|---:|---:|---:|---:|
| Term-vector cosine, unexpanded | All 115 URLs, top-3 | n/a | 0.250 | 0.083 | 0.250 |
| Term-vector cosine, normalized | All 115 URLs, top-3 | n/a | 0.417 | 0.139 | 0.417 |
| Hybrid | All 115 URLs, top-3 | n/a | 0.417 | 0.139 | 0.417 |
| Hybrid | Portfolio URL only, top-2 | 0.15 | **0.583** | **0.292** | **0.500** |
| Hybrid | Portfolio URL only, top-2 | 0.20 | 0.500 | 0.250 | 0.458 |
| Hybrid | Portfolio URL only, top-2 | 0.25 | 0.417 | 0.208 | 0.417 |

Query normalization improved all-source hit@3 over the unexpanded lexical
baseline. The hybrid weighting and lightweight reranker did not improve the
aggregate over normalization. Source filtering reduced cross-domain
competition. The original query-level failures and label caveats remain in the
[portfolio failure log](./portfolio-domain-failure-log-2026-11-05.md).

### Industry and technology rewrite diagnostic

| Test group | Term-vector cosine: original → expanded | Hybrid: original → expanded | Interpretation |
|---|---:|---:|---|
| Logistics / supply chain | hit@2 0/1 → 0/1 | hit@2 0/1 → 0/1 | No matching portfolio passage in this corpus slice; expansion did not create evidence. |
| HealthTech / healthcare | hit@2 0/1 → 0/1 | hit@2 0/1 → 0/1 | No matching portfolio passage in this corpus slice; expansion did not create evidence. |
| FinTech / B2B SaaS | hit@2 0/1 → 0/1 | hit@2 0/1 → 0/1 | No matching portfolio passage in this corpus slice; expansion did not create evidence. |
| HisabDo framework / database | hit@2 1/1 → 1/1 | hit@2 1/1 → 1/1 | The matching historical technology fact is not approved in the current source; do not serve it. |
| **All four diagnostic queries** | **hit@2 0.250 → 0.250; precision@2 0.125 → 0.125** | **hit@2 0.250 → 0.250; precision@2 0.125 → 0.125** | No net measured gain; the only match is excluded source content. |

Industry results are not evidence that XICTEK has no such projects; they mean
this portfolio-only benchmark did not return an anchored fact from its
historical corpus. The technology match is not a supported current answer.
Neither outcome should be turned into a public claim.

## Threshold recommendation

1. **Offline lexical hybrid experiment:** use **0.15 and top-k 2** as the
   precision-oriented comparison point for the 12-question historical
   benchmark. Use top-k 3 at 0.15 only when the benchmark's higher hit rate
   (0.667) is worth its lower precision (0.222).
2. **Application vector store:** do **not** copy 0.15 into
   `relevance_threshold`. The application uses cosine similarity from learned
   embeddings, while 0.15 above is on the separate lexical-hybrid score scale.
   Keep the existing vector threshold of 0.20 provisional until a reviewed
   corpus is indexed and the real embedding path is evaluated.
3. **Release gate:** do not enable industry or specific technology rewrites
   until current, approved portfolio passages support those terms. Rebuild the
   index from reviewed sources, verify its portfolio chunks, then rerun the
   failed queries against actual embeddings and calibrate on manually reviewed
   relevance labels.

## Reproduction and limits

From `hisabdo-webapp-ai`:

```powershell
python scripts\evaluate_portfolio_retrieval.py
python scripts\evaluate_portfolio_query_rewrites.py
```

The rewrite log is in
[`portfolio-query-rewriting-test-log-2026-11-11.md`](./portfolio-query-rewriting-test-log-2026-11-11.md).
The empty chunk metadata prevents mapping the existing embedding array to
source passages, so this run does not establish live-vector retrieval,
generated-answer quality, latency, or production performance.
