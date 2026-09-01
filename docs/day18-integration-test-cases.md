# Day 18 – Integration Test Cases & Expected Results

**Prepared by:** Rimsha Mushtaq
**Workstream:** Smart Expense Categorization
**Responsibility:** Integration Test Cases & Expected Results

## 1. Objective

The purpose of this document is to define integration test cases for the Smart Expense Categorization service flow.

The target flow is:

**User → HisabDo App → Backend/API → AI Service → Model → Validated Response → User**

The tests cover valid, invalid, ambiguous, and edge-case transaction inputs.

## 2. Test Cases

| Test ID | Input                                 | Type      | Expected Result                          | Status     |
| ------- | ------------------------------------- | --------- | ---------------------------------------- | ---------- |
| TC-01   | Bought vegetables from grocery store  | Valid     | Groceries                                | NOT TESTED |
| TC-02   | Paid electricity bill                 | Valid     | Utilities                                | NOT TESTED |
| TC-03   | Had lunch at a restaurant             | Valid     | Food                                     | NOT TESTED |
| TC-04   | Paid university tuition fee           | Valid     | Education                                | NOT TESTED |
| TC-05   | Bought medicine from pharmacy         | Valid     | Healthcare                               | NOT TESTED |
| TC-06   | Uber ride to work                     | Valid     | Transport                                | NOT TESTED |
| TC-07   | Bought a new shirt online             | Valid     | Shopping                                 | NOT TESTED |
| TC-08   | Movie theater ticket                  | Valid     | Entertainment                            | NOT TESTED |
| TC-09   | Paid internet bill                    | Valid     | Bills                                    | NOT TESTED |
| TC-10   | Payment for electricity and groceries | Ambiguous | Review/flag ambiguous input              | NOT TESTED |
| TC-11   | Apple                                 | Ambiguous | Review/flag ambiguous input              | NOT TESTED |
| TC-12   | Spotify subscription                  | Ambiguous | Entertainment                            | NOT TESTED |
| TC-13   | 123456789                             | Edge Case | Validation/error or no reliable category | NOT TESTED |
| TC-14   | xyz random payment                    | Edge Case | Validation/error or no reliable category | NOT TESTED |
| TC-15   | !!!                                   | Edge Case | Validation/error or no reliable category | NOT TESTED |
| TC-16   | Empty input                           | Invalid   | Validation/error response                | NOT TESTED |

## 3. Expected vs Actual Results

Actual results will be recorded only after the complete API/service integration is available and the test cases are executed through the integration flow.

| Test ID | Expected Result  | Actual Result | Status     | Notes                                 |
| ------- | ---------------- | ------------- | ---------- | ------------------------------------- |
| TC-01   | Groceries        | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-02   | Utilities        | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-03   | Food             | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-04   | Education        | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-05   | Healthcare       | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-06   | Transport        | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-07   | Shopping         | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-08   | Entertainment    | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-09   | Bills            | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-10   | Ambiguous/review | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-11   | Ambiguous/review | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-12   | Entertainment    | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-13   | Validation/error | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-14   | Validation/error | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-15   | Validation/error | —             | NOT TESTED | Integration endpoint not yet verified |
| TC-16   | Validation/error | —             | NOT TESTED | Integration endpoint not yet verified |

## 4. Dependency and Blocker Status

The Day 18 integration tests require the Smart Expense Categorization API/service endpoint to be available and connected to the trained model.

The model-level predictions were evaluated during Day 17, but those predictions do not by themselves prove that the complete application integration flow works.

Therefore, integration-level results will remain **NOT TESTED** until the required API/service integration is available.

## 5. Error Handling

Incorrect or unexpected responses will be recorded with:

* Input description
* Expected category/result
* Actual response
* Status code where applicable
* Predicted category
* Likely cause
* Recommended improvement

## 6. Security and Data Considerations

Only non-sensitive sample transaction descriptions will be used for testing.

No passwords, API keys, personal financial information, or other secrets should be included in test evidence.

## 7. Evidence

Evidence for completed integration testing will include:

* API request/response output
* Screenshots where applicable
* Expected vs actual results
* PASS/FAIL results
* Error-analysis notes
* GitHub commit and Pull Request

## 8. Current Progress

**Completed:**

* Defined valid integration test cases.
* Defined ambiguous test cases.
* Defined invalid and edge-case test cases.
* Defined expected results.
* Prepared expected-vs-actual result tracking.

**Remaining:**

* Execute the test cases through the integrated API/service.
* Record actual responses.
* Mark each executed test as PASS or FAIL.
* Record incorrect responses and perform error analysis.

**Current blocker:**

* Complete API/service integration has not yet been verified for these tests.

**Current status:** Documentation and test-case preparation completed; integration execution is pending.
## 9. Integration Availability Check

The repository was checked for the application-facing AI integration service.

The `src/integration/` directory currently contains only `README.md`, which describes the intended integration layer and mentions FastAPI service, request/response schemas, validation, error handling, orchestration, and application-facing endpoints.

No executable integration API endpoint or service implementation was available in this branch at the time of testing.

### Verification Evidence

**Checked directory:**

`src/integration/`

**Available file:**

`src/integration/README.md`

**Executable integration endpoint:** Not available

**Integration execution status:** BLOCKED / NOT TESTED

### Reason

The integration test cases require an application-facing API/service endpoint through which requests can be submitted and responses received.

The existing Day 17 model-level evaluation provides model prediction evidence, but it does not demonstrate the complete:

**User → HisabDo App → Backend/API → AI Service → Model → Validated Response → User**

integration flow.

Therefore, integration-level PASS/FAIL results are not reported until the required service endpoint is available.

### Next Required Dependency

Once the integration service/API is available, the test cases in this document should be executed and the following should be recorded:

* Actual response
* HTTP status code
* Predicted category
* Expected category
* PASS/FAIL status
* Incorrect response and likely cause
* Screenshot/API output as evidence
