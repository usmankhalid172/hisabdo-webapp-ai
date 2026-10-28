# Retrieval Approach Comparison â€” HisabDo

## 1. Objective

Evaluate retrieval against seven Day 1 failed chatbot questions. Compare
plain TF-IDF retrieval with query rewriting and document relevance.
Avoid presenting unrelated or unsupported content as verified guidance.

## 2. Test Setup

- Knowledge base: `data/faq_docs.json`
- Verified documents in baseline test: 12
- Baseline retriever: `FaqRetriever` in `src/financial_assistant/rag/retriever.py`
- Retrieval method: TF-IDF with cosine similarity
- Existing minimum relevance threshold: 0.12
- Compared result depth: top 3
- Test queries: seven Day 1 failed questions

The threshold of 0.12 is the existing configuration, not a newly
validated optimum. The current experiment does not establish an optimal
threshold or prove that all returned passages are relevant.

## 3. Baseline vs. Query Rewriting

| Day 1 question | Baseline top result | Rewritten top result | Finding |
|---|---|---|---|
| What can I do with HisabDo? | faq-001, 0.3647 | faq-001, 0.7055 | Same relevant overview; score increased. |
| How do I categorize an expense? | finance_003, 0.6912 | finance_003, 0.5713 | Still returns a definition, not categorization steps. |
| What if the predicted category is wrong? | No results | finance_003, 0.6912 | A result appears, but it is unrelated to correcting a prediction. |
| How do I generate a PDF report in HisabDo? | faq-001, 0.3202 | faq-005, 0.6348 | Relevant export guidance moves to rank 1. |
| How can I view my total income and expenses in HisabDo? | finance_002, 0.3366 | faq-001, 0.4350 | App overview is more relevant, but exact viewing steps are missing. |
| How do I add a new customer in HisabDo? | faq-001, 0.3868 | faq-udhar-guidance, 0.2976 | Customer-balance guidance moves to rank 1, but add-customer steps are missing. |
| How do I record a new expense in HisabDo? | finance_003, 0.4840 | finance_003, 0.4840 | No ranking improvement; the result remains a definition. |

Scores are cosine-similarity outputs from the existing retriever.
A higher score is not proof of semantic relevance.

## 4. Findings

### Plain TF-IDF

Plain TF-IDF finds useful overview and export documents, but it can
rank generic finance definitions or unrelated content for procedural
questions. One of the seven original queries returns no results.

### Query rewriting

The manually rewritten queries improve the top-ranked result for the
PDF-report question and improve the ranking for the overview question.
The customer question retrieves related balance guidance, but not the
requested workflow.

Rewriting also exposes a false-positive risk: the wrong-predicted-category
query returns the general expense definition. Retrieval success must
therefore be assessed by relevance, not by whether any result is returned.

### Verified-document filtering

The retriever indexes verified documents only. This is an existing
metadata restriction and should remain enabled. It does not, by itself,
prevent irrelevant results among verified documents.

### Hybrid retrieval, semantic retrieval and reranking

These approaches have not been measured against the same seven-query
test set in this experiment. No performance improvement is claimed for
them. They should be evaluated only if the available dependencies and
time permit a fair comparison.

## 5. Knowledge-Base Coverage Gaps

The inspected verified documents do not provide confirmed, step-by-step
instructions for:

- Correcting an incorrectly predicted expense category.
- Categorizing an expense through the actual app workflow.
- Adding a new customer.
- Recording a new expense.
- Viewing a complete income-and-expense total through exact app screens.

The existing export guidance confirms that PDF reports are supported
for certain records, but it does not specify exact screen-by-screen
steps. Retrieval changes cannot supply missing verified instructions.

## 6. Configuration Decision

- Keep verified-only document filtering enabled.
- Retain the existing threshold of 0.12 as the baseline for now.
- Do not label 0.12 as the experimentally optimal threshold.
- Do not increase `top_k` blindly: additional results can introduce
  unrelated passages into the answer context.
- Apply query rewriting only with relevance checks.
- Reject or suppress unrelated passages rather than passing them to
  answer generation.
- Add verified workflow documentation before claiming that the missing
  procedural questions are solved.

A final threshold and `top_k` selection requires a labeled relevance
assessment across candidate settings. The seven-query comparison above
does not yet provide that complete parameter sweep.

## 7. Evaluation Limitations and Next Steps

This is a small diagnostic set of seven known failures, not a
representative production benchmark. Experiments have been completed
for lexical retrieval, query rewriting, threshold/top-k settings,
metadata-filter comparison, sentence-transformer embeddings, and
Reciprocal Rank Fusion (RRF) hybrid retrieval.

