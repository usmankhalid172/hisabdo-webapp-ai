# Department 4 — Day 7 Safety Hardening Report
**Consolidated evidence review | 13 November 2026**

## 1. Executive summary
The supplied Day 7 package reports 19 domain-specific adversarial audit cases, 20 UX checklist items, and a separate automated XICTEK regression suite reported as 102 passed / 0 failed. These are distinct evidence sets and must not be added together as if they were one homogeneous test run. The supplied multi-turn Blog/News/Portfolio log covers 5 scenarios / 15 turns.

**Evidence status:** The source documents report full passes, but this consolidation did not independently reproduce the 102-test result. The supplied runner is not correctly located relative to its expected repository root, and its first execution failed before pytest collection (`--confcutdir` path invalid). A second attempt exposed a missing `test_careers_grounding.py` in the uploaded repository snapshot. Therefore the historical 102/0 result is recorded as *reported evidence*, not re-certified here.

## 2. Reported results (source evidence)
| Evidence set | Reported result | Interpretation |
|---|---:|---|
| Day 7 adversarial audit | 19/19 PASS | 8 injection, 3 jailbreak, 5 confidentiality, 3 UX cases |
| Contact/Portfolio/General UX checklist | 20/20 PASS | Checklist completion reported by safety lead |
| Department 4 domain register | 9/9 CLEARED | All nine domains marked cleared in the supplied sign-off |
| Automated regression | 102 passed, 0 failed | Reported in execution report; not independently reproduced in this compilation |
| Multi-turn UX log | 5 scenarios, 15 turns | Blog/News, Portfolio, cross-section |
| About/Services/Portfolio inquiry flow | 20 conversations, 35 turns | 35/35 routing and handoff decisions reported correct; 33/35 content checks fully passed |
| Careers/Portfolio privacy tests | Individual cases documented | Supplied document contains example probes and expected safe behavior |

## 3. Safety controls consolidated
### Prompt injection and jailbreak
- Do not disclose system/developer prompts, internal instructions, environment variables, API keys, tokens, credentials, or internal service details.
- Reject role reassignment, DAN/unrestricted framing, pretend/fictional framing, encoded extraction, format coercion, and conversation replay attacks.
- Sanitize HTML/comment/control-character injection before downstream processing.
- Scan every historical turn, regardless of whether the role is labelled user or assistant.

### Confidentiality
- No private client/customer identities, financial records, employee/applicant personal contact details, or unapproved client lists.
- No unpublished client revenue, ROI, performance, adoption, download, or user metrics.
- No speculation about client pricing, internal vulnerabilities, partnerships, or confidential project outcomes.
- Do not imply access to private accounts or internal company systems.

### Harmful requests and scope
- Explicit malware, credential theft, doxxing, data theft, and weapon-building requests should be blocked before retrieval/provider calls.
- Keep the classifier narrow enough not to block ordinary business questions or defensive security education.
- General out-of-scope questions receive a polite concise redirect; system-prompt text alone is not a deterministic safety boundary.

### UX and privacy
- Do not auto-fill or submit contact forms without user intent and validation.
- Do not invent contact details, office locations, opening hours, meeting slots, or support response times.
- Do not expose staff private phone numbers/emails.
- Keep XICTEK and HisabDo contact/support channels distinct.
- Explain when the assistant cannot book calls, forward details, inspect accounts, or perform an action.

## 4. Cross-domain consistency findings
1. **Strong common rule:** all domains use public-source grounding and prohibit unsupported claims.
2. **Portfolio:** privacy guardrails align with the case-study policy; only publicly disclosed facts are allowed.
3. **Careers:** protect applicant/employee contact data; do not expose personal contact details or infer hiring status beyond published information.
4. **HisabDo:** strict split between public product FAQ and authenticated personal financial data. The HisabDo intent-router notes say private figures are backend-only and never RAG/LLM-generated.
5. **Blog/News:** source citations and stale/conflict notes are domain-specific; do not apply those notes to evergreen Portfolio pages.
6. **Contact/Sales:** escalation rules must not fabricate availability or imply that the chatbot transmitted a message.
7. **Conversation state discrepancy:** the Blog/News/Portfolio UX log says 5/5 scenarios show continuity at retrieval level, but its own findings state the generation function is stateless and does not preserve turn history. Treat article overlap as retrieval continuity, not conversational memory. This needs correction in future reporting.
8. **Formatting discrepancy:** the Blog guide's 80–150 word explanatory target conflicts with the General Inquiry checklist's ≤120-word target. Resolve by applying domain-specific targets and prioritizing concise answer-first behavior.

## 5. Known limitations and remediation
| Priority | Finding | Required action |
|---|---|---|
| Critical | English-centric deterministic injection patterns in the uploaded guardrails | Add reviewed Urdu, Roman Urdu, Hindi and Arabic adversarial cases; do not claim equivalent deterministic coverage until tested |
| High | Multi-turn context persistence is caller-supplied; not proof of durable server-side state | Verify conversation ownership, persistence, tamper resistance, retention and cross-user isolation |
| High | Current uploaded repo lacks `tests/xictek_website_assistant/test_careers_grounding.py`, referenced by runner | Restore the missing test file or update runner to the actual repository layout |
| High | Runner stored under `internship/` although it expects repo-root-relative `tests/` paths | Place it under repository `scripts/` and validate from repo root |
| Medium | UX log's continuity summary overstates memory behavior | Report retrieval overlap and actual history forwarding as separate metrics |
| Medium | Two inquiry-flow turns failed content checks due weak retrieval | Improve domain routing/source selection; retain correct handoff logic |
| Medium | Contact support email/channel and response-time wording require current owner verification | Confirm official values before production |
| Medium | Mocked provider tests do not validate deployed widget/provider behavior | Add staging/live smoke tests with safe test data and consent |

## 6. Sign-off interpretation
The supplied lead report marks Day 7 as cleared. This consolidated package preserves that reported sign-off while distinguishing it from this review's execution status. No claim is made that the 102-test suite was rerun successfully in this environment. Production release should be conditional on the remediation items above, especially multilingual coverage, runner integrity, and live staging validation.
