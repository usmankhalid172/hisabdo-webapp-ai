# Department 3 Baseline Comparison Report

Dataset version: 1.0.0
Report version: 1.1.0
Prepared: 2026-11-01

## Purpose

This report records the existing retrieval baseline and distinguishes historical results from evaluation of the new Department 3 dataset.

## Historical measured baseline

The existing report `docs/faq_retrieval_approach_comparison.md` describes a proxy evaluation with 20 questions, 16 answerable questions and 4 no answer questions, using 12 FAQ records.

| Existing approach | Historical Hit@1 | Historical Hit@3 |
| --- | ---: | ---: |
| Baseline TF IDF | 68.75% | 93.75% |
| Normalized query | 68.75% | 93.75% |
| Synonym expanded query | 81.25% | 93.75% |
| Expanded query plus reranking | 81.25% | 87.50% |

The existing report states that top k 3 achieved 93.75% baseline Hit rate, compared with 68.75% at top k 1. It also reports that a global product area filter reduced Hit@3 to 50%.

## New Department 3 evaluation set

The new versioned dataset contains 71 questions. It covers common questions, difficult cases, paraphrases, misspellings, Roman Urdu, ambiguity, no answer scenarios and incomplete or overlapping sources.

New dataset retrieval results have now been measured and are recorded below. Full model response scores have not yet been measured. Historical numbers above remain separate.


## New Department 3 measured retrieval baseline

Evaluation dataset: data/department3_evaluation_v1.json
Results file: docs/department3_evaluation_v1_results.json
Evaluation date: 2026-11-01

| Metric | Measured result |
| --- | ---: |
| Total evaluation questions | 71 |
| Knowledge base documents | 12 |
| Answerable cases with supporting sources | 55 |
| No answer or clarification cases | 16 |
| Hit@1 | 89.09% |
| Hit@3 | 96.36% |
| No answer cases that still retrieved a source | 16 of 16 |

The evaluation used TF IDF unigram and bigram retrieval with sublinear term frequency and top 3 ranking.

### Findings

1. The correct supporting source appeared first for 89.09% of answerable cases.
2. The correct supporting source appeared in the top three for 96.36% of answerable cases.
3. All 16 no answer or clarification cases still received a retrieved source. Retrieval alone therefore does not reliably decide when the assistant should abstain or ask for clarification.
4. These results measure source retrieval only. They do not measure generated answer accuracy, citation correctness, completeness, language quality or safety.

### Comparison note

The historical results above use a different 20 question proxy dataset. They must not be treated as a direct before and after comparison with this 71 question evaluation. The new results use the same 12 document count but a separate evaluation script and dataset.

## Limitations

1. The previous set was a small proxy set and was not the original Day 1 failed question list.
2. The knowledge base has only 12 FAQ records and 6 sample financial knowledge records.
3. Some source URLs and updated dates are null.
4. Product workflow and privacy policy approval remain pending in the source audit.
5. No live application response evaluation is claimed in this report.

## Next comparison

Next, evaluate actual assistant responses on every question in `data/department3_evaluation_v1.json`. Save raw responses, retrieved record IDs, per dimension scores, total scores, pass rate, abstention behavior and safety failures in a separate versioned results file. Compare approaches only when they use the same dataset version and settings.
