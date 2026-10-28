# Day 28 — Retrieval Comparison Report

## 1. Objective
Compare plain similarity retrieval and Maximal Marginal Relevance (MMR), test different top-k and relevance-threshold settings, and identify retrieval-quality issues.

## 2. Existing Environment
- Indexed chunks: 976
- Unique source URLs: 115
- Existing settings: top_k = 8; relevance_threshold = 0.20
- Active query representation: persisted TF-IDF vectorizer
- Tests previously run: 19 passed
- Warning: persisted scikit-learn objects were created with version 1.5.2; current environment uses 1.7.2.

## 3. Benchmark Method
Eight provisional queries were tested:
1. How do I manage daily Khata?
2. How can I track customer udhaar?
3. How do I record business expenses?
4. How can I understand business profit?
5. How do I use HisabDo for financial reports?
6. How do I manage business cash flow?
7. What features does HisabDo provide?
8. How can I use AI for business management?

Retrieval modes: plain similarity (`diversify=False`) and MMR (`diversify=True`).

Thresholds tested: 0.10, 0.15, 0.20, 0.25.
Top-k values tested: 3, 5, 8.

## 4. Observed Results

| Query | Plain Similarity | MMR |
|---|---|---|
| Daily Khata | Returned the Daily Khata guide more than once. | Reduced some repetition but still returned general blog content. |
| Customer udhaar | Returned Khata, shop accounting, and bookkeeping content. | Included finance tips and a cross-platform development page, indicating possible irrelevant results. |
| Business expenses | Returned expense tracking and budgeting content. | Included expense categories and cash-flow content; relevance requires manual checking. |
| Business profit | Returned 3 results at threshold 0.20 in the tested top-k configurations. | Returned the same 3 results; no clear improvement observed. |
| Financial reports | Returned the product guide and expense content, but also an XICTEK company page. | Included repeated product-guide content and disclaimer content. |
| Business cash flow | Included duplicate cash-flow article chunks. | Reduced some repetition but still included general blog content. |
| HisabDo features | Returned services, About HisabDo, and product pages. | Returned similar product/company pages, with some less-specific pages. |
| AI for business | Returned technology/company pages and HisabDo content; relevance was uncertain. | Similar pattern; repeated blog content remained. |

## 5. Threshold and Top-k Findings
- Tested thresholds: 0.10, 0.15, 0.20, 0.25.
- At top-k = 8, some queries returned fewer than eight results at higher thresholds.
- At top-k = 3 or 5, the top-k limit often capped the number of returned results.
- Result counts alone do not establish passage relevance or identify an optimal threshold.

## 6. Preliminary Conclusion
MMR reduced repetition for some queries, but did not consistently improve relevance or remove unrelated content. Plain similarity sometimes returned more directly related passages. Neither method can yet be declared the overall winner.

The existing configuration (top-k = 8, threshold = 0.20) is recorded as the baseline, not as a proven optimal configuration.

## 7. Limitations and Remaining Work
1. Replace provisional queries with the confirmed Day 1 failed-query list.
2. Label retrieved passages as relevant or irrelevant for each query.
3. Measure Precision@k and relevant-passage coverage.
4. Tune threshold and top-k using those relevance labels.
5. Test metadata filtering, query normalization/rewrite, and reranking.
6. Investigate the scikit-learn persisted-vectorizer version warning.
7. Rerun relevant tests after any code/configuration changes.

## 8. Completion Status
This report documents the provisional benchmark observations. The original Day 1 failed-query evaluation, relevance-labelled metrics, and final parameter selection are not yet verified.

## Day 1 Failed-Query Benchmark — Current Index

### Test setup
- Original failed queries tested: 17
- Current index: 976 chunks across 115 URLs
- top_k: 5
- Relevance threshold: 0.20
- Compared approaches: Plain Similarity and MMR

### Results observed
- Software-cost query: relevant software development cost article ranked first.
- Mobile-app-cost query: mobile app cost guide appeared in the top 3.
- AI chatbot customer-support query: chatbot development article ranked first.
- Azure vs AWS: Azure development article ranked first, but generic pages also appeared.
- Chatbot query with punctuation variation: chatbot development article ranked first.
- iOS development: relevant iOS article appeared, but generic pages ranked above it in plain similarity.
- ERP automation: plain similarity missed the strongest expected article; MMR included an AI-in-ERP article.
- Internal tools, slow checkout, documentation assistant, app security, legacy modernization, recurring subscriptions, and deployment pipeline queries showed weak or missing expected matches in the top 5.
- Startup launch: a startup mobile-app article appeared in MMR results but not in the plain-similarity top 5.

