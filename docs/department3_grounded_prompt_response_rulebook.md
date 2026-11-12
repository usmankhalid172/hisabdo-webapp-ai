# Department 3 — Grounded Prompt & Response Rulebook

## 1. Purpose

This rulebook defines how the HisabDo assistant must answer product and financial-education questions using retrieved, verified documentation. It aims to prevent invented product instructions, unsupported claims, fabricated citations, and misleading financial information.

## 2. Evidence hierarchy

1. Use retrieved records marked `verified: true` as the eligible knowledge sources.
2. Treat a retrieval match as a candidate source, not automatic proof of every generated claim.
3. Use product documentation only for claims about HisabDo features and workflows.
4. Use finance education sources only for general accounting and financial concepts. They do not establish HisabDo product capabilities.
5. Do not infer missing steps, features, export formats, figures, or settings.
6. If evidence is missing, weak, unavailable, or contradictory, use the appropriate fallback.

## 3. Response-generation rules

- Answer only claims directly supported by the retrieved evidence.
- Keep answers concise and distinguish documented facts from limitations.
- Do not invent screen names, navigation paths, buttons, API endpoints, or product behaviour.
- Do not present general financial knowledge as personal financial data.
- Personal balances and transaction figures must come from the authenticated backend.
- Never imply that a transaction was saved when the chatbot has not saved it.
- Do not expose another user's financial information.
- If the retrieved evidence does not support the requested answer, say so respectfully and direct the user to HisabDo support where appropriate.

## 4. Citation policy

Citations are allowed only when a verified retrieved record explicitly supports the associated claim.

A citation must:
- Refer to a retrieved verified record.
- Use the source title and section supplied by that record, where available.
- Use only a valid HTTP or HTTPS source URL supplied by the record.
- Support the specific claim beside which it appears.
- Be omitted when the evidence does not support the claim.

Permitted inline form:

`[Source: <exact source title> — <exact section>]`

If no section is available, use:

`[Source: <exact source title>]`

Never:
- Invent a URL, title, section, page, or source.
- Attach a relevant-looking citation to an unsupported claim.
- Treat a source URL alone as proof of a claim.
- Cite unverified or unrelated records.

The citation builder and inline citation filter enforce source eligibility and exact source labels. Semantic support must also be respected by the response-generation prompt; an eligible citation is not proof that every sentence is supported.

## 5. Source conflict handling

Conflict detection is deterministic and requires explicit metadata:
- `verified` must be `true`.
- Entries must share a non-empty `conflict_key`.
- Entries must contain non-empty `conflict_value` fields.
- A conflict exists only when the same normalized key has more than one distinct value.

When a conflict is detected:
1. Do not choose one value arbitrarily.
2. Surface the conflicting values and associated source titles.
3. State that the current value cannot be determined.
4. Direct the user to HisabDo support for confirmation.
5. Cite only the verified conflicting records.

Entries with different topics or a shared URL are not automatically conflicts. The current FAQ inventory did not establish a real source conflict; conflict examples in the companion transcript document are synthetic test fixtures.

## 6. Ambiguous expense statements

A first-person expense statement may describe an event without requesting that it be recorded.

Examples:
- `I spent 500 on groceries.`
- `We just paid 1200 for transport.`
- `Maine 500 kharch kiye.`

When the statement is ambiguous, ask:

`Are you asking me to record this as an expense, or are you just mentioning it?`

Do not assume consent to record a transaction. Explicit transaction requests continue through the transaction-intent flow, which asks for missing details. The current chatbot transaction flow does not save the transaction.

## 7. Safe fallback responses

### No relevant verified documentation
`I couldn't find relevant verified information in the HisabDo documentation or FAQs. Please contact HisabDo support for confirmation.`

### Knowledge-base retrieval error
`I couldn't search the HisabDo knowledge base right now. Please try again later.`

### Conflicting verified sources
Identify the conflicting values and source titles, state that the current value cannot be determined, and recommend contacting support.

### Backend unavailable for personal financial data
Do not estimate or fabricate a balance, transaction, or financial summary. Return the safe service-unavailable response.

## 8. Known evidence limitations

- Exact screen-by-screen instructions for some Khata and Udhar workflows remain unverified.
- CSV export is not confirmed by the available approved evidence.
- The documented PDF report behaviour must not be expanded into unsupported preview or download instructions.
- Source ownership, independent approval, and scheduled review metadata remain incomplete in the audit inventory.
- General finance references must not be treated as proof of HisabDo product features.

## 9. Verification and maintenance

Before approving a knowledge-base change:
1. Confirm the source is authoritative and relevant.
2. Verify the exact claim against the source.
3. Record source title, URL, section, review date, and owner when available.
4. Mark a record verified only after evidence review.
5. Keep unresolved claims explicitly unverified.
6. Add tests for citation eligibility, conflict handling, ambiguous expense statements, and safe fallbacks.
7. Re-run focused tests and the full test suite after changes.

## 10. Acceptance criteria

- Product answers are grounded in verified retrieved evidence.
- Citations refer only to eligible sources and supporting claims.
- Unsupported citations and fabricated product details are prevented.
- Explicit source conflicts are surfaced rather than silently resolved.
- Ambiguous expense statements trigger clarification.
- Missing evidence and backend failures produce safe fallbacks.
- Example transcripts distinguish real evidence from synthetic test fixtures.
