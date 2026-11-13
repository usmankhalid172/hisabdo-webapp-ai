# Conversational Refinement Checklist — Blog, News & Portfolio

**Task:** Multi-Turn Conversation Continuity, Follow-Up UX & Response Formatting
**Date:** 13 November 2026
**Owner:** QA Automation
**Companion artifact:** `reports/multi-turn-ux-test-log.md` (test results that motivated this checklist)

---

## How to Use This Checklist

For each multi-turn conversation scenario, run through every item below. A scenario passes only when all `MUST` items are satisfied. `SHOULD` items are recommended but not blocking.

Mark each item: **PASS** / **FAIL** / **N/A** (with reason).

---

## Section A — Context Preservation Across Turns

| # | Rule | Priority | How to verify |
|---|---|---|---|
| A1 | Turn N+1 must acknowledge the topic of Turn N when the user's follow-up is a drilldown (e.g., "what about in Pakistan?" after a cost question). | MUST | Response contains a phrase like "Following up on…" or "As the previous article noted…" OR cites the same article as Turn N when relevant. |
| A2 | If Turn N retrieved article X and Turn N+1 retrieves the same article X, the response must NOT re-introduce it from scratch. | MUST | Response references prior citation (e.g., "As noted in [1] earlier…") instead of "Based on the X article [1]…". |
| A3 | If Turn N triggered a fallback (e.g., out-of-domain deflect to /services), Turn N+1 on the same topic must NOT re-trigger the same deflect unless the user's query materially changed scope. | MUST | Same fallback code (e.g., `5.2_OUT_OF_DOMAIN`) does NOT appear in two consecutive turns unless the second query contains new out-of-domain keywords. |
| A4 | If the user acknowledges a prior answer ("ok", "got it", "thanks"), the assistant should not restate the prior answer. | SHOULD | Acknowledgement turns produce a short confirmation (≤20 words), not a fresh retrieval. |
| A5 | Cross-section transitions (Blog → Portfolio) must explicitly bridge: "You were reading about SaaS development in our blog — here's how that relates to our services…". | MUST | Cross-section follow-up responses include a one-sentence bridge to the prior section. |

---

## Section B — Disclaimer Deduplication

| # | Rule | Priority | How to verify |
|---|---|---|---|
| B1 | The contact prompt ("contact XICTEK Systems at xicteksystems@gmail.com") must appear at most once per conversation, not once per turn. | MUST | Across all turns of a conversation, the contact prompt string appears ≤1 time total. |
| B2 | The stale-article recency note ("Note: This article was published in…") must appear at most once per cited article per conversation. | MUST | If article X is cited in Turns 1 and 3, the recency note for X appears only in Turn 1. |
| B3 | The out-of-domain deflection template must NOT be repeated if the user's follow-up is still out-of-domain — instead, a shorter acknowledgement ("Still best answered on /services — anything specific I can pull from the blog?"). | MUST | Identical deflection string does not appear in two consecutive turns. |
| B4 | The no-source fallback ("I don't have a blog article that addresses that…") must NOT repeat if Turn N already said the same thing. | MUST | Identical fallback string does not appear in two consecutive turns. |
| B5 | Conflict disclosures ("Note: A separate article cites…") can repeat across turns if a different conflict is disclosed, but the SAME conflict notice must appear only once per conversation. | SHOULD | Same conflict pair (same two article indices) disclosed ≤1 time per conversation. |

---

## Section C — Tone & Length Consistency

| # | Rule | Priority | How to verify |
|---|---|---|---|
| C1 | Response length for a single factual lookup: 30-80 words (body only, excluding Sources block). | MUST | `word_count` of body is in [30, 80]. |
| C2 | Response length for an explanatory answer: 80-150 words. | MUST | `word_count` of body is in [80, 150]. |
| C3 | Response length for a comparison/synthesis answer (multi-source): 120-200 words. | MUST | `word_count` of body is in [120, 200]. |
| C4 | Length drift across turns of the same conversation: ≤75 words (max − min). | MUST | `max(word_counts) − min(word_counts) ≤ 75` per conversation. |
| C5 | Tone is professional, restrained, no hype. No exclamation marks. No marketing adjectives ("amazing", "best-in-class", "world-class"). | MUST | Scan response for `!`, `amazing`, `world-class`, `best-in-class`, `cutting-edge`, `revolutionary` → 0 hits. |
| C6 | Sentence length: average 12-22 words/sentence. Avoid run-ons (>30 words). | SHOULD | `avg_sentence_length` is in [12, 22]; no sentence >30 words. |
| C7 | No emoji, no Markdown emphasis (`**bold**`) in body — bold is reserved for the `**Sources:**` header only. | MUST | Body contains no `**` (except in Sources header) and no emoji characters. |

