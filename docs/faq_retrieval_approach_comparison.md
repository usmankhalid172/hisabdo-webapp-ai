# FAQ Retrieval Approach Comparison

## 1. Objective
Evaluate FAQ retrieval approaches against 20 evaluation questions, including 16 answerable questions and 4 questions that should not be answered from the FAQ knowledge base.

The original Day 1 failed-query list was not available during this evaluation. Therefore, these questions are a proxy evaluation set and should not be represented as the exact original Day 1 failures.

## 2. Evaluation Setup
- Knowledge base: 12 FAQ documents from `data/faq_docs.json`.
- Baseline retriever: TF-IDF lexical similarity.
- Existing FAQ retriever threshold: 0.30.
- Baseline retrieval default: top-k = 1.
- Query normalization: text normalization before retrieval.
- Query expansion: lexical synonym expansion.
- Reranking: token and title overlap scoring.
- Metadata experiment: filter documents to `HisabDo` and `HisabDo Privacy` product areas.

This evaluation did not use a semantic embedding model. Query expansion is lexical synonym expansion, not embedding-based semantic retrieval.

## 3. Retrieval Approach Results

| Approach | Hit@1 | Hit@3 |
|---|---:|---:|
| Baseline TF-IDF | 68.75% | 93.75% |
| Normalized query | 68.75% | 93.75% |
| Synonym-expanded query | 81.25% | 93.75% |
| Expanded query + reranking | 81.25% | 87.50% |

Hit@1 measures whether the expected relevant document appears first. Hit@3 measures whether it appears within the first three results.

### Findings
- Query normalization did not improve measured retrieval results on this test set.
- Synonym expansion improved Hit@1 from 68.75% to 81.25%.
- Synonym expansion did not improve Hit@3 over baseline.
- Reranking did not improve Hit@1 and reduced Hit@3 from 93.75% to 87.50%. It should not be enabled by default without further evaluation.

## 4. Top-k Experiment

| Top-k | Baseline Hit Rate |
|---|---:|
| 1 | 68.75% |
| 2 | 81.25% |
| 3 | 93.75% |
| 5 | 93.75% |

Top-k = 3 is the practical candidate because it improved recall over top-k = 1, while top-k = 5 added no measured benefit. Returning more passages can increase irrelevant context, so retrieval results must still be checked for relevance before they are passed to the chatbot.

These top-k results were measured using baseline TF-IDF, not synonym-expanded retrieval.

## 5. Metadata Filtering

The experiment filtered the corpus to documents whose product area was `HisabDo` or `HisabDo Privacy` for every query. Hit@3 fell to 50%, compared with 93.75% for baseline retrieval.

This global filter is too broad because some valid questions concern general financial knowledge. Do not apply this filter to all queries. Future work should use metadata filters only when the query's product area is known reliably, and should include a fallback when filtering removes relevant documents.

## 6. Threshold Sweep

The evaluation script simulated acceptance using the top result score. These are evaluation results, not proof that every threshold is already wired into the production retriever.

### Baseline and normalized retrieval

| Threshold | Answerable coverage | Precision among accepted answerable queries | False accepts among 4 no-answer queries |
|---|---:|---:|---:|
| 0.00 | 100% | 68.75% | 4 |
| 0.10 | 100% | 68.75% | 3 |
| 0.20 | 75% | 83.33% | 1 |
| 0.30 | 56.25% | 88.89% | 0 |
| 0.40 | 50% | 87.50% | 0 |
| 0.50 | 25% | 100% | 0 |

### Synonym-expanded retrieval

| Threshold | Answerable coverage | Precision among accepted answerable queries | False accepts among 4 no-answer queries |
|---|---:|---:|---:|
| 0.00 | 100% | 81.25% | 4 |
| 0.10 | 100% | 81.25% | 3 |
| 0.20 | 81.25% | 100% | 1 |
| 0.30 | 68.75% | 100% | 0 |
| 0.40 | 50% | 100% | 0 |
| 0.50 | 25% | 100% | 0 |

The expanded approach at threshold 0.30 is the best current conservative candidate in this small proxy set: 68.75% answerable coverage, 100% precision among accepted answerable queries, and zero false accepts among four no-answer queries. These results are based on a small test set and require validation against the original Day 1 failures.

The reranked threshold sweep behaved less reliably: at threshold 0.30 it had 75% answerable coverage but two false accepts among the four no-answer queries. This reinforces the decision not to use the current reranker by default.

## 7. Recommended Candidate Configuration

- Retrieval method: TF-IDF with synonym expansion.
- Candidate threshold: 0.30, subject to production-path verification.
- Candidate top-k: 3, subject to relevance filtering before constructing chatbot context.
- Reranking: disabled by default until it demonstrates consistent improvement.
- Metadata filtering: apply only when a query-specific filter is reliable; do not globally restrict the corpus to HisabDo product areas.
- No-answer handling: reject unrelated or low-confidence retrieval results rather than placing them into the model context.

The threshold and top-k recommendations are provisional. Similarity scores depend on the retriever implementation, and threshold behavior must be tested against the actual production retrieval path.

## 8. Limitations and Follow-up Work

1. The exact Day 1 failed-query list was not available. Obtain it and rerun the same evaluation before claiming that every original failed question is fixed.
2. The corpus contains only 12 documents, and the evaluation set contains 20 questions. Results may change with a larger and more representative dataset.
3. No true semantic embedding retrieval or lexical-semantic hybrid system was measured. Implement and evaluate one before making claims about semantic retrieval.
4. The current metadata experiment uses a broad static filter, not a validated query-aware metadata strategy.
5. The reranker reduced Hit@3, so it requires changes and a fresh held-out evaluation before use.
6. Add per-query outputs showing expected document, retrieved ranks, similarity scores, acceptance/rejection, and whether unrelated passages entered the final context.
7. Validate the chosen threshold in the production FAQ retriever and add automated tests for answerable, unrelated, and out-of-scope questions.

## 9. Conclusion

On the current 20-question proxy evaluation, synonym-expanded TF-IDF achieved the best measured Hit@1 result (81.25%). Baseline top-k = 3 achieved 93.75% Hit@3, while top-k = 5 offered no additional benefit. The broad metadata filter and current reranker reduced retrieval quality in their measured experiments.

The provisional recommendation is synonym-expanded TF-IDF, threshold 0.30, and top-k 3, with strict relevance checks and no-answer handling. This is an evidence-based candidate for further validation, not proof that all Day 1 failures have been resolved.
