# Day 16 — Product Guidance and PDF Verification

## 1\. Objective

Prepare practical guidance for HisabDo Expenses, Income, Khata, Udhar,
and Reports. Review the available repository documentation and define
English, Urdu, and Roman Urdu test cases.

## 2\. Verification limitations

The actual HisabDo application is not accessible for this task.
Therefore, UI workflows, saved records, and PDF downloads cannot be
verified directly.

Evidence reviewed:

* data/faq\_docs.json
* tests/test\_chatbot.py
* tests/evaluation/test\_cases.md
* tests/xictek\_website\_assistant/test\_multilingual.py

The existing multilingual tests target the XICTEK website assistant.
They do not establish multilingual coverage for HisabDo.

## 3\. Product guidance verification matrix

|Feature|Guidance / check required|Current status|
|-|-|-|
|Expenses|Record an expense; verify amount, date, and category|NOT TESTED|
|Income|Record income; verify amount, date, and saved record|NOT TESTED|
|Khata|Check how account/customer records are created and updated|NOT VERIFIED|
|Udhar|Check how credit/debt is recorded and balances are updated|NOT VERIFIED|
|Reports|Check report filters, displayed totals, and export options|PARTIALLY DOCUMENTED|
|PDF export|Export a report and open the downloaded PDF|BLOCKED|
|CSV export|Export a report and inspect the downloaded CSV|BLOCKED|

Note: The existing FAQ says users can export expense reports as CSV or
PDF and filter by date range, category, or tag. This claim has not been
confirmed in the actual application.

## 4\. Practical guidance — pending product verification

### Expenses

Expected workflow to verify: open Expenses, add a record, enter its
details, save it, and confirm that the record appears correctly.

### Income

Expected workflow to verify: open Income, add an income record, save it,
and confirm that the amount and date are displayed correctly.

### Khata

Verify the actual workflow for creating or opening a Khata/account,
recording a transaction, and checking the updated balance. Exact UI steps
are unknown until the application is accessible.

### Udhar

Verify how a credit/debt transaction is recorded, how repayment is
entered if supported, and whether the displayed outstanding amount is
correct. Do not assume these functions exist without evidence.

### Reports and PDF

The repository FAQ describes report filters and CSV/PDF export.
Once application access is available, select a date range, inspect the
report, export PDF, open the file, and compare its totals with the report.
Until then, PDF export remains BLOCKED.

## 5\. Multilingual test cases

|ID|Feature|Language|Test input|Expected result|Status|
|-|-|-|-|-|-|
|D16-L01|Expenses guidance|English|How do I add an expense?|Clear, relevant guidance without invented UI steps|NOT TESTED|
|D16-L02|Expenses guidance|Urdu|میں خرچہ کیسے شامل کروں؟|Relevant answer in Urdu|NOT TESTED|
|D16-L03|Expenses guidance|Roman Urdu|Expense kaisay add karun?|Relevant answer in Roman Urdu|NOT TESTED|
|D16-L04|Income guidance|English|How do I record income?|Clear, relevant guidance|NOT TESTED|
|D16-L05|Khata guidance|Urdu|کھاتہ کیسے بناؤں؟|Relevant answer or honest clarification|NOT TESTED|
|D16-L06|Udhar guidance|Roman Urdu|Udhar ki entry kaisay karun?|Relevant answer or honest clarification|NOT TESTED|
|D16-L07|Reports|English|How can I export a PDF report?|Answer must match verified product evidence|NOT TESTED|
|D16-L08|Reports|Roman Urdu|Report PDF mein kaisay download karun?|Answer must match verified product evidence|NOT TESTED|
|D16-L09|Reports|Urdu|رپورٹ پی ڈی ایف میں کیسے ڈاؤن لوڈ کروں؟|Answer must match verified product evidence|NOT TESTED|
|D16-L10|Unknown feature|Roman Urdu|Kya Khata mein automatic reminder hai?|Do not invent an unsupported feature|NOT TESTED|

## 6\. Result definitions

PASS: The observed result matches the expected result.
FAIL: The observed result does not match the expected result.
BLOCKED: Execution cannot proceed because a required app or dependency
is unavailable.
NOT TESTED: The test is documented but has not been executed.
NOT VERIFIED: Available evidence is insufficient to confirm the claim.

## 7\. Day 16 status

Repository documentation reviewed: DONE.
Initial guidance and multilingual test plan: DOCUMENTED.
Actual Expenses, Income, Khata, and Udhar workflows: NOT VERIFIED.
Actual PDF/CSV export: BLOCKED — application access unavailable.
HisabDo-specific multilingual execution: NOT TESTED.

## 8\. Next actions

1. Obtain access to the actual HisabDo application.
2. Execute each workflow using fictional test data.
3. Record actual results and capture screenshots where possible.
4. Update each status based on observed evidence.
5. Run relevant existing automated tests and record their output.

\## 9. Automated Test Execution Results



Command executed:



`python -m pytest tests/test\_chatbot.py tests/test\_categorization.py tests/test\_intent\_router.py -q`



Observed result: \*\*29 passed in 0.34s\*\*



Status: PASS — all tests in the selected test modules passed.



Coverage reviewed:

\- Chatbot tests

\- Expense categorization tests

\- Intent router tests



Multilingual coverage limitation:

\- Existing `tests/xictek\_website\_assistant/test\_multilingual.py` checks English, Urdu, Roman Urdu, Hindi, and Arabic handling for the XICTEK website assistant.

\- These tests do not verify multilingual responses for HisabDo product guidance.

\- HisabDo-specific multilingual cases D16-L01 to D16-L10 remain NOT TESTED.

\- Actual application workflows and PDF/CSV downloads remain NOT VERIFIED or BLOCKED because application access is unavailable.



\## 10. Updated Day 16 Summary



\- Repository review: DONE

\- Product guidance and test plan: DOCUMENTED

\- Selected automated tests: PASS (29 passed)

\- Actual Expenses, Income, Khata, and Udhar workflows: NOT VERIFIED

\- Actual PDF/CSV export: BLOCKED

\- HisabDo-specific multilingual execution: NOT TESTED