---

## Section D — Bullet Formatting Adherence

| # | Rule | Priority | How to verify |
|---|---|---|---|
| D1 | Enumerations of 3+ items must use bullet points, not prose. | MUST | If the response lists 3+ parallel items (steps, features, factors), it uses `- ` bullets. |
| D2 | Enumerations of 1-2 items should stay in prose. | SHOULD | Bullets are not used for 1-2 item lists. |
| D3 | Bullet items must be parallel in structure (all noun phrases, or all verb phrases — not mixed). | MUST | All bullets in a list start with the same part of speech. |
| D4 | Bullets should be ≤15 words each. If a bullet needs >15 words, it's a paragraph, not a bullet. | SHOULD | Each bullet line is ≤15 words. |
| D5 | Maximum 5 bullets per response. If a list is longer, group into sub-categories with bold sub-headers (but body bold is forbidden by C7 — so use plain sub-headers like "Process:" on its own line). | MUST | Total bullet count per response ≤5. |
| D6 | Bullets must end with no terminal punctuation if they are noun phrases; end with a period if they are full sentences. | SHOULD | Bullet punctuation is internally consistent within a single list. |

---

## Section E — Citation Continuity

| # | Rule | Priority | How to verify |
|---|---|---|---|
| E1 | Inline markers `[n]` must follow the citation contract from the grounded-prompt-rules spec (orphan-free, padding-free, URL-allowlisted). | MUST | Citation validator passes (`overall_pass = True`). |
| E2 | If Turn N cited article [1] and Turn N+1 cites the same article, Turn N+1 may either (a) keep the same index [1] for continuity OR (b) renumber — but the Sources block must list the article. | MUST | Article appears in Sources block of every turn where it's cited in body. |
| E3 | Sources block must NOT list articles already cited in Turn N unless they're cited again in Turn N+1. | MUST | Padded-source check passes (CHECK 2 from validator). |
| E4 | When a user asks a follow-up that doesn't need a citation (e.g., "thanks" or "ok"), no Sources block is emitted. | SHOULD | Acknowledgement turns have no Sources block. |

---

## Section F — Fallback Continuity

| # | Rule | Priority | How to verify |
|---|---|---|---|
| F1 | A fallback triggered in Turn N must influence Turn N+1's behavior — the assistant should remember it doesn't have data on this topic and either ask a clarifying question or suggest a related blog topic. | MUST | If Turn N triggers `5.1_NO_SOURCE`, Turn N+1 on a related query does NOT trigger `5.1_NO_SOURCE` again without first offering to clarify. |
| F2 | When a fallback fires, the assistant must offer ONE concrete next step (rephrase suggestion, related topic, or contact link) — not just say "I can't help". | MUST | Fallback response contains ≥1 of: a rephrase suggestion, a related blog topic name, or a /contact link. |
| F3 | Fallback responses should be ≤60 words (shorter than a normal answer) — the user knows it's a miss, no need to over-explain. | SHOULD | Fallback response body word count ≤60. |

---

## Section G — Cross-Section (Blog ↔ Portfolio) Continuity

| # | Rule | Priority | How to verify |
|---|---|---|---|
| G1 | When the user moves from a Blog query to a Portfolio/Services query on the same topic (e.g., "what is SaaS" → "does XICTEK offer SaaS services"), Turn 2 must reference the blog article from Turn 1 as context. | MUST | Turn 2 response mentions the prior article title OR includes a phrase like "As our blog article noted…". |
| G2 | Portfolio/Services responses must NOT cite blog URLs as Portfolio sources — they deflect to /services or /contact per the scope rules. | MUST | Scope check (CHECK 4 from validator) passes; no /blog/ URLs in Portfolio responses. |
| G3 | When the user moves from Portfolio to Blog ("you mentioned SaaS services — tell me more about SaaS platforms"), the Blog response should retrieve the SaaS-platforms article first. | SHOULD | Top-1 retrieved article in Turn 2 matches the topic of Turn 1's Portfolio response. |

---

## Scoring

- **PASS**: All MUST items satisfied for the scenario.
- **CONDITIONAL**: All MUST items satisfied except ≤2 SHOULD items.
- **FAIL**: Any MUST item fails.

Record results per scenario in the test log. A scenario that FAILS must be re-tested after the pipeline is patched.

---

## Sign-off

| Criterion | Status |
|---|---|
| Checklist covers context preservation, disclaimer dedup, tone/length, bullets, citations, fallbacks, cross-section | PASS |
| Each item has a clear PASS/FAIL verification method | PASS |
| Tied to actual test results in `multi-turn-ux-test-log.md` | PASS |

---

*QA Automation — Conversational Refinement Checklist — Blog, News & Portfolio*
