# Department 3 — Baseline Comparison Report

**Project:** HisabDo Expense Management Chatbot  
**Department:** Department 3 — Expense Management  
**Report Version:** 1.1  
**Status:** Preliminary - Retrieval Evaluation Completed; Chatbot Response Evaluation Pending

## 1. Purpose

This report summarizes previous exploratory testing, identified chatbot limitations, and targeted retrieval improvements for the HisabDo Expense Management Chatbot.

The report provides preliminary evidence for the Department 3 evaluation. It is not a final benchmark of the 60-question evaluation dataset.

## 2. Previous Exploratory Baseline

An earlier exploratory evaluation covered 19 questions.

| Result | Questions | Observation |
|---|---:|---|
| Clear passes | 11 | Basic app information and accounting questions were answered correctly. |
| Retrieval issues | 6 | Some questions retrieved unrelated records or failed to retrieve relevant information. |
| Partial response | 1 | A PDF/customer-balance response lacked sufficient confirmation and citation. |
| Backend limitation | 1 | An account-specific query could not be completed because the authenticated financial backend was unavailable. |
| **Total** | **19** | |

## 3. Issues Identified

The exploratory evaluation identified these limitations:

1. Payable and receivable questions sometimes retrieved unrelated financial information.
2. Some misspelled customer-balance queries did not retrieve the appropriate knowledge-base record.
3. Expense categorization questions lacked verified workflow information.
4. Some PDF-related responses lacked sufficient supporting citations.
5. Account-specific financial queries depended on authenticated backend availability.

## 4. Targeted Retrieval Improvement

A targeted retrieval adjustment was introduced in `src/financial_assistant/faq_rag.py`.

The adjustment added payable and receivable query detection and targeted retrieval of the `faq-udhar-guidance` record.

### Live Test Results

| Test Question | Observed Result |
|---|---|
| What does payable mean in a business? | Retrieved `faq-udhar-guidance`. |
| What does receivable mean in accounting? | Retrieved `faq-udhar-guidance`. |
| Difference between payable and receivable? | Retrieved `faq-udhar-guidance`. |
| Kis customer ne kitne paise dene hain? | Retrieved `faq-udhar-guidance`. |
| Expense categorization question | Returned a safe no-match response. |

The four payable/receivable checks demonstrated improved retrieval for those specific queries.

The expense categorization no-match response was appropriate because the available categorization guidance was unverified.

## 5. Automated Test Evidence

| Test Evidence | Result |
|---|---:|
| Focused FAQ and chatbot test suite | 16 passed |
| Warnings | 2 |
| Earlier broader test-suite result | 351 passed, 4 skipped |

The broader test-suite result is historical evidence. It must not be presented as a current full-suite result without rerunning the tests.

## 6. Comparison Summary

| Evaluation Area | Earlier Observation | Later Targeted Check |
|---|---|---|
| Payable retrieval | Some unrelated retrieval issues | Relevant guidance retrieved |
| Receivable retrieval | Some unrelated retrieval issues | Relevant guidance retrieved |
| Roman Urdu Udhar query | Retrieval inconsistency | Relevant guidance retrieved in the tested query |
| Expense categorization | Unverified workflow information | Safe no-match response |
| Account-specific financial data | Authenticated backend limitation | No new backend capability established |

## 7. Remaining Limitations

The following work is pending:

- Complete authenticated chatbot response evaluation for all 60 questions.
- Record and score actual chatbot responses when authorized backend authentication becomes available.
- Score each response using the seven-dimension scoring rubric.
- Evaluate English and Roman Urdu response quality.
- Evaluate actual chatbot responses to misspellings, ambiguous queries and conflicting-source scenarios.
- Perform privacy and safety regression checks.
- Re-run the relevant automated tests before final submission.
- Calculate actual evaluation percentages and compare results.

## 8. Interpretation of Results

The targeted retrieval checks provide evidence of improvement in four specific payable and receivable queries.

However:

- These checks do not establish overall chatbot accuracy.
- The 16 passing automated tests are not equivalent to 16 successful evaluation questions.
- The historical 351-pass result is not a current benchmark.
- No complete before-and-after accuracy percentage is available yet.

## 9. Conclusion

The targeted retrieval adjustment improved the tested payable and receivable queries by directing them to the relevant verified Udhar guidance record.

The chatbot also demonstrated safe abstention for the tested expense categorization query, where verified workflow information was unavailable.

The Department 3 evaluation is still preliminary. A final performance assessment requires execution and scoring of the complete 60-question dataset.


## 10. Version 1.1 - 60-Question Retrieval Evaluation

The 60-question evaluation dataset was executed against the local verified knowledge-base retriever using `FaqRetriever`.

**Results file:** `docs/evaluation/retrieval_results_v1.0.csv`

| Retrieval result | Questions | Interpretation |
|---|---:|---|
| Expected source matched | 30 | At least one expected source ID was retrieved. |
| Expected source missed | 11 | No expected source ID was retrieved. |
| No source retrieved for unverified/no-source cases | 13 | Retrieval returned no documents; this is a retrieval-level abstention indicator, not proof of chatbot response behaviour. |
| Manual review required | 6 | Documents were retrieved for questions without an approved verified source. |
| **Total** | **60** | |

Among the 41 questions with verified expected sources, 30 retrieved at least one expected source. This represents a **73.17% expected-source match rate** for this retrieval run. It is not chatbot answer accuracy or a complete citation correctness score.

## 11. Retrieval Findings and Cases for Review

The 11 verified-source misses were:

- D3-003, D3-007, D3-008, D3-016, D3-018, D3-019, D3-020
- D3-025, D3-027, D3-036, D3-040

Some misses involve spelling variations, Roman Urdu, or broad questions. Others involve related information being retrieved under a different source ID. These cases require manual relevance review before being treated as definite content failures.

The six unverified/no-verified-source cases requiring review were:

- D3-042, D3-046, D3-047, D3-050, D3-056, D3-057

D3-056 asks for an official support phone number, for which no verified source is available. D3-057 requests another customer's outstanding balance. Retrieving general Udhar guidance does not authorize disclosure of another person's financial information. The expected safe behaviour is to refuse that disclosure.

## 12. Automated Test Evidence - Current Run

The focused command `python -m pytest tests/test_faq_rag.py -q` completed with:

- 7 passed
- 0 failed
- 2 dependency/configuration deprecation warnings

These seven automated tests are separate from the 60-question retrieval evaluation.

## 13. Evaluation Limitations and Remaining Work

The retrieval evaluation records source matching only. It does not generate or score chatbot replies.

The authenticated chatbot endpoint requires `X-Internal-Token` and `X-Authenticated-User-ID`. No `.env` file or `INTERNAL_SERVICE_TOKEN` environment variable was available during this evaluation. The configured default in `src/config.py` is a development placeholder and was not treated as production authentication.

Therefore, the following remain pending:

- Authorized authenticated chatbot testing across the 60 questions.
- Scoring actual responses against the seven-dimension rubric.
- Manual review of all source mismatches and unverified-source cases.
- Final response accuracy, safety, language, and citation scores.
- Final before-and-after chatbot performance comparison.

No chatbot accuracy percentage is claimed in this report.

## 14. Version History

| Version | Description |
|---|---|
| 1.0 | Initial preliminary baseline report based on exploratory testing and targeted retrieval checks. |
| 1.1 | Added results from the 60-question retrieval evaluation, current focused test evidence, reviewed cases, and authentication limitations. |


