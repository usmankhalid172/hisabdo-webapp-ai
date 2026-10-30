# Department 3 — Chatbot Evaluation

**Project:** HisabDo Expense Management Chatbot  
**Department:** Department 3 — Expense Management  
**Evaluation Set Version:** 1.0  
**Status:** Draft — Full Evaluation Pending

## 1. Purpose

This directory contains the evaluation materials for assessing the HisabDo Expense Management Chatbot.

The evaluation focuses on factual accuracy, knowledge retrieval, response quality, multilingual understanding, citation correctness, and safe handling of financial and personal information.

## 2. Evaluation Deliverables

| File | Description |
|---|---|
| `department3_evaluation_set_v1.0.csv` | 60 representative test questions, expected answer points, and supporting source record IDs |
| `scoring_rubric_v1.0.md` | Standardized scoring criteria and evaluation procedure |
| `baseline_comparison_report_v1.0.md` | Previous exploratory results, targeted retrieval improvement, and outstanding limitations |

## 3. Evaluation Coverage

The evaluation dataset covers:

- HisabDo app basics
- Khata, Udhar, receivables, and payables
- PDF reports and export questions
- Basic accounting concepts
- Expense management and categorization
- Privacy, security, and chatbot safety

It also includes different question styles, misspellings, Roman Urdu and English queries, ambiguous questions, no-answer scenarios, and conflicting-source cases.

## 4. Data Safety

- No real customer financial records are included.
- No real phone numbers, email addresses, or private contact details are included.
- Synthetic values may be used where a test requires an example.
- Unverified knowledge-base records must not be treated as authoritative evidence.
- Account-specific questions must not be answered using invented financial information.

## 5. Evaluation Method

Each chatbot response will be assessed using the seven scoring dimensions defined in `scoring_rubric_v1.0.md`:

1. Factual accuracy
2. Relevance
3. Completeness
4. Citation correctness
5. Clarity
6. Language
7. Safety

The maximum score is 28 points per question.

## 6. Baseline and Improvement Tracking

The baseline report records previous exploratory testing and targeted retrieval checks.

The 60-question evaluation has not yet been fully executed. Therefore, no overall accuracy percentage or final performance improvement is claimed.

## 7. Versioning

| Version | Description |
|---|---|
| 1.0 | Initial Department 3 evaluation dataset, scoring rubric, and baseline report draft |

Changes to questions, expected answers, supporting source records, or scoring criteria should be documented in a new version.