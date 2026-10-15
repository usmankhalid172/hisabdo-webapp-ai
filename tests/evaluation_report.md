# HisabDo AI Chatbot Evaluation Report

**Date:** 15 October 2026  
**Branch:** purnoor-zafar-ai-intern

## Objective
Evaluate retrieval for realistic finance/product questions, identify weak retrieval behavior, add regression coverage, and review privacy boundaries.

## Evaluation dataset
- Total retrieval cases: 10
- Retrieval checks passed: 10/10
- Cases needing review: 0
- Coverage includes simple, detailed, reworded, ambiguous, Roman Urdu, Urdu-English mixed, and unsupported questions.

## Fixes and regression coverage
- Added a guard to avoid treating an ambiguous balance question as a balance-sheet FAQ.
- Added explicit clarification handling for ambiguous balance questions.
- Added regression tests for ambiguous-balance retrieval and chatbot clarification.

## Test results
- Chatbot tests: 16 passed
- Cross-user data boundary tests: 19 passed
- Full-suite result: Record the final result from `python -X utf8 -m pytest tests -q`.

## Privacy and grounding notes
- Third-party financial-data requests are checked by policy-guard tests.
- Authenticated user identity checks are covered by API tests.
- Personal financial queries use the backend-financial-data path rather than the shared FAQ retrieval path.
- The current backend client returns demo figures; production data isolation must be verified against the real backend.
- Retrieval results validate FAQ selection, not every generated answer. Source attribution, readability, and response factuality should be assessed with response-level tests.

## Conclusion
The retrieval evaluation passed all 10 cases. Targeted chatbot and cross-user boundary tests passed. Final completion depends on recording the full-suite result and successfully committing and pushing the reviewed changes.
