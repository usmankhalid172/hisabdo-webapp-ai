# Department 3 — Verified Multi-Turn Conversation Transcripts

**Project:** HisabDo
**Review date:** 2026-11-13

## Important note
The following are synthetic, test-backed examples based on the existing transaction intent-router tests. They are not real customer conversations or real financial records.

## Transcript 1 — Expense with missing description

**User:** Add an expense of 500 PKR.

**Assistant:** Please describe the transaction.

**User:** groceries.

**Assistant:** I have the expense details: 500 PKR for groceries. This is not saved yet; transaction saving is not enabled in this chatbot flow.

**Verification:** Covered by `test_follow_up_collects_missing_description` in `tests/test_intent_router.py`.

## Transcript 2 — Expense with missing amount

**User:** Add expense for groceries.

**Assistant:** What was the amount?

**User:** 500

**Assistant:** The collected details include 500 PKR for groceries.

**Verification:** Covered by `test_follow_up_collects_missing_amount` in `tests/test_intent_router.py`.

**Note:** The test verifies the amount and description in the response. The implementation explicitly states that transaction saving is not enabled.

## Transcript 3 — Unrelated message

**User:** How do I use HisabDo?

**Assistant:** The transaction intent handler does not start a transaction for this unrelated message when there is no pending transaction.

**Verification:** Covered by `test_unrelated_message_does_not_start_transaction`.

## Transcript 4 — Product FAQ flow

**User:** How do I categorize an expense?

**Assistant:** The chatbot uses the FAQ retrieval flow for product-help questions.

**Verification:** The focused chatbot suite passed and includes product FAQ/RAG coverage. This transcript is a flow summary, not a verbatim captured model response.

## 5. Unverified conversation journeys

The following are not claimed as fully verified by the recorded tests:
- Multi-turn budget summaries and period changes.
- Follow-up questions across every financial-report type.
- Live production account-level queries.
- Actual human-support handoff through a verified contact channel.
- Live transaction saving.

## 6. Verification summary

The expense follow-up examples are backed by passing intent-router tests. Product FAQ/RAG behavior is covered by the focused chatbot test suite. No live user data or production transaction was used to produce these examples.

## 7. Additional FAQ follow-up verification — 2026-11-13

The following retrieval-context behaviors are covered by dedicated passing tests:

- A short product-help follow-up reuses the previous product question.
- The latest relevant user question is selected rather than an older question.
- Assistant replies are not treated as user instructions or retrieval context.
- Normal standalone questions remain unchanged.
- Personal financial questions and third-party financial questions are not reused as product FAQ context.

**Tests:**
- `test_faq_follow_up_reuses_previous_product_question`
- `test_faq_follow_up_does_not_use_previous_assistant_reply`
- `test_faq_follow_up_uses_latest_user_question`
- `test_faq_retrieval_query_keeps_normal_question_unchanged`
- `test_faq_follow_up_does_not_reuse_personal_financial_question`
- `test_faq_follow_up_does_not_reuse_third_party_financial_question`

**Result:** 6 passed.

These tests verify retrieval-query construction and context selection. They do not establish a complete live multi-turn FAQ conversation with a production backend.

## 8. Full project test result

**Date:** 2026-11-13

- 453 passed
- 4 skipped
- 0 failed
- 2 dependency/configuration deprecation warnings

The four skipped tests require grounded transaction, budget, multi-period comparison, and trend/aggregate data that is unavailable to this module.
