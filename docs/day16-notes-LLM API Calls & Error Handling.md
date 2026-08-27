# Day 16 — LLM API Implementation Notes

## Owner
Muhammad Hamza Nawaz — LLM Validation & Error Flow

## Provider status

An OpenAI-compatible API is used as a temporary implementation
assumption for this branch. This is not a finalized project decision.

Asim's model/API research task is marked complete in ClickUp, but no
PR or branch with that comparison/recommendation exists in the repo
yet. Once that research is submitted and reviewed by the Team Lead,
the final provider/model will be confirmed and this implementation
will be updated to match if needed.

The provider-specific call is isolated in a single function
(`_call_llm_api` in `llm_service.py`), so switching providers later
is a small, contained change rather than a rewrite.

## API key handling

The API key is read from the `FINANCIAL_ASSISTANT_LLM_API_KEY`
environment variable. No real API key is committed anywhere in this
repository.

## Testing status

Live-key testing against a real LLM API is currently blocked, since
no provider/key has been confirmed yet. All 15 tests in
`tests/test_llm_service.py` use a mocked LLM client and do not
require network access or a real API key.

This mocked test suite is the current evidence for the request flow,
input validation, response validation, error handling, timeout
behavior, and fallback behavior. Live testing will be added once a
provider is confirmed and a key is available.

## Blockers / Dependencies

- Final LLM provider/model: pending Asim's model/API research review
- Live API testing: blocked until a provider/key is confirmed