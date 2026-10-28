# Portfolio and Case Study Retrieval Evaluation

**Owner:** Muhammad Mohsin  
**Task:** Advanced Retrieval & Query Evaluation — Portfolio & Case Studies  
**Evaluation date:** 2026-10-28

## Goal

Measure whether portfolio questions retrieve the supporting project passages without filling context with unrelated company, blog, or HisabDo help content. The benchmark covers project identity, technologies, challenge, solution, outcomes, visuals, flagship status, public case-study availability, custom work, and contact path.

## Corpus and method

The reproducible benchmark is `scripts/evaluate_portfolio_retrieval.py`. It reads the checked-in `xictek_faq_raw.jsonl` (1,086 FAQ facts across 115 URLs), uses 12 hand-labeled portfolio questions, and reports hit@3, precision@3, and MRR. The answer fact(s) are relevant labels; other facts are distractors. The four compared rankers are:

1. **Baseline:** bag-of-words cosine similarity on the unmodified query.
2. **Normalized:** cosine after small portfolio-specific synonym/alias expansion.
3. **Hybrid:** 65% normalized cosine plus 35% exact-token coverage.
4. **Reranked:** hybrid score followed by a lightweight exact-token second-stage score.

The script additionally tests thresholds and top-k values after restricting candidates to the `/portfolio` page. That source restriction is a corpus metadata filter, not part of the ranking formulas.

## Results

| Ranker | Hit@3 | Precision@3 | MRR |
|---|---:|---:|---:|
| Baseline cosine | 0.250 | 0.083 | 0.250 |
| Query normalized | 0.417 | 0.139 | 0.417 |
| Hybrid | 0.417 | 0.139 | 0.417 |
| Hybrid + lightweight rerank | 0.417 | 0.139 | 0.417 |

Normalization raises hit rate by 16.7 points. Hybrid weighting and this simple reranker add no measured gain over normalized cosine on this small set. Without a source restriction, the top results for queries such as “What is HisabDo?” and “What challenge does the project address?” include unrelated Android platform, privacy, and general service facts. Relevant portfolio passages often appear below the first three results.

After restricting candidates to the portfolio URL, the threshold/top-k sweep was:

| top-k | Minimum hybrid score | Hit rate | Precision (denominator = k) | MRR |
|---:|---:|---:|---:|---:|
| 1 | 0.15–0.30 | 0.417 | 0.417 | 0.417 |
| 2 | 0.15 | **0.583** | **0.292** | 0.500 |
| 2 | 0.20 | 0.500 | 0.250 | 0.458 |
| 2 | 0.25–0.30 | 0.417 | 0.208 | 0.417 |
| 3 | 0.15 | 0.667 | 0.222 | 0.528 |
| 3 | 0.20 | 0.583 | 0.194 | 0.486 |
| 3 | 0.25–0.30 | 0.500 | 0.167 | 0.444 |
| 4 | 0.15 | 0.667 | 0.167 | 0.528 |

The best precision-oriented operating point in the tested sweep is **portfolio source filter + top-k 2 + hybrid threshold 0.15**. Use top-k 3 at the same threshold when coverage matters more than context size. Requiring 0.20 or more reduces coverage on this corpus. These are benchmark-specific hybrid-score values, not cosine thresholds.

## Recommendation

- Route portfolio/case-study intents to the portfolio source and filter candidates by URL or an explicit `content_type=portfolio` metadata field before ranking.
- For this filtered path, start with **top-k 2**; use **top-k 3** when the query explicitly requests multiple examples or broader project detail.
- If the filtered path uses the benchmark's hybrid scorer, start with score threshold **0.15** and calibrate it against newly labeled queries before production.
- Keep the existing general retrieval threshold separate. The app's `VectorStore.query()` expects cosine similarity, while this benchmark's tuned threshold is on the hybrid score scale; copying `0.15` into `relevance_threshold` would not be a valid calibration.
- Do not enable the evaluated lightweight reranker as a quality improvement: it did not change aggregate metrics. A trained cross-encoder or another substantive second-stage model needs its own measured comparison.
- Keep outcome claims grounded: the portfolio source explicitly says quantified business/customer impact metrics are not published.

## Evidence limits and next validation

The checked-in `data/index/chunks.json` is empty even though `embeddings.npy` is nonempty. The current environment also has no NumPy installed, so the application vector index could not be loaded or evaluated. Consequently, the report is a dependency-free lexical benchmark over the source FAQ facts, not a measurement of the deployed embedding model or the live vector store. The local portfolio markdown (`data/portfolio/hisabdo.md`) should also be included in the next ingest/index build. The 12-query set is small and hand-labeled; collect more paraphrases (including Urdu/Roman Urdu) and explicit unanswerable portfolio questions before treating these settings as production-calibrated.

## Reproduce

From `hisabdo-webapp-ai`:

```powershell
python scripts/evaluate_portfolio_retrieval.py
```
