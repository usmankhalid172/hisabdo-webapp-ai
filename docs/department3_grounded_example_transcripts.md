# Department 3 — Grounded Prompt & Response Example Transcripts

## Status and interpretation

These are documented expected-behaviour examples based on the current implementation and approved knowledge-base evidence. They are not represented as captured production conversations. The source-conflict case is a synthetic test fixture because no real conflict was established in the current FAQ inventory.

## 1. Standard grounded answer

**User:** What is HisabDo?

**Assistant:** HisabDo is an offline-first khata and ledger application that helps users keep track of money given and received, customer balances, and expenses.

**Evidence:** `faq-001` — Official HisabDo FAQ, section `Product Overview`.

**Grounding check:** The answer is limited to the documented product overview. It does not invent additional features or workflows.

## 2. Citation-supported answer

**User:** What does cash flow mean?

**Assistant:** Cash flow tracks money entering and leaving a business. [Source: OpenStax Principles of Financial Accounting — Section 2.1]

**Evidence:** Verified finance-education entry `faq-004`, OpenStax Principles of Financial Accounting, section 2.1.

**Grounding check:** This is a general accounting explanation, not a claim about a HisabDo feature.

## 3. Conflicting source entries — synthetic test fixture

**Fixture only:** Two verified test records share `conflict_key = "pdf_export_format"` but have different values.

- Test source A: `PDF`
- Test source B: `CSV`

**User:** Which export format is currently supported?

**Assistant:** The verified sources contain conflicting entries for `pdf_export_format`. Recorded values: CSV; PDF. I can't determine which value is current. Please contact HisabDo support for confirmation.

**Grounding check:** The assistant does not select a value arbitrarily. The fixture is synthetic and does not establish a real HisabDo product conflict.

## 4. Ambiguous expense statement

**User:** Maine 500 kharch kiye.

**Assistant:** Are you asking me to record this as an expense, or are you just mentioning it?

**User:** I am just mentioning it.

**Assistant:** Understood. I won't treat that statement as a request to record a transaction.

**Grounding check:** The assistant asks for intent before entering the transaction flow. No transaction is claimed to have been saved.

## 5. No-answer fallback

**User:** Does HisabDo support automatic bank synchronization with every bank?

**Assistant:** I couldn't find relevant verified information in the HisabDo documentation or FAQs. Please contact HisabDo support for confirmation.

**Grounding check:** The assistant does not invent a feature or claim universal bank support.

---

## Transcript verification notes

- The standard answer is grounded in the approved product overview entry.
- The cash-flow answer uses a general finance-education source.
- The conflict example is a synthetic fixture, not a discovered production conflict.
- The ambiguity example reflects the intended clarification behaviour.
- The no-answer example reflects the safe retrieval fallback.
- These examples should be run against the application and retained as captured test transcripts before being described as end-to-end production-verified conversations.