### Comparison
MMR sometimes changed the order and reduced repetitive results, but it did not consistently improve relevance. Both methods still returned unrelated content for several failed queries. Therefore, neither method is verified to satisfy the requirement to filter all unrelated context.

### Limitations and next steps
- The current index contains 976 chunks and is not the same corpus as the historical 47-article blog evaluation.
- Formal Precision@5, Recall@5, and MRR have not yet been calculated using verified relevance labels.
- Threshold 0.20 and top_k 5 are the tested baseline, not a proven optimum.
- The saved TF-IDF vectorizer produces a scikit-learn version warning (saved with 1.5.2; current environment 1.7.2).
- Next: map expected articles to current URLs, calculate relevance metrics, test candidate threshold/top_k settings against those metrics, and rerun tests.

## Label-Based Threshold and Top-k Evaluation

### Evaluation method
- 17 historical failed queries tested against the current index.
- Compared Plain Similarity and MMR.
- Threshold candidates: 0.10, 0.15, 0.20, 0.25, 0.30.
- top_k candidates: 3, 5, 8.
- Repeated chunks with the same title were deduplicated for article-level evaluation.
- Relevance was matched against expected article-title phrases from the historical report.
- These are title-label metrics, not human-judged semantic relevance.

| Mode | Threshold | top_k | Precision@k | Recall@k | MRR | Coverage |
|---|---:|---:|---:|---:|---:|---:|
| Plain | 0.10 | 3 | 0.118 | 0.235 | 0.255 | 29.4% |
| Plain | 0.10 | 5 | 0.094 | 0.324 | 0.267 | 35.3% |
| Plain | 0.10 | 8 | 0.081 | 0.382 | 0.285 | 47.1% |
| Plain | 0.15 | 3 | 0.118 | 0.235 | 0.255 | 29.4% |
| Plain | 0.15 | 5 | 0.094 | 0.324 | 0.267 | 35.3% |
| Plain | 0.15 | 8 | 0.081 | 0.382 | 0.285 | 47.1% |
| Plain | 0.20 | 3 | 0.118 | 0.235 | 0.255 | 29.4% |
| Plain | 0.20 | 5 | 0.094 | 0.324 | 0.267 | 35.3% |
| Plain | 0.20 | 8 | 0.081 | 0.382 | 0.285 | 47.1% |
| Plain | 0.25 | 3 | 0.118 | 0.235 | 0.255 | 29.4% |
| Plain | 0.25 | 5 | 0.082 | 0.294 | 0.267 | 35.3% |
| Plain | 0.25 | 8 | 0.051 | 0.294 | 0.267 | 35.3% |
| Plain | 0.30 | 3 | 0.098 | 0.206 | 0.235 | 23.5% |
| Plain | 0.30 | 5 | 0.071 | 0.265 | 0.247 | 29.4% |
| Plain | 0.30 | 8 | 0.044 | 0.265 | 0.247 | 29.4% |
| MMR | 0.10 | 3 | 0.118 | 0.265 | 0.265 | 29.4% |
| MMR | 0.10 | 5 | 0.106 | 0.343 | 0.306 | 47.1% |
| MMR | 0.10 | 8 | 0.074 | 0.363 | 0.306 | 47.1% |
| MMR | 0.15 | 3 | 0.118 | 0.265 | 0.265 | 29.4% |
| MMR | 0.15 | 5 | 0.106 | 0.343 | 0.309 | 47.1% |
| MMR | 0.15 | 8 | 0.110 | 0.490 | 0.326 | 58.8% |
| MMR | 0.20 | 3 | 0.137 | 0.294 | 0.284 | 35.3% |
| MMR | 0.20 | 5 | 0.129 | 0.392 | 0.325 | 52.9% |
| MMR | 0.20 | 8 | 0.103 | 0.451 | 0.325 | 52.9% |
| MMR | 0.25 | 3 | 0.137 | 0.294 | 0.284 | 35.3% |
| MMR | 0.25 | 5 | 0.082 | 0.294 | 0.284 | 35.3% |
| MMR | 0.25 | 8 | 0.051 | 0.294 | 0.284 | 35.3% |
| MMR | 0.30 | 3 | 0.118 | 0.265 | 0.265 | 29.4% |
| MMR | 0.30 | 5 | 0.071 | 0.265 | 0.265 | 29.4% |
| MMR | 0.30 | 8 | 0.044 | 0.265 | 0.265 | 29.4% |

