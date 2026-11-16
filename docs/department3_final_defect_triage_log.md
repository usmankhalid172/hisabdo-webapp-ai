# Department 3 Final Defect Triage Log

Date: 16 November 2026

## 1. Summary

Validation identified two observed functional or quality defects and several release readiness blockers.

The full local automated test suite passed, but passing tests do not override defects found during direct API smoke testing.

## 2. Defect Register

| ID | Priority | Defect | Evidence | Required action |
|---|---|---|---|---|
| D3-REG-001 | High | Expense export instructions are routed to the financial backend | "How do I export my expenses?" returned backend financial values instead of FAQ instructions | Narrow own financial data detection and add route assertion tests |
| D3-REG-002 | Medium | Relevant evidence is missing from the response citation list | Cash flow statement answer included faq 005 evidence in context but returned citations for faq 004 and faq 006 | Review citation support matching and test evidence to citation completeness |
| D3-REG-003 | Medium | Source URLs are absent from sampled citations | All five API smoke responses had null source URLs | Verify approved source URLs and ensure valid URL metadata reaches API responses |

## 3. Release Readiness Blockers

| ID | Priority | Issue | Evidence | Required action |
|---|---|---|---|---|
| D3-BLK-001 | Blocker | Experimental hybrid retrieval is not verified in active API | Active faq_rag.py uses TF IDF and cosine similarity | Integrate and verify the intended retrieval strategy in the actual request path |
| D3-BLK-002 | Blocker | Production financial backend is not validated | Local environment uses deterministic mock financial data | Obtain approved backend contract and test real authenticated account access |
| D3-BLK-003 | Blocker | Production LLM integration is not validated | Local tests use mock provider | Configure and test the approved production provider and grounded prompt |
| D3-BLK-004 | Blocker | Production session isolation is not proven | Local security tests do not replace live backend and concurrent customer tests | Verify account ownership, session isolation, and concurrent requests |
| D3-BLK-005 | High | Full Day 1 golden set was not manually checked through the API | Five question smoke sample completed, not the complete golden set | Run all golden questions through the integrated API and record expected versus actual behavior |

## 4. Routing Defect Detail

Observed question:

"How do I export my expenses?"

Expected behavior:

Return FAQ instructions from faq 005. The knowledge base states that recorded expenses can be exported as CSV or PDF from the Reports section, with filters for date range, category, or tag.

Actual behavior:

The request was routed to backend_financial_api and returned synthetic values for balance, expenses, revenue, and outstanding receivables.

Likely cause:

The own financial data classifier contains a broad pattern matching "my expenses". This treats an instruction request as a request for the user's financial figures.

Impact:

Incorrect response and unnecessary disclosure of synthetic account figures. No cross user exposure was demonstrated in this test.

Fix verification:

Add tests that require export instructions and expense report download questions to use RAG, while genuine questions about the user's own expense totals continue to require authenticated backend data.

## 5. Citation Defect Detail

Observed question:

"What is a cash flow statement?"

The response context included faq 005 evidence, but the returned citations included faq 004 and faq 006 only.

All five sampled API responses had null source URLs.

Required verification:

Check the citation support matching logic, source metadata, and API response serialization. Confirm that every cited source supports the answer and every relevant source used in the final response is attributed appropriately.

## 6. Retrieval Benchmark Notes

The best offline strategy, feature_intent_020, achieved:

| Metric | Result |
|---|---:|
| Hit at 1 | 95.00% |
| Hit at 3 | 98.33% |
| Hit at 5 | 100.00% |

These results are not evidence of active API performance. The active retriever remains TF IDF only. Dense embeddings were not measured, and the BM25 and reranking components are experimental.

## 7. Test Evidence

Full suite: 341 passed, 4 skipped, 1 warning.

Selected Phase 2 group: 94 passed.

Cross user, safety, and adversarial tests: 37 passed.

Chatbot, financial security, and integration readiness: 34 passed.

Multi turn and safety focused tests: 13 passed.

The focused groups overlap and must not be added to the full suite count.

## 8. Closure Criteria

A defect can be closed only after:

1. The code change is reviewed.
2. A focused regression test passes.
3. The relevant full test suite passes.
4. Direct API behavior matches the expected result.
5. Evidence and citations are checked.

Production blockers require live integration evidence, not only local mock tests.

## 9. Final Triage Decision

Release status: NOT CLEARED.

High priority routing defect remains open. Citation attribution requires correction and verification. Active hybrid retrieval, production LLM, real backend integration, and production session isolation remain unverified.

No application code was modified during this validation.