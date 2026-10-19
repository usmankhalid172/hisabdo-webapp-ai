# Evaluation Test Set and Results

## Scope
This report records the latest full test-suite result provided for the current working repository.

## Execution Result

Command:

```powershell
python -m pytest -q
```

Reported result:

- Passed: 351
- Skipped: 4
- Warnings: 2
- Duration: 68.67 seconds
- Reported failures: 0

These figures are the terminal output from the reported run. Re-run the suite after further code or documentation-related changes if implementation files change.

## Test Coverage Areas

The repository includes test files for the following areas:

| Area | Relevant test files |
|---|---|
| Chatbot and FAQ retrieval | `test_chatbot.py`, `test_faq_rag.py`, `test_retrieval.py` |
| Financial API security | `test_financial_api_security.py` |
| Cross-user data boundaries | `test_cross_user_data_boundary.py` |
| Multilingual behaviour | `test_financial_multilingual.py` |
| Intent routing | `test_intent_router.py` |
| LLM service | `test_llm_service.py` |
| RAG pipeline | `test_rag_pipeline.py` |
| API integration and readiness | `test_integration_api.py`, `test_integration_readiness.py` |
| Error handling | `test_day21_22_error_handling.py` |
| Adversarial inputs | `test_day27_adversarial_inputs.py` |
| Startup/import checks | `test_startup_imports.py` |
| Vector-store behaviour | `test_vector_store_day25.py`, `test_vector_store_day26.py` |

The table identifies available test areas; it does not represent separate per-file pass counts.

## Recommended Evaluation Cases

1. Submit a supported product FAQ and check whether the answer is relevant.
2. Ask a question with no supporting knowledge-base entry and check the fallback response.
3. Ask equivalent supported questions in English and Roman Urdu where multilingual coverage applies.
4. Submit malformed or incomplete input and verify controlled error handling.
5. Call protected endpoints without a valid internal token and verify rejection.
6. Attempt to request another user's financial information and verify access is denied.
7. Test intent and slot extraction with an expense request containing an amount and description.
8. Check that retrieval results are relevant to the submitted question.
9. Check service startup and API health behaviour.
10. Re-run the full suite after changes.

Record the input, expected behaviour, actual output, status, and evidence for each manually evaluated case.

## Warnings and Skipped Tests
The reported run contained two warnings and four skipped tests. Their causes have not been established in this report. Review the full pytest output before deciding whether they require action.

## Evaluation Status
Automated test run: PASS according to the reported summary (351 passed, 4 skipped, 2 warnings).

This does not by itself establish production readiness, successful live-provider operation, upstream application integration, or team-lead sign-off.
