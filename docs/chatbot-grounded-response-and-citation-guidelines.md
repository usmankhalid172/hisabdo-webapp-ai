# Chatbot Grounded Response and Citation Guidelines

## 1. Purpose

Ensure chatbot responses are grounded in retrieved knowledge sources. The chatbot must provide evidence-based answers, cite sources only when they support the response, acknowledge missing information, clarify ambiguous questions, and handle conflicting sources transparently.

## 2. Prompt and Response Handling Rules

- Use retrieved knowledge to answer product and workflow questions.
- Do not invent product features, policies, financial facts, instructions, or source references.
- Distinguish verified source information from assumptions or unavailable information.
- Provide citations only when the retrieved source genuinely supports the associated claim.
- Include relevant source links and section names when available.
- If evidence is incomplete, explain the limitation instead of presenting uncertain claims as confirmed.
- Ask a focused clarifying question when a request has multiple plausible meanings.
- Never claim a transaction was saved or an action was completed unless the system confirms it.
- Protect other users' private financial information.

## 3. Correct Source Citation Example

**Example question:** Where can I find information about HisabDo?

**Expected response pattern:**

"Please review the relevant product information in the [HisabDo FAQ](https://hisabdo.app/faq), under the section covering the product overview."

**Citation rule:** Use this link only when the retrieved FAQ genuinely supports the answer. Verify the link and section against the retrieved source before presenting them as evidence.

## 4. Fallback When Information Is Unavailable

**Example question:** Does HisabDo support a feature that is not covered by the retrieved documents?

**Expected response:**

"I couldn't verify that feature from the available documentation. Please check the official HisabDo documentation or contact product support to confirm."

**Rule:** Do not invent a feature or imply that the documentation confirms it.

## 5. Clarifying Ambiguous Questions

**Example question:** "Show me my report."

**Expected response:**

"Do you mean your expense report, income report, or another report?"

**Rule:** Ask one relevant question that resolves the ambiguity before giving specific instructions.

## 6. Conflicting Sources

When retrieved sources disagree:

1. Identify the claims that conflict.
2. Compare source authority, verification status, dates, and relevance.
3. Do not silently choose one claim when the conflict cannot be resolved reliably.
4. Explain that the available sources disagree.
5. Flag the conflict for knowledge-base review where supported.
6. Update the knowledge base only after the correct information has been verified.

**Example response:**

"The available documentation gives conflicting information about this feature, so I can't confirm which version is correct. Please contact product support while the documentation is reviewed."

## 7. Verification Checklist

- [ ] Answers use relevant retrieved evidence.
- [ ] Citations support the claims they accompany.
- [ ] Source links and section names refer to verified material.
- [ ] Unsupported questions receive a transparent fallback.
- [ ] Ambiguous questions receive a focused clarification.
- [ ] Conflicting sources are disclosed and flagged for review.
- [ ] Automated tests pass, and skipped tests are reviewed separately.

## 8. Validation Limitations

These examples describe intended behavior; they do not independently prove that every scenario works in the running application. Validate behavior with automated tests and, where available, integration or live-model testing. Record unavailable live-model checks as limitations.