### Best candidate by measured title-label metrics
- Mode: MMR
- Threshold: 0.15
- top_k: 8
- Precision@k: 0.110
- Recall@k: 0.490
- MRR: 0.326
- Coverage: 58.8%

### Interpretation and caveats
- This selects a candidate setting, not a production-validated optimum.
- Title phrase matching can miss relevant articles whose current titles differ from historical expected titles.
- Review the expected-title mapping and inspect weak queries before changing production configuration.
- The historical evaluation corpus and current 976-chunk index differ.

## Corrected Document-Level Metrics

Re-evaluated the same 17 queries using unique retrieved article titles.
Precision@k counts retrieved titles matching at least one expected title label, divided by k.
Recall counts expected title labels found among retrieved titles, divided by the number of expected labels.
MRR uses the rank of the first retrieved relevant title. Coverage is the fraction of queries with at least one relevant title.
Labels are title-phrase matches from the historical evaluation; they are not human-judged semantic labels.

| Mode | Threshold | top_k | Precision@k | Recall | MRR | Coverage |
|---|---:|---:|---:|---:|---:|---:|
| Plain | 0.10 | 3 | 0.118 | 0.235 | 0.255 | 29.4% |
| Plain | 0.10 | 5 | 0.094 | 0.324 | 0.267 | 35.3% |
| Plain | 0.10 | 8 | 0.081 | 0.382 | 0.285 | 47.1% |
| Plain | 0.15 | 3 | 0.118 | 0.235 | 0.255 | 29.4% |
| Plain | 0.15 | 5 | 0.094 | 0.324 | 0.267 | 35.3% |
| Plain | 0.15 | 8 | 0.081 | 0.382 | 0.285 | 47.1% |
| Plain | 0.20 | 3 | 0.118 | 0.235 | 0.255 | 29.4% |
| Plain | 0.20 | 5 | 0.094 | 0.324 | 0.267 | 35.3% |
| Plain | 0.20 | 8 | 0.081 | 0.382 | 0.285 | 47.1% |
| Plain | 0.25 | 3 | 0.118 | 0.235 | 0.255 | 29.4% |
| Plain | 0.25 | 5 | 0.082 | 0.294 | 0.267 | 35.3% |
| Plain | 0.25 | 8 | 0.051 | 0.294 | 0.267 | 35.3% |
| Plain | 0.30 | 3 | 0.098 | 0.206 | 0.235 | 23.5% |
| Plain | 0.30 | 5 | 0.071 | 0.265 | 0.247 | 29.4% |
| Plain | 0.30 | 8 | 0.044 | 0.265 | 0.247 | 29.4% |
| MMR | 0.10 | 3 | 0.118 | 0.265 | 0.265 | 29.4% |
| MMR | 0.10 | 5 | 0.106 | 0.343 | 0.306 | 47.1% |
| MMR | 0.10 | 8 | 0.074 | 0.363 | 0.306 | 47.1% |
| MMR | 0.15 | 3 | 0.118 | 0.265 | 0.265 | 29.4% |
| MMR | 0.15 | 5 | 0.106 | 0.343 | 0.309 | 47.1% |
| MMR | 0.15 | 8 | 0.110 | 0.490 | 0.326 | 58.8% |
| MMR | 0.20 | 3 | 0.137 | 0.294 | 0.284 | 35.3% |
| MMR | 0.20 | 5 | 0.129 | 0.392 | 0.325 | 52.9% |
| MMR | 0.20 | 8 | 0.103 | 0.451 | 0.325 | 52.9% |
| MMR | 0.25 | 3 | 0.137 | 0.294 | 0.284 | 35.3% |
| MMR | 0.25 | 5 | 0.082 | 0.294 | 0.284 | 35.3% |
| MMR | 0.25 | 8 | 0.051 | 0.294 | 0.284 | 35.3% |
| MMR | 0.30 | 3 | 0.118 | 0.265 | 0.265 | 29.4% |
| MMR | 0.30 | 5 | 0.071 | 0.265 | 0.265 | 29.4% |
| MMR | 0.30 | 8 | 0.044 | 0.265 | 0.265 | 29.4% |

### Highest-ranked candidate
- Mode: MMR
- Threshold: 0.15
- top_k: 8
- Precision@k: 0.110
- Recall: 0.490
- MRR: 0.326
- Coverage: 58.8%

### Decision
This is a candidate configuration based on title-label metrics, not proof of production quality. Review mismatched titles and the low-relevance queries before changing application defaults.
