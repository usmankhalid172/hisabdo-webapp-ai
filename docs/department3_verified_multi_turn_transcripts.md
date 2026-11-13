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
