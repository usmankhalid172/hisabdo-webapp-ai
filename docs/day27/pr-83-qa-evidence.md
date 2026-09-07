# PR #83 QA Evidence — Day 27 End-to-End Workflow Testing

## PR Information

- PR: #83 — Feature/task27 workflow testing Joyce
- Author: hanyjoyce28-arch
- Source branch: `feature/task27-workflow-testing-joyce`
- Reviewed commit: `f096fe28cb087a77f64b6e6d8c8706a17cc1acdd`
- QA branch: `feature/task27-integration-qa-isma`
- Review date: 2026-09-05
- Test environment: Local FastAPI application
- Python environment: Project `.venv`

## Repository Verification

| Check | Result |
|---|---|
| PR branch vs `main` merge-tree | PASS — no merge conflicts reported |
| Changed files | 2 documentation files |
| Diff | 67 additions, 0 deletions |
| `git diff --check origin/main...HEAD` | PASS |

## API Authentication

The categorization and chatbot endpoints require the `X-Internal-Token` header. Tests were executed using the project's development token configured for the local environment.

## Executed QA Tests

### 1. Health Endpoint

**Request:** `GET /api/v1/health`

**Actual result:** `status: ok`

**Result:** PASS

### 2. Version Endpoint

**Request:** `GET /api/v1/version`

**Actual result:**
- service: `hisabdo-ai-service`
- version: `0.1.0-poc`
- model_provider: `mock`

**Result:** PASS

### 3. Valid Expense Categorization

**Input:** `Bought groceries from Imtiaz`, amount `2500`, merchant `Imtiaz`, currency `PKR`

**Actual result:**
- category: `Groceries`
- confidence: `0.95`
- method: `rule_based`
- needs_confirmation: `False`

**Result:** PASS

### 4. Empty Description Validation

**Input:** Empty description with amount `2500`

**Actual result:** API returned `VALIDATION_ERROR` with `string_too_short`; description requires at least one character.

**Result:** PASS

### 5. Negative Amount Validation

**Input:** `Test expense`, amount `-500`, merchant `Test`, currency `PKR`

**Expected:** Request rejected because the amount is invalid.

**Actual result:** Request was accepted and returned:
- category: `Transport`
- confidence: `0.1286`
- method: `ml_model`
- needs_confirmation: `True`

**Result:** FAIL

**Finding:** PR #83 reports the negative-amount test as PASS with validation rejection, but independent reproduction shows that negative amounts are currently accepted by the API.

The existing `CategorizeRequest` schema defines `amount` as `float` without a positive-value constraint, and the categorization service does not independently reject negative amounts.

### 6. Chatbot Workflow

**Input:** `How much did I spend on food?`

**Actual result:**
- valid reply returned
- conversation_id: `qa-pr83-test`
- intent: `own_financial_data`
- tokens_used: `31`
- source: `backend_financial_api`

**Result:** PASS

### 7. Category Taxonomy Checks

#### Food-style expense

**Input:** `Dinner at a restaurant`

**Actual category:** `Dining`

**Result:** PASS — categorization works, but the actual taxonomy is `Dining`, not `Food`.

#### Healthcare-style expense

**Input:** `Bought medicine from pharmacy`

**Actual category:** `Health`

**Result:** PASS — categorization works, but the actual taxonomy is `Health`, not `Healthcare`.

#### Transport

**Input:** `Paid for taxi ride`

**Actual category:** `Transport`

**Result:** PASS

## Automated Test Suite

The command:

`python -m pytest -q`

returned no test output in the local environment, so the full automated suite is **not counted as a successful test result**.

## QA Findings

1. **Negative amount validation is incorrectly documented as PASS in PR #83.** The live API accepted `amount: -500`.
2. The PR's category test labels `Food` and `Healthcare` do not match the actual categories observed during independent testing (`Dining` and `Health`).
3. The statement that no new issues were identified is not supported because the negative-amount behavior was reproduced.
4. The PR should be updated to accurately document actual request/response results and the negative-amount validation status.

## QA Conclusion

**PR #83 requires changes before approval.**

The health, version, valid categorization, empty-description validation, chatbot, and transport workflows were successfully reproduced. However, the documented negative-amount validation result is incorrect and represents a reproducible API validation gap.

The PR should correct the test report and bug log before re-review.
