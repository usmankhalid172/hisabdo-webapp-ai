# Department 3 Final Defect Closure Report

Date: 17 November 2026
Project: HisabDo AI Financial Assistant

## 1. Summary

The Department 3 defect review addressed retrieval routing, citation completeness, and prompt rule consistency. Automated validation completed successfully.

Final test result: 346 passed, 4 skipped, 1 warning.

Release status: NOT CLEARED.

## 2. Defect Register

### D3 REG 001: Expense export routing

Severity: High
Status: FIXED

Problem:
Procedural questions such as "How do I export my expenses?" were incorrectly classified as requests for the user's personal financial figures.

Resolution:
Added an exclusion for procedural export and download questions in the own financial data query detector.

Validation:
Three procedural export examples added as regression cases. Integration assertions verify that the request follows the RAG path instead of the financial backend path.

### D3 REG 002: Cash flow citation completeness

Severity: Medium
Status: FIXED, TESTED

Problem:
The citation matching check could reject a relevant source when the generated response contained several topics.

Resolution:
Adjusted the lexical overlap calculation to compare matched reply words against the meaningful words in the individual source.

Evidence:
The current evaluation case identifies faq-004, faq-006, and finance_004 as supporting records for the cash flow statement question. A new handle_chat regression test verifies that finance_004 appears in the response citations.

### D3 REG 003: Missing source URLs

Severity: Medium
Status: OPEN, BLOCKED BY SOURCE APPROVAL

Finding:
All 12 records in the current FAQ and financial knowledge dataset have missing source URLs.

Resolution:
No URLs were invented or added. Approved source URLs must be supplied by the responsible content owners before this defect can close.

## 3. Additional Cleanup

A duplicate hidden system prompt pattern was found in the prompt injection rules. The duplicate entry was removed and its count was verified as one.

## 4. Validation Evidence

Focused regression suite:
50 passed, 1 warning.

Full automated test suite:
346 passed, 4 skipped, 1 warning, 10.53 seconds.

These results establish local automated test success. They do not establish production readiness.

## 5. Remaining Release Blockers

1. Approved source URLs and content ownership remain pending.
2. Hybrid retrieval is not active in the API runtime.
3. Dense embedding retrieval has not been measured in the active runtime.
4. Production financial backend contract and live integration tests remain unverified.
5. Production LLM provider configuration remains unvalidated. The default provider is mock.
6. Real customer session isolation and concurrent account boundary tests remain unproven.
7. Full Day 1 golden dataset has not been manually validated through the integrated API.

## 6. Closure Decision

D3 REG 001 and D3 REG 002 are closed based on the recorded regression tests. The duplicate prompt rule cleanup is verified. D3 REG 003 remains open.

Department 3 is not cleared for production deployment. Production approval requires closure of the listed blockers and review by the responsible owners.
