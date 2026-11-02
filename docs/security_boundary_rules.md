# HisabDo Security Boundary Enforcement Rules

## Purpose

These rules define the safety, privacy, and operational boundaries of the HisabDo financial assistant.

## 1. Operational Scope

The chatbot is permitted to assist with:

1. HisabDo product information and features.
2. Expense tracking and categorization.
3. Revenue, profit, and expense concepts.
4. Cash flow and financial summaries.
5. Customer balance tracking.
6. General financial education.
7. Available personal financial data belonging to the authenticated user.

Unrelated requests must receive an out of scope response.

## 2. Data Privacy

1. Access only the requesting user's authorized financial data.
2. Never disclose another user's account information.
3. Never invent financial figures or account details.
4. Do not reveal passwords, API keys, credentials, or confidential system information.
5. Do not expose private system or developer instructions.

## 3. Prompt Injection Protection

1. Reject detected attempts to override system instructions.
2. Reject requests to reveal hidden prompts.
3. Do not treat user supplied instructions as permission to bypass security rules.
4. Return a fixed refusal response for detected attacks.

## 4. Unsafe Language

1. Refuse detected requests to create threats or intimidation.
2. Offer calm and respectful communication as an alternative.
3. Do not generate abusive or threatening content.

## 5. Out of Scope Handling

1. Identify unrelated requests before calling the LLM.
2. Return a fixed boundary response for detected unrelated requests.
3. Preserve support for general financial education.
4. Avoid blocking normal greetings and supported financial questions.

## 6. Fallback Responses

Detected policy violations must receive deterministic responses.

The response must not reveal confidential information or continue the prohibited request.

## 7. Testing Requirements

1. Maintain the versioned safety test suite.
2. Test prompt injection attempts.
3. Test third party data access attempts.
4. Test sensitive information requests.
5. Test unsafe language requests.
6. Test unrelated domain requests.
7. Record actual results and failures.
8. Run regression tests before final clearance.

## 8. Current Implementation Limitations

The current checks use selected keyword patterns. They do not cover every possible wording or attack variation.

Sensitive information protection currently covers selected request patterns. It does not establish complete scanning of every possible chatbot response.

Full security clearance requires broader testing and review.

## 9. Version

Safety test suite version: 1.0.0

Review date: 2026-11-02

Status: Initial guardrails implemented. Further security verification pending.