The experiments were inspected by document ID, title, and score.
Only the overview and PDF queries currently have explicit target-document
labels. Five workflow queries still require verified relevance judgments.
Reranking has not been separately benchmarked.

Recommended next steps:

1. Verify relevant, partially relevant, and irrelevant passages for all
   seven questions.
2. Compare original and rewritten queries using the same relevance labels.
3. Validate threshold and top_k against labelled relevance and unrelated
   context, rather than result counts alone.
4. Treat RRF hybrid retrieval and semantic embeddings as experimental;
   current results do not prove overall superiority.
5. Add and verify missing workflow documentation, then rerun the original
   seven questions.
6. Test reranking separately only if a fair, reproducible comparison
   can be performed.

## 8. Conclusion

The experiments show that query rewriting can improve some rankings,
especially for PDF reporting, but does not resolve all Day 1 failures.
The metadata comparison supports retaining verified-only filtering.
Semantic and hybrid experiments still return unrelated content for
some workflow questions. Retain the existing TF-IDF threshold of 0.12
as a provisional baseline, not a proven optimum, and use top_k=1 as a
conservative evaluation starting point. Missing workflow instructions,
incomplete relevance labels, and the absence of a separate reranking
experiment mean the retrieval task is not yet fully validated.

## Measured threshold and top-k sweep

The existing verified-only TF-IDF retriever was tested on all seven rewritten Day 1 queries using thresholds 0.12, 0.20, 0.30, 0.40, 0.50, 0.60, and 0.70, with top_k values 1, 2, and 3. The corpus contained 12 verified documents.

| Threshold | top_k | Queries with results | Total passages | Overview target | PDF target |
|---:|---:|---:|---:|---|---|
| 0.12 | 1 | 7/7 | 7 | Hit | Hit |
| 0.12 | 2 | 7/7 | 13 | Hit | Hit |
| 0.12 | 3 | 7/7 | 18 | Hit | Hit |
| 0.20 | 1 | 7/7 | 7 | Hit | Hit |
| 0.20 | 2 | 7/7 | 12 | Hit | Hit |
| 0.20 | 3 | 7/7 | 15 | Hit | Hit |
| 0.30 | 1 | 6/7 | 6 | Hit | Hit |
| 0.30 | 2 | 6/7 | 9 | Hit | Hit |
| 0.30 | 3 | 6/7 | 10 | Hit | Hit |
| 0.40 | 1 | 6/7 | 6 | Hit | Hit |
| 0.40 | 2 | 6/7 | 7 | Hit | Hit |
| 0.40 | 3 | 6/7 | 7 | Hit | Hit |
| 0.50 | 1 | 4/7 | 4 | Hit | Hit |
| 0.50 | 2 | 4/7 | 4 | Hit | Hit |
| 0.50 | 3 | 4/7 | 4 | Hit | Hit |
| 0.60 | 1 | 3/7 | 3 | Hit | Hit |
| 0.60 | 2 | 3/7 | 3 | Hit | Hit |
| 0.60 | 3 | 3/7 | 3 | Hit | Hit |
| 0.70 | 1 | 1/7 | 1 | Hit | Miss |
| 0.70 | 2 | 1/7 | 1 | Hit | Miss |
| 0.70 | 3 | 1/7 | 1 | Hit | Miss |

### Interpretation and configuration decision

The sweep demonstrates the trade-off between retrieval coverage and the number of passages returned. Thresholds of 0.12 and 0.20 returned passages for all seven queries, while 0.70 filtered out the PDF target. Increasing top_k increased the number of passages at lower thresholds but did not establish improved answer accuracy.

These results do not prove that a single threshold removes all unrelated context. Only the overview and PDF target documents were explicitly labelled for this experiment; results for the other five workflow questions must not be treated as successful answers merely because retrieval returned a passage. Their exact verified instructions remain a knowledge-base coverage gap.

For now, retain the existing production threshold of 0.12 and verified-only document filter rather than promoting an unvalidated threshold. Use top_k=1 as a conservative evaluation baseline, not as a proven optimum. The supporting sweep is saved in `docs/retrieval_parameter_sweep.md`.

This threshold/top-k sweep evaluates the lexical TF-IDF retriever only. Separate experiments for metadata-filter comparison, embedding retrieval, and RRF hybrid retrieval are documented in the sections below. Reranking has not been separately benchmarked, and none of these experiments proves overall superiority.

## Measured metadata-filter comparison

