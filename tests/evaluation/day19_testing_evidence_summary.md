# AI/ML Testing and Evaluation Evidence Summary - Day 19

## Ownership

**Prepared by:** Syeda Isma Nazir  
**Responsibility:** AI/ML Testing and Evaluation  
**Project:** HisabDo AI/ML Capstone  
**Day:** 19

---

## 1. Objective

The objective of Day 19 is to consolidate available AI/ML testing and
evaluation evidence and perform a documentation quality and traceability
review.

The review covers:

- Financial Assistant / chatbot testing evidence
- Smart Expense Categorization evaluation evidence
- API/service/integration testing evidence
- PASS / FAIL / BLOCKED / NOT TESTED status
- Evidence traceability
- Missing testing evidence
- Dependencies preventing testing
- Documentation completeness and consistency

No test is marked PASS unless it was actually executed and evidence or
results are available.

---

## 2. Evidence Reviewed

The following project artifacts were reviewed as part of the Day 19
consolidation:

| Area | Evidence / Artifact | Review Status |
|---|---|---|
| Financial Assistant / Chatbot | `docs/day15-financial-assistant-prompts-and-test-cases.md` | Reviewed |
| Model Evaluation | `docs/model-evaluation-test-plan.md` | Reviewed |
| Smart Expense Categorization | Day 16 evaluation results | Reviewed |
| Integration Flow | `docs/smart_expense_integration_notes.md` | Reviewed |
| Integration Testing | Day 18 integration testing evidence | Reviewed |
| Sample Payloads | `data/expense_category_sample_payloads.json` | Reviewed |
| Expense Dataset | `data/expense_data.csv` | Reviewed |
| ML Components | `src/expense_categorization/` | Reviewed |

---

## 3. Chatbot / Financial Assistant Evidence

### Evidence Available

The repository contains a structured Financial Assistant testing
specification in:

`docs/day15-financial-assistant-prompts-and-test-cases.md`

The document defines:

- Financial user-question categories
- Expected assistant behavior
- 25 functional and safety test cases
- Ambiguous-input scenarios
- Unsupported-question scenarios
- Prompt-injection testing
- Missing-data scenarios
- Budget-related scenarios
- Follow-up and contextual questions
- Expected evaluation criteria

### Testing Status

The chatbot test cases are currently defined as test specifications.
No executable chatbot implementation or actual chatbot response evidence
was identified during the repository review.

**Overall Chatbot Testing Status: NOT TESTED**

### Important Evidence Limitation

The existence of test cases does not constitute execution evidence.

Therefore, chatbot test cases are not marked PASS.

---

## 4. Smart Expense Categorization Evidence

The Day 16 evaluation was previously executed using the corrected
evaluation setup.

### Evaluation Results

| Metric | Result |
|---|---:|
| Accuracy | **78.64%** |
| Precision | **85.92%** |
| Recall | **78.64%** |
| F1-Score | **79.03%** |
| Training Samples | **397** |
| Test Samples | **103** |
| Unique Descriptions | **200** |
| Description Overlap | **0** |

### Evaluation Status

**PASS**

The evaluation used unique expense descriptions for the train/test
split, resulting in zero description overlap between training and testing
sets.

The result is recorded as model evaluation evidence, not as API or
end-to-end integration evidence.

---

## 5. API / Service / Integration Evidence

The documented target integration flow is:

```text
User
  |
  v
HisabDo Application
  |
  v
Backend / API
  |
  v
Expense Categorization AI Service
  |
  v
Preprocessing
  |
  v
ML Model
  |
  v
Validated Response
  |
  v
HisabDo Application
  |
  v
User