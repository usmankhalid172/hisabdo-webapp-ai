# Department 3 Baseline Comparison Report

Dataset version: 1.0.0
Report version: 1.0.0
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

New dataset model response scores have not yet been measured. Historical numbers above must not be presented as results on the new dataset.

## Limitations

1. The previous set was a small proxy set and was not the original Day 1 failed question list.
2. The knowledge base has only 12 FAQ records and 6 sample financial knowledge records.
3. Some source URLs and updated dates are null.
4. Product workflow and privacy policy approval remain pending in the source audit.
5. No live application response evaluation is claimed in this report.

## Next comparison

Run the same model and retrieval configurations on every question in `data/department3_evaluation_v1.json`. Save raw responses, retrieved record IDs, per dimension scores, total scores, pass rate, abstention behavior and safety failures in a separate versioned results file. Compare approaches only when they use the same dataset version and settings.