The original Day 1 queries were tested with TF-IDF cosine similarity and top_k=1 across three document sets: 12 verified documents, all 20 documents, and the 4 verified Product Support documents.

| Query | Verified-only top result | All-documents top result | Product Support-only top result |
|---|---|---|---|
| What can I do with HisabDo? | faq-001 (0.3647) | faq-001 (0.3653) | faq-001 (0.3083) |
| How do I categorize an expense? | finance_003 (0.6912) | finance_003 (0.3760) | faq-udhar-guidance (0.0000) |
| What if the predicted category is wrong? | faq-udhar-guidance (0.0000) | faq-udhar-guidance (0.0000) | faq-udhar-guidance (0.0000) |
| How do I generate a PDF report? | faq-001 (0.3202) | faq-001 (0.3223) | faq-001 (0.3644) |
| How can I view total income and expenses? | finance_002 (0.3366) | finance_002 (0.3203) | faq-001 (0.3411) |
| How do I add a new customer? | faq-001 (0.3868) | faq-001 (0.3833) | faq-001 (0.3270) |
| How do I record a new expense? | finance_003 (0.4840) | finance_003 (0.3670) | faq-005 (0.1978) |

Only the overview target was ranked first in this original-query comparison. The PDF target faq-005 was not ranked first in any of the three document sets. The other five questions do not yet have confirmed target passages, so their answer correctness cannot be measured from these results.

### Metadata-filter conclusion

The verified-only filter remains the safer default because it excludes unverified material. Removing the filter did not improve the labelled overview result and reduced several top similarity scores. Restricting retrieval to Product Support changed rankings but did not fix the PDF result and produced zero-score matches for some queries. Therefore, category filtering should only be applied when the query's intent and document metadata support it; it is not a substitute for relevant, verified workflow documentation.

### Evaluation limitations

This metadata-filter comparison uses TF-IDF lexical retrieval. Separate embedding and RRF hybrid experiments are documented below. No reranking experiment has been completed. The available labelled targets are insufficient to claim that the selected threshold is globally optimal or that all seven questions are answered correctly.

## Embedding Retrieval Experiment â€” Original Failed Queries

**Method:** Sentence-transformer embeddings using `sentence-transformers/all-MiniLM-L6-v2`. The experiment loaded 12 verified documents and tested the seven original failed queries without query rewriting.

### Top-ranked results

| Query | Top document | Similarity score | Assessment |
|---|---|---:|---|
| HisabDo overview | faq-001 | 0.5574 | Relevant overview |
| Categorize expense | finance_003 | 0.7122 | Definition, not workflow |
| Wrong predicted category | finance_001 | 0.1035 | Irrelevant result |
| Generate PDF report | faq-005 | 0.6460 | Related export guide |
| View income and expenses | faq-005 | 0.6828 | Export guide; dashboard steps unconfirmed |
| Add customer | faq-001 | 0.3901 | General overview, not customer-creation steps |
| Record expense | faq-005 | 0.7085 | Export guide, not expense-recording steps |

### Measured threshold sweep

| Threshold | Queries with results | Passages returned |
|---:|---:|---:|
| 0.0 | 7/7 | 59 |
| 0.2 | 6/7 | 36 |
| 0.4 | 5/7 | 12 |
| 0.6 | 4/7 | 4 |
| 0.8 | 0/7 | 0 |

### Interpretation and limitations

Embedding retrieval ranked related documents for some queries, but similarity scores alone did not guarantee workflow relevance. In particular, the expense-recording query ranked an export guide first, while the wrong-prediction query returned unrelated finance education content.

A higher threshold reduced the number of returned passages but did not reliably eliminate unrelated context. The results do not establish that any threshold solves all seven queries. Exact workflow coverage is still missing or unverified for expense categorization, correcting predicted categories, viewing totals, adding customers, and recording expenses.

This experiment evaluates embedding retrieval separately. The RRF hybrid and metadata-filter comparisons are documented in their own sections below. No reranking experiment has been completed, and the available labels do not establish that any method improves answer correctness across all seven queries.


## Hybrid Retrieval Experiment â€” Reciprocal Rank Fusion

**Method:** Reciprocal Rank Fusion (RRF), combining the ranks from the existing TF-IDF lexical retriever and sentence-transformer semantic retriever. The experiment used the seven original failed queries and compared each method's top three results.

### Measured comparison

