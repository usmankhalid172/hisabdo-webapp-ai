# Careers & Job Openings — Quality, Latency & Monitoring

**Owner:**Muhammad Daniyal  
**Updated:** 3 November 2026

## Executive summary

I ran a reproducible offline TF-IDF benchmark against the repository snapshot's **976 indexed chunks**. This replaces the previously unmeasured rank metrics with measured local results.

| Method | Hit Rate@5 | Precision@5 | MRR@5 |
|---|---:|---:|---:|
| Global TF-IDF baseline | 80% | 20% | 0.583 |
| Careers metadata-filtered TF-IDF | 90% | 26% | 0.800 |

**Important:** These are offline local benchmark results, not live production retriever metrics. The supplied repository archive contains `chunks.json`, but not the deployed embedding vectors or semantic reranker configuration.

## 1. Method

- Corpus: `src/xictek_website_assistant/data/index/chunks.json` from the supplied repository ZIP (976 chunks).
- Queries: the 10 benchmark questions from the earlier Careers evaluation.
- TF-IDF: word unigrams+bigrams, English stop-word removal, sublinear term frequency, cosine similarity, top five.
- Global baseline: all indexed chunks are eligible.
- Filtered run: Q1–Q8 and Q10 restricted to XICTEK Careers/Internship URLs; historical Q9 restricted to HisabDo Careers URL.
- Relevance judgments: manually mapped expected result IDs from the earlier benchmark specification. All 100 ranked rows and labels are in `Careers_Retrieval_Top5_Details.csv`.

## 2. Results and interpretation

- Global baseline: 8/10 queries hit; 10 relevant results in 50 top-five slots.
- Careers-filtered: 9/10 queries hit; 13 relevant results in 50 slots.
- Filtering improved hit rate and MRR, but Precision@5 remains low. Many top-five slots still contain chunks not judged relevant.
- Current-openings query Q1 remained a miss even after URL filtering. This needs query expansion or better retrieval/reranking.
- Q4's global results included general cloud/company pages; Careers filtering promoted the Cloud Solutions Architect role record to rank 1.

## 3. Live chatbot quality review

Separate from rank-based retrieval metrics, the 10 manually tested live chatbot responses were graded **1 pass, 6 partial, 3 fail**. Observed issues include missing cloud-role details and an unrelated HisabDo citation, an omitted internship-duration answer in a mixed-intent query, and failure to answer historical internship status.

## 4. Manual end-to-end latency

Mean **1370 ms**; median **1000 ms**; nearest-rank p95 **3000 ms** (n=10); min 600 ms; max 3000 ms. No technical errors were reported in 10 manual requests. These are stopwatch readings, not server-side traces. Retrieval, reranking, generation, and network/queue stage timings remain individually unmeasured.

## 5. Error tracking and privacy

The error log records answer-quality defects separately from technical service errors. No technical errors were reported in the manual session. No production telemetry logs were inspected, so privacy-safe logging remains a proposed specification rather than a verified live control.

## 6. Recommendations

1. Add query expansion for role synonyms and current-opening language.
2. Enforce Careers source filtering and explicit routing for historical HisabDo questions.
3. Improve Precision@5 by excluding generic company/service chunks from Careers results.
4. Decompose mixed-intent queries and answer each requested part.
5. Capture production top-five chunk IDs, ranks, scores, and stage-level timings.
6. Run at least 100 queries before treating p95 as stable.

## 7. Reproducibility

Included: exact indexed chunk corpus (`benchmark_source/chunks.json`), benchmark script, ranked top-five results, metrics summary, updated scorecard, latency breakdown, manual live test data, and error log. Script requires `scikit-learn` and `numpy`; it does not call the production website/API.
