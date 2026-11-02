# HisabDo Safety and Privacy Guardrails v1.0.0

Date: 2026-11-02
Department: 3
Status: Implemented with limitations; security clearance pending.

## 1. Purpose
Define input validation, privacy protections, unsafe-request handling,
domain boundaries, and untrusted-context handling for the HisabDo
financial assistant.

## 2. Implemented controls

- Guardrails version: 1.0.0.
- Maximum user message: 1,000 characters.
- Maximum history: 20 turns.
- Maximum individual history content: 2,000 characters.
- Maximum total history content: 8,000 characters.
- Only user and assistant history roles are accepted.
- Common prompt-injection and instruction-override phrases are blocked.
- Configured unsafe-request patterns receive a refusal.
- Configured off-topic patterns receive a domain-boundary refusal.
- Obvious API keys, passwords, bearer tokens, email addresses,
  Pakistani mobile numbers, and labeled contact details are detected
  in generated output.
- Retrieved/backend context is explicitly marked as untrusted reference data.
- Existing cross-user account access protection remains in place.
- Invalid input and history receive fallback responses.

## 3. Boundary enforcement rules

1. The assistant is intended for HisabDo features and the authenticated
   user's own financial information.
2. Requests for another person's private financial data must be refused.
3. User instructions must not override system or safety instructions.
4. Retrieved documents and backend context are reference data, not instructions.
5. Unsupported product information must not be invented.
6. Configured out-of-scope and unsafe requests must receive a refusal.
7. Responses containing detected credential/contact patterns must be replaced
   with the configured sensitive-output fallback.
8. Cross-user access must continue to be rejected by the API authorization layer.

## 4. Fallback categories

- prompt_injection: INJECTION_REPLY
- unsafe_request: UNSAFE_REPLY
- out_of_scope: OUT_OF_SCOPE_REPLY
- invalid_input / invalid_history: INVALID_INPUT_REPLY
- sensitive generated output: SENSITIVE_OUTPUT_REPLY

## 5. Known limitations

- Detection is regex/pattern based, not a comprehensive semantic classifier.
- English-language patterns do not cover every language or paraphrase.
- Threat patterns do not detect every toxic or abusive message.
- Contact detection covers selected formats and is not a guarantee against
  all personal-data disclosure.
- Output scanning does not identify every possible confidential detail.
- Untrusted-context delimiters reduce instruction confusion but do not
  independently prove model-level prompt-injection resistance.
- All assigned knowledge-base components have not yet received a separate
  end-to-end security verification.
- Production authentication/backend behaviour requires separate deployment
  testing.

## 6. Clearance decision

This version has passed the recorded regression and guardrail test run.
It is not an unrestricted production security clearance. Further multilingual,
semantic, end-to-end, and deployment testing is required.
