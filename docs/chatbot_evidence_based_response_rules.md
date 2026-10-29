# Chatbot Evidence-Based Response and Source Handling Rules

## 1. Purpose

The HisabDo chatbot must provide accurate, reliable, evidence-based answers. Product and workflow claims must be supported by retrieved, approved knowledge sources. The chatbot must not invent product details, links, sections, or citations.

## 2. Prompt and response handling rules

1. Use relevant retrieved knowledge for product, feature, workflow, and general knowledge questions.
2. Only make claims supported by the available evidence.
3. Include a source title, section, and source ID when available and relevant.
4. Include a source URL only when a real URL is present in the retrieved metadata.
5. Do not invent citations or claim a source was checked when it was not retrieved.
6. If evidence is missing, acknowledge the limitation and suggest a useful next step.
7. If the question is ambiguous and the ambiguity affects the answer, ask one concise clarifying question.
8. If sources conflict, explain the specific conflict when supported by the retrieved evidence. If it cannot be resolved, refer it to the responsible content owner.
9. Never obtain a user's own financial figures from the FAQ knowledge base. Continue using the authorized backend financial-data path.
10. Never disclose another user's financial information.

## 3. Citation format and examples

The API citation metadata contains:
- `title`: retrieved source title
- `section`: source section, if available
- `source_id`: retrieved knowledge record ID
- `source_url`: actual source URL, if available

### Example: a retrieved FAQ supports the answer

Suppose a retrieved record has:
- Title: Export Expenses
- Section: FAQ
- Source ID: `faq_export_expenses`
- Source URL: `null`

Appropriate response format:

"According to the Export Expenses FAQ, you can follow the documented expense-export guidance. Source: Export Expenses, section FAQ (ID: faq_export_expenses)."

This example illustrates citation formatting only. The answer's actual product instructions must come from the retrieved FAQ text.

Because the URL is null, do not display a fabricated link.

### Example: a real source URL is available

If retrieved metadata contains an approved URL, include that exact URL with the relevant source title and section. Do not construct a URL from the source ID.

### Example: a source does not support the claim

If the retrieved FAQ discusses expense categorization but the user asks whether a specific export format is supported, do not cite the categorization FAQ as proof. State that the available source does not confirm export-format support and suggest checking approved documentation or contacting product support.

## 4. Unavailable information and fallback responses

When no relevant source is retrieved, the chatbot should not invent product facts.

Example response:

"I couldn't find a relevant, verified source for that question in the current knowledge base. Please check the approved HisabDo documentation or contact product support to confirm."

For a question about a specific feature, the chatbot may ask the user which feature or workflow they mean if that clarification would help.

## 5. Ambiguous questions

Ask a focused clarification when different interpretations could produce different answers.

Example:

User: "How do I export it?"

Appropriate response:

"Do you want to export your expenses, a report, or another type of data?"

Do not guess which workflow the user means. Once the user clarifies, retrieve the relevant source and answer from its contents.

## 6. Conflicting sources

When multiple retrieved sources appear to disagree:

1. Identify the relevant source titles, sections, and IDs.
2. Compare the exact statements and check whether they describe different versions, dates, or workflows.
3. Do not silently select one conflicting statement as correct.
4. Explain the disagreement without adding unsupported details.
5. If the conflict cannot be resolved from approved evidence, state that confirmation is needed and escalate it to the responsible content owner.
6. Record the conflicting records for review. The content owner should confirm the authoritative wording and update or retire outdated entries.

Example response:

"I found conflicting guidance in the available documentation about this workflow, so I can't reliably confirm which instruction is current. The relevant sources need review by the content owner before I can give you a definitive answer."

This is an illustrative response; identify actual source titles and sections only when those records were retrieved.

## 7. Knowledge-source maintenance

For each knowledge record, maintain these fields where applicable:
- Record ID and title
- Category and product area
- Section
- Approved source URL
- Owner
- Last-verified date
- Review or expiry policy

Review duplicate, outdated, contradictory, or low-quality entries. Do not add customer personal information, credentials, or secrets to the knowledge base.

## 8. Current implementation notes and limitations

- The retriever currently uses TF-IDF similarity and a relevance threshold of 0.30.
- The current service retrieves one FAQ match for a normal RAG response.
- The response schema supports citation metadata, and the RAG path attaches the retrieved record's title, section, URL, and ID.
- Existing FAQ records may have a null URL or last-verified date. In those cases, the chatbot must not invent a link or verification date.
- A single-result retrieval does not reliably identify conflicts between separate records. Conflict detection and owner escalation require multiple-source comparison and an operational review process.
- Prompt instructions alone do not guarantee that every ambiguous question will trigger clarification. This behavior should be verified with targeted tests.
- Citation metadata identifies the retrieved record; it does not by itself prove that every generated sentence is supported. Responses and citations must be checked against the retrieved text.

## 9. Validation checklist

- [ ] Product claims are supported by retrieved source text.
- [ ] Citations use real retrieved metadata only.
- [ ] Missing URLs are not fabricated.
- [ ] Unsupported questions receive a clear limitation and next step.
- [ ] Ambiguous questions receive a focused clarifying question.
- [ ] Conflicting sources are disclosed and sent for review when unresolved.
- [ ] Own-account financial data continues to use the backend financial API.
- [ ] Third-party financial-data requests remain refused.
- [ ] Tests cover citations, fallback behavior, ambiguity, and source conflicts.