| Query | Lexical top result | Semantic top result | Hybrid top result | Finding |
|---|---|---|---|---|
| HisabDo overview | faq-001 | faq-001 | faq-001 | All methods retrieve the overview |
| Categorize expense | finance_003 | finance_003 | finance_003 | Definition returned, not workflow |
| Wrong prediction | faq-udhar-guidance | finance_001 | finance_008 | No method retrieves a confirmed answer |
| PDF report | faq-001 | faq-005 | faq-001 | All contain faq-005 in top three; semantic ranks it first |
| Income and expenses | finance_002 | faq-005 | faq-001 | Related documents returned; exact dashboard steps unconfirmed |
| Add customer | faq-001 | faq-001 | faq-001 | General overview returned; exact steps unconfirmed |
| Record expense | finance_003 | faq-005 | finance_003 | Definition/export guide returned, not recording steps |

### Interpretation

RRF retained the labelled overview and PDF targets within the top three results for the two queries with confirmed target labels. However, this does not demonstrate an overall improvement: the hybrid ranking did not consistently place the most task-relevant document first, and the other five queries lack confirmed target labels.

The wrong-prediction query still returned unrelated finance education content. The experiment ranks documents but does not independently guarantee relevance or filter all unrelated passages. Therefore, RRF is an evaluated candidate, not a proven production winner.

### Configuration decision

Do not declare a universally optimal similarity threshold or top-k from these experiments. The lexical sweep measures result counts, while embedding retrieval uses a different score scale; their raw thresholds are not directly interchangeable. A defensible final configuration requires labelled relevance judgments for all seven queries, a measured irrelevant-context check, and separate validation of threshold and top-k on the chosen retriever.


## 9. Final Consolidated Results and Provisional Recommendation

This section consolidates the experiments performed after the initial draft. It supersedes earlier statements in this report that described hybrid retrieval and metadata-filter comparison as not yet completed.

### Experiments completed

- Plain TF-IDF retrieval and a threshold/top-k sweep on seven rewritten queries.
- Query-rewriting comparison using the documented original and rewritten query results.
- Verified-only, all-document, and Product Support-only metadata-filter comparison.
- Sentence-transformer embedding retrieval on all seven original failed queries, including a measured threshold sweep.
- Lexical, semantic, and Reciprocal Rank Fusion (RRF) hybrid ranking comparison on the seven original failed queries.

### What the evidence supports

The overview target (`faq-001`) and PDF export target (`faq-005`) appeared in the top three for the lexical, semantic, and hybrid comparisons. However, the hybrid method did not consistently rank the most task-relevant document first. The wrong-prediction query still retrieved unrelated finance education content. The expense categorization and recording queries did not retrieve verified, exact workflow instructions.

The metadata-filter experiment also showed that restricting documents to Product Support alone does not solve missing workflow coverage. A zero lexical similarity score must not be treated as evidence of relevance.

### Provisional configuration

- **Document eligibility:** retain verified-only filtering for the existing knowledge base.
- **Existing TF-IDF baseline:** retain threshold `0.12` for continuity with the current implementation; this is a baseline, not a proven optimum.
- **Initial context size:** use `top_k=1` as a conservative starting point to limit unrelated context, subject to answer-quality validation.
- **Semantic and hybrid retrieval:** keep as experimental candidates; do not replace the production retriever solely on these results.
- **Query rewriting:** use only when the rewritten query and returned passages are checked for relevance.
- **Context filtering:** reject passages that are demonstrably irrelevant before answer generation. The experiments do not yet establish a universally reliable filtering threshold.

The lexical threshold and semantic similarity threshold are on different scoring scales and must not be treated as interchangeable. The measured results show the trade-off between returned passage count and query coverage, but the available relevance labels are insufficient to prove that one configuration answers all seven questions correctly.

### Remaining limitations

Only the overview and PDF queries have explicit target-document labels in the current evaluation. Five workflow queries still require verified relevance judgments and, where documentation is missing, verified product instructions. A separate heuristic reranking experiment has been completed, but it did not demonstrate consistent improvement. Therefore, the evidence supports a documented provisional baseline and continued evaluation, not a claim that every Day 1 failure has been resolved.

## 10. Reranking Experiment

A separate heuristic reranking diagnostic was run on all seven original Day 1 failed queries. It compared the semantic retriever's original order against a query-term-overlap reranker. The experiment and raw output are saved in `docs/reranking_experiment.py` and `docs/reranking_experiment.md`.

### Results

