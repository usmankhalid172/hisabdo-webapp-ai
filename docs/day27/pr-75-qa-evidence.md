# Day 27 — PR #75 QA Evidence

**QA Assignee:** Syeda Isma Nazir
**Task:** Day 27 — Integration QA & PR Verification
**Pull Request:** PR #75
**QA Branch:** `feature/task27-integration-qa-isma`
**QA Decision:** **APPROVED**
**Date:** 30 August 2026

---

## 1. QA Workflow

The PR was reviewed using the Day 27 QA workflow:

**Fetch → Inspect → Conflict Check → Compile → Tests → Functional Verification → Finding → GitHub Review → Approve/Request Changes → QA Log**

---

## 2. Repository / Branch Verification

The PR was reviewed in the local HisabDo repository.

Working tree status:

```text
On branch qa-pr-75
nothing to commit, working tree clean
```

No unexpected local modifications were present during verification.

---

## 3. Model Artifact Verification

The expected expense categorization model was verified at:

```text
model/expense_categorization_pipeline.pkl
```

The model artifact was successfully found and loaded.

Model type:

```text
sklearn.pipeline.Pipeline
```

The pipeline contains the expense categorization ML workflow.

---

## 4. Training Pipeline Verification

The training implementation was inspected in:

```text
src/expense_categorization/train_model.py
```

The implementation:

* Loads `data/expense_data.csv`.
* Converts description and category fields to strings.
* Splits unique descriptions into training and testing sets.
* Verifies that descriptions do not overlap between the training and testing sets.
* Uses TF-IDF text features.
* Uses Logistic Regression as the classifier.
* Generates predictions and prediction probabilities.
* Applies a confidence threshold of `0.30`.
* Marks low-confidence predictions as `Needs Review`.
* Calculates accuracy, precision, recall and F1-score.
* Saves the trained model to `model/expense_categorization_pipeline.pkl`.

---

## 5. Automated Test Verification

Command executed:

```powershell
python -m pytest -q
```

Result:

```text
81 passed, 4 skipped, 0 failed
```

### Test Status

| Result                  | Count |
| ----------------------- | ----: |
| Passed                  |    81 |
| Failed                  |     0 |
| Skipped                 |     4 |
| Total executed/reported |    85 |

The test suite completed successfully with no failing tests.

---

## 6. Warnings

The test run reported warnings related primarily to:

* NumPy/joblib deprecation behavior.
* A Starlette deprecated HTTP 422 constant.

These warnings did not cause test failures and did not block the PR approval.

---

## 7. Git Ignore Verification

The model artifact is excluded by the repository `.gitignore`:

```text
*.pkl
*.joblib
```

Therefore, the local model being untracked/ignored is expected repository behavior and was **not treated as a QA defect**.

Verification command:

```powershell
git check-ignore -v F:\HisabDo-Capstone\model\expense_categorization_pipeline.pkl
```

Confirmed:

```text
.gitignore:44:*.pkl
```

---

## 8. Functional Verification

The saved model was loaded successfully using Joblib and confirmed to be a scikit-learn Pipeline.

The training script and model artifact are consistent with the expense categorization implementation.

No blocking functional issue was identified during the performed QA validation.

---

## 9. QA Finding

**Finding: PASS**

No blocking defect was identified from the performed local verification.

The automated test suite passed completely, the expected model artifact was available locally, and the expense categorization training pipeline was verified.

---

## 10. GitHub Review Decision

**Decision: APPROVE**

PR #75 was approved based on the completed QA validation.

### Approval rationale

* No failing automated tests.
* Model artifact successfully verified.
* Training pipeline inspected.
* Confidence-based prediction workflow verified.
* No blocking functional issue identified.
* Ignored model artifact behavior is consistent with `.gitignore`.

---

## 11. Evidence Summary

| QA Check                              | Result                        |
| ------------------------------------- | ----------------------------- |
| Repository status                     | PASS                          |
| Model artifact exists                 | PASS                          |
| Model loads successfully              | PASS                          |
| Training pipeline inspected           | PASS                          |
| TF-IDF + Logistic Regression pipeline | PASS                          |
| Confidence threshold workflow         | PASS                          |
| Automated tests                       | **81 PASS / 0 FAIL / 4 SKIP** |
| Git ignore behavior                   | PASS                          |
| Functional verification               | PASS                          |
| Blocking defects                      | None identified               |
| GitHub review                         | **APPROVED**                  |

---

## Final QA Status

**PR #75 — APPROVED / QA PASS**

This evidence is maintained as part of the Day 27 Integration QA & PR Verification deliverables.
