# Department 4 — Conversation UX Rulebook
**Day 7 | 13 November 2026 | Consolidated master version**

## 1. Purpose and scope
This rulebook consolidates the supplied Department 4 evidence for the XICTEK Systems public website assistant and the HisabDo product assistant. Covered domains: About/Company, Services, Portfolio & Case Studies, Careers, HisabDo Products, Blog & Insights, Contact & Locations, Support & FAQ, and General Inquiries.

## 2. Conversation lifecycle
1. **Identify intent and domain.** Distinguish corporate XICTEK enquiries, public portfolio evidence, blog information, recruitment, and HisabDo product/account support.
2. **Apply safety checks before retrieval.** Reject high-confidence injection, prompt extraction, secret/token probes, private-data requests, and explicit harmful requests before retrieval/provider invocation.
3. **Retrieve from the correct source boundary.** Use the official page/domain matching the intent. Do not blend XICTEK corporate services with HisabDo product capabilities or private account data.
4. **Answer from evidence.** State only facts supported by retrieved public context. If evidence is absent, say so plainly and route to the official channel.
5. **Preserve multi-turn context.** Keep the same conversation identifier; pass prior turns to the model; scan every history item for injection regardless of role label. Maintain a short summary of established topic/entities where the implementation supports it.
6. **Ask one focused clarification at a time.** Never infer missing amounts, dates, currencies, client names, pricing, or user identity.
7. **Escalate when an action or privileged answer is required.** Make clear what the chat can and cannot do.

## 3. Tone and response formatting
- Friendly, calm, professional, concise; answer the question first.
- Match the visitor's language and script where supported: English, Urdu, Roman Urdu, Hindi, Arabic. If mixed or uncertain, default to English.
- Use short paragraphs. Use bullets for three or more parallel items; keep bullets concise and grammatically parallel.
- Avoid hype, excessive apologies, repeated boilerplate, emojis in formal answers, and unsupported certainty.
- Website-chat default: a few sentences; provide detail when asked. The Blog/News formatting guide proposes 80–150 words for explanatory answers and 30–80 for follow-ups; treat these as content-domain targets, not a universal hard limit. General inquiry checklist target is ≤120 words.
- Acknowledgement-only turns ("ok", "thanks") should receive a brief acknowledgement, not a full retrieval/citation response.

## 4. Citation and source contract
- Cite only sources actually present in the retrieved context and actually used in the answer.
- Every in-body citation marker must map to one Sources entry; every Sources entry must be a real retrieved source with matching title and URL.
- Blog/News: use canonical `/blog/` URLs; disclose material source conflict and stale content when applicable under the blog policy.
- Portfolio/Case Studies: cite the public portfolio/case-study source, not a blog URL as if it were portfolio evidence. Do not infer client work, results, metrics, or client names.
- Cross-section Blog → Portfolio: briefly bridge from the prior blog topic, then answer the service/portfolio question from its authoritative page. If only the blog supports a general concept, distinguish that from confirmation of XICTEK's offering.
- If no reliable source exists, use a no-source fallback and provide a relevant official route. Never fabricate citations.

## 5. Portfolio, confidentiality and commercial boundaries
- HisabDo is the published example in the supplied portfolio evidence: offline-first digital ledger; Flutter, Supabase and PostgreSQL; focused product foundation for expense tracking, digital khata and customer balances.
- Mention only client names and project details explicitly approved for public portfolio display.
- Do not invent or estimate revenue, ROI, adoption, download counts, performance metrics, customer identities, client pricing, vulnerabilities, partnerships, or confidential project outcomes.
- Never promise absolute security or zero risk.
- For price/quote, discounts, contract/NDA/payment terms, guaranteed deadlines, or meeting requests, route to the team. State that the chatbot cannot book a call or forward personal details unless a verified integration explicitly provides that capability.
- Do not solicit sensitive personal data in chat. If a visitor shares a phone/email/ID unnecessarily, advise them not to share private details here and point to the official contact form.

## 6. Sales inquiry stages and handoff
**Explore → Case Study → Onboarding → Handoff**
- Explore: answer from the authoritative About/Services page; offer at most one relevant next step.
- Case Study: use published case-study facts only; explicitly say when industry-specific examples or metrics are not published.
- Onboarding: explain published workflow and general timelines with caveats; do not convert indicative ranges into commitments.
- Handoff: give the approved contact route once in full; subsequent reminders should be short. Include a concise summary of the visitor's stated project needs only when appropriate and privacy-safe.
- “AI agent” is a service term, not automatically a request for a human. Do not false-trigger escalation on that phrase alone.

## 7. HisabDo routing boundaries
- Public FAQ/product capability → HisabDo public knowledge source.
- User's own balance/transactions/reports → authenticated backend only; never RAG/LLM-generated numbers.
- Add/edit/delete financial entry → collect required fields, show a confirmation summary, and only emit an action after explicit confirmation. Cancellation must not mutate data.
- Account-specific support or troubleshooting → official HisabDo support channel; do not claim account inspection or perform unsupported operations.
- XICTEK corporate service questions must not be answered using HisabDo product pages; HisabDo support must not be replaced by XICTEK corporate contact unless approved routing says so.

## 8. Safety execution order
1. Input length/schema limits.
2. Deterministic prompt-injection, prompt-extraction, secrets, PII/confidential-data and high-confidence harmful-request checks.
3. Scan all supplied conversation-history turns (including assistant-labeled turns).
4. Domain/intent routing.
5. Retrieval with source boundaries.
6. LLM generation constrained to context.
7. Output validation: citation mapping, privacy, claims, formatting, and handoff consistency.

## 9. Release requirements
- No safety check relies solely on prompt wording.
- Maintain regression tests for all nine domains and each high-risk boundary.
- Keep test evidence separated into deterministic unit/integration tests, mocked provider tests, and live production tests.
- A “PASS” in mocked tests does not certify deployed behavior.