- **Overview:** `faq-001` remained first in both rankings.
- **Categorize expense:** the original top result was `finance_003` ("What is an expense?"). The reranker moved `faq-005` ("How do I export my expenses?") first, which does not establish better relevance.
- **Wrong prediction:** both rankings returned unrelated finance concepts; the reranker did not solve the query.
- **PDF report:** `faq-005` remained first in both rankings.
- **Income and expenses:** the export guide remained first; this does not confirm that it answers the requested dashboard workflow.
- **Add customer:** the reranker moved customer-balance and Khata guidance higher, but neither document provides verified exact customer-creation steps.
- **Record expense:** the export guide remained first, so exact expense-recording instructions remain unverified.

### Reranking decision

The term-overlap heuristic did not demonstrate consistent improvement across the seven queries. It is not a trained cross-encoder and must not be treated as a production reranker. Keep it as a diagnostic only; do not replace the current retriever based on this experiment.

### Updated limitations

Only the overview and PDF export queries have explicit target-document labels. Five workflow queries still need verified relevance judgments and confirmed product instructions where documentation is missing. The current experiments do not prove that unrelated context is completely filtered for every query. Threshold and top-k settings remain provisional until evaluated against labelled relevance and irrelevant-context checks.

## Query Normalization / Rewrite Experiment

A TF-IDF comparison was run for all seven Day 1 queries using the original query and a synonym-expanded query. The same verified document set was used for both rankings.

| Day 1 query | Original top result | Expanded top result | Finding |
|---|---|---|---|
| HisabDo features | faq-001 (0.112) | faq-001 (0.211) | Better lexical score; relevance still needs validation |
| Categorize expense | finance_003 (0.422) | finance_003 (0.465) | Generic expense definition remains first; exact workflow not retrieved |
| Wrong predicted category | finance_007 (0.179) | finance_003 (0.287) | Ranking changes, but neither result confirms correction steps |
| Generate PDF report | faq-005 (0.200) | faq-005 (0.233) | Export guide remains first; PDF workflow must be verified |
| View total income and expenses | faq-001 (0.165) | finance_002 (0.147) | Rewrite does not establish the dashboard workflow |
| Add a customer | faq-005 (0.239) | faq-005 (0.249) | Export guide remains first; customer creation is not answered |
| Record a new expense | faq-005 (0.190) | finance_003 (0.243) | Generic expense definition moves first; workflow remains unanswered |

Scores are TF-IDF cosine similarities from this experiment. They are not probabilities or proof of relevance and must not be compared directly with embedding scores.

### Conclusion and safe retrieval policy

Synonym expansion improves some lexical scores but does not consistently retrieve the correct workflow. It must not be treated as a universal fix. For production use, query rewriting should be evaluated alongside the original query and should only be adopted when it improves judged relevance.

The current verified knowledge base does not provide confirmed, exact instructions for every Day 1 workflow. In particular, the customer-creation, expense-recording, category-correction, and dashboard-total workflows need verified product documentation or human review. Do not label unrelated finance definitions or export instructions as relevant answers. If no relevant verified passage is available after filtering, return no retrieved context and use a safe fallback instead of answering from unrelated material.

This experiment measures ranking changes; it does not establish that all seven queries are correctly answered or that unrelated passages have been completely eliminated.

## Final Production Retrieval Verification

The production retriever was run against all seven original Day 1 queries after adding the conservative query guard.

| Day 1 query | Actual result | Interpretation |
|---|---|---|
| What can I do with HisabDo? | faq-001, score 0.5574 | Product overview retrieved |
| How do I categorize an expense? | No context | Verified workflow instructions unavailable |
| What if the predicted category is wrong? | No context | Verified correction instructions unavailable |
| How do I generate a PDF report in HisabDo? | faq-005, score 0.6460 | Export guide retrieved; exact PDF workflow remains unverified |
| How can I view my total income and expenses in HisabDo? | No context | Verified dashboard instructions unavailable |
| How do I add a new customer in HisabDo? | No context | Verified customer-creation instructions unavailable |
| How do I record a new expense in HisabDo? | No context | Verified expense-entry instructions unavailable |

Production verification returned context for 2 of 7 queries and no context for the other 5. This is a fail-closed safety outcome, not a claim that all seven questions are answerable. The knowledge base needs verified workflow guides before those five queries can retrieve useful instructions.

The existing FAQ retrieval test suite passed 7 tests. The final configuration retains the existing embedding threshold of 0.40; this threshold has not been proven optimal for every query. The lexical parameter sweep and alternative retrieval experiments are documented separately. Similarity scores across different retrieval methods are not directly comparable.

Release limitation: do not claim full workflow coverage until the missing product guides are verified and end-to-end relevance tests pass.
