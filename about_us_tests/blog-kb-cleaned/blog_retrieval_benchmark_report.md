# Blog & News Retrieval Benchmark Report
Date: 2026-11-11 | Corpus: 47 articles (blog-kb-cleaned-consolidated.md) | Script: blog_retrieval_benchmark.py

## 1. Scope and limitations
- **Queries:** the 24 from blog-retrieval-evaluation.md, plus 6 held-out probes from the weak-question analysis (P2, P6-P10) = 30 answerable queries, and 10 unanswerable queries (P1, P4, X1-X8) for threshold tuning.
- **Vector method:** real all-MiniLM-L6-v2. Lexical = TF-IDF and BM25.
- **Not production code:** src/retrieval.py was not available, so this is a standalone reimplementation. Confirm the numbers against the real retriever.
- **Small sample:** 30 + 10 queries. A difference of one query (3.3 points) is within noise.

## 2. Method comparison (30 answerable queries)
| Method | Hit@1 | Hit@3 | Recall@3 | MRR@3 | Hit@5 |
|---|---|---|---|---|---|
| TF-IDF | 0.767 | 0.867 | 0.756 | 0.817 | 0.933 |
| BM25 | 0.700 | 0.900 | 0.722 | 0.783 | 0.933 |
| Vector (MiniLM) | 0.900 | 0.900 | 0.778 | 0.900 | 0.967 |
| Hybrid a=0.5 | 0.833 | 0.967 | 0.850 | 0.894 | 0.967 |
| Hybrid a=0.7 | 0.867 | 0.967 | 0.839 | 0.911 | 0.967 |
| Hybrid RRF | 0.867 | 0.933 | 0.789 | 0.900 | 0.967 |

Reading:
- Both semantic methods clearly beat lexical (MRR@3 0.89-0.91 vs 0.78-0.82). Vector alone is best at Hit@1.
- Hybrid improves coverage in the top 3: Hit@3 0.967 and Recall@3 up to 0.850, vs 0.900 / 0.778 for vector alone.
- Best overall: hybrid a=0.7 (highest MRR@3, tied-best Hit@3). The gap between a=0.5 and a=0.7 is one or two queries, so treat them as equivalent until more queries are added.
- The earlier report's claim that hybrid beats lexical and semantic alone is partly supported: hybrid beats lexical clearly, and beats vector on Hit@3 and Recall@3 but not on Hit@1.

## 3. Remaining failures
Failures seen in the proxy run (to be confirmed against per_query_log.csv from the MiniLM run):
| Query | Likely cause |
|---|---|
| H1 internal tools online | concept query; "portal"/"enterprise" absent from query |
| H4 app doesn't get hacked | "hacked" vs "security" vocabulary gap |
| P6 "chatobt" typo | typo unhandled |

These are vocabulary problems, not missing content (every expected article exists).

## 4. Metadata filtering (hybrid a=0.5, k=3)
| Filter | Hit@3 | Recall@3 | MRR |
|---|---|---|---|
| none | 0.967 | 0.850 | 0.894 |
| predicted category (keyword rules) | 0.900 | 0.706 | 0.861 |
| oracle category (upper bound) | 1.000 | 0.783 | 0.978 |

- The keyword category predictor hurts on every metric. Keep it disabled.
- A perfect classifier would lift MRR to 0.978 but lowers recall (0.850 -> 0.783). Use category as an optional user-chosen filter or a soft boost, not a hard default.
- Category values were normalized first (AI AND AUTOMATION + ARTIFICIAL INTELLIGENCE, MOBILE APPS + MOBILE DEVELOPMENT, Uncategorized -> SOFTWARE DEVELOPMENT).
- Date filtering could not be tested: all 47 articles have published_date = 2026-09-07. Real publish dates are needed.

## 5. Threshold tuning (abstain when top-1 score < t)
Absolute cosine of the top-1 article, tested on 30 answerable + 10 unanswerable queries.

MiniLM cosine (recommended gate):
| t | correct | wrong answers | unanswerable accepted | wrongly refused | precision | recall | F1 |
|---|---|---|---|---|---|---|---|
| 0.00 | 27 | 3 | 10/10 | 0 | 0.675 | 0.900 | 0.771 |
| 0.20 | 27 | 3 | 5/10 | 0 | 0.771 | 0.900 | 0.831 |
| 0.30 | 26 | 3 | 1/10 | 1 | 0.867 | 0.867 | 0.867 |
| 0.35 | 24 | 0 | 1/10 | 6 | 0.960 | 0.800 | 0.873 |
| 0.40 | 22 | 0 | 1/10 | 8 | 0.957 | 0.733 | 0.830 |
| 0.50 | 16 | 0 | 0/10 | 14 | 1.000 | 0.533 | 0.696 |

- Recommended: 0.35 (max F1). Use 0.30 if missing an answer is worse than a wrong one. Use 0.50 if a wrong answer is worse (it rejects all 10 unanswerable queries but refuses 14 of 30 valid ones).
- Scores separate well: answerable queries have median 0.524 (min 0.275); unanswerable queries have median 0.201 (max 0.421). One unanswerable query scores up to 0.421 and passes at every threshold below 0.50.
- TF-IDF alone reaches only F1 0.778 (at 0.15), so MiniLM is much better at separating answerable from unanswerable questions.
- TF-IDF reference: P1 (refund policy) scores 0.152, just above the 0.15 cutoff, which is how it leaks through a lexical-only gate.

Important: these thresholds apply to the raw MiniLM cosine of the top-1 article. If production uses one threshold on a blended hybrid score, that scale is different. Gate on the MiniLM cosine separately, or re-run the sweep on the production blended score before copying 0.35.

## 6. Data-quality findings
- The 33 "duplicates" are not duplicates. Mean TF-IDF cosine to the claimed primary is 0.46 (max 0.53; no pairs >= 0.9), vs 0.29 across all pairs. They share template text. Excluding them from the index would make most expected articles unreachable. Index all 47.
- The previous retrieval report is inconsistent: it states 24 queries but also a "15-query evaluation set", and its grid optimized MRR, which does not penalize low-quality answers. Only unanswerable queries expose threshold quality.
- The H1-H8 queries drove the synonym fixes, so the earlier "100% Hit@3" on the 24-query set is tuned on itself.

## 7. Next steps
1. Supply real publish dates, then add date-filter tests.
2. Identify which unanswerable query scores 0.421 and test whether a title-term guard removes it.
3. Add typo tolerance (P6) and synonyms for "hacked/security" and "internal tools/portal".
4. Have a reviewer confirm the expected articles for the 6 held-out queries.