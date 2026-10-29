# Day 29 — Grounded Generation, Citations and Fallback

## Objective
Improve chatbot response-grounding rules so answers stay within retrieved evidence, unsupported citations are not invented, missing information is handled transparently, and ambiguous questions are clarified.

## Changes Made
- Updated `src/financial_assistant/prompts.py`.
- Added Day 29 grounded-generation and source-evidence rules inside `SYSTEM_PROMPT`.
- Verified that the rules are present in the imported prompt.
- Confirmed prompt length: 6240 characters at verification time.

## Grounded Response Rules
1. Use retrieved FAQ context only for claims that it supports.
2. Do not invent source titles, document IDs, section names, URLs, quotations, or citations.
3. Do not create clickable links when a valid source URL is unavailable.
4. Treat `pending` verification status as pending, not verified.
5. If relevant information is unavailable, explain the limitation and suggest a useful next step.
6. If a question is ambiguous, ask a concise clarification question.
7. If sources conflict, do not silently combine them or choose one without justification; explain the conflict and seek review when appropriate.
8. Route personal financial-data questions through the authorized backend instead of shared FAQ retrieval.
9. Do not disclose another user's private financial data.

## Expected Behavior Examples

### Supported answer
When retrieved FAQ text directly supports an answer, respond using only the supported facts.

### Missing source URL
If a retrieved document has no URL, do not invent a link. Only identify the source using metadata that actually exists.

### Missing information
Example response:
"I cannot confirm that from the available product information. Please check the relevant product documentation or contact support."

### Ambiguous question
Example:
User: "Show me the balance."
Assistant: "Do you mean your account balance or the balance for a particular report or period?"

### Conflicting sources
If two retrieved sources provide incompatible information, explain that the available information conflicts and recommend verification rather than presenting an unsupported conclusion.

## Source Metadata Observations
The inspected FAQ data contains source metadata fields such as document ID and `source_url`. Some records have `source_url: null` and `source_verification: "pending"`.

Therefore, valid clickable citations and verified-source claims cannot be assumed for every FAQ record.

## Verification
- `SYSTEM_PROMPT` import check: passed.
- Grounded rules presence check: passed.
- Targeted tests:
  `tests/test_chatbot.py`
  `tests/test_llm_service.py`
  `tests/test_rag_pipeline.py`
  `tests/test_retrieval.py`
- Result: 52 passed in 2.34 seconds.

## Limitations
- Prompt instructions alone do not implement a dedicated citation-rendering system.
- Automatic source-conflict detection has not been independently verified.
- Actual source-link behavior depends on available metadata and application response handling.
- These test results verify the selected test suite, not every possible production scenario.

## Status
Grounded-generation prompt rules added and verified. Documentation created; further checks are required before declaring citation handling and source-conflict behavior fully implemented.
