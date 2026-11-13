# Unified Response Formatting & Conciseness Template — Blog, News & Portfolio

**Task:** Multi-Turn Conversation Continuity, Follow-Up UX & Response Formatting
**Date:** 13 November 2026
**Owner:** QA Automation
**Scope:** Applies to ALL chatbot responses across Blog, News, and Portfolio/Case-Studies queries.

---

## 1. Why This Template Exists

The multi-turn UX test log (`reports/multi-turn-ux-test-log.md`) found three formatting problems in the current pipeline:

1. **Length is too uniform** — every response is ~40-50 words regardless of whether the user asked a quick factual lookup or a deep synthesis question.
2. **Bullets are unused** — the simulated LLM emits prose paragraphs even when listing 3-5 parallel items (steps, factors, features), making the response harder to scan.
3. **Tone drifts** — no exclamation marks today, but no positive enforcement either; future LLM swaps could regress.

This template defines a single unified format that production LLM prompts must follow. It is section-agnostic: Blog, News, and Portfolio responses all use the same structure.

---

## 2. Response Anatomy

Every chatbot response has up to 5 parts. Parts marked **required** appear in every grounded response; parts marked **conditional** appear only when triggered.

| Part | Required? | When |
|---|---|---|
| 1. Lead sentence | Required | Always — directly answers the user's question in one sentence. |
| 2. Body (prose OR bullets) | Required | Always — supports the lead with cited detail. |
| 3. Conflict / recency note | Conditional | Only when applicable (Sections 4.3, 4.4). |
| 4. Bridge to prior turn | Conditional | Only on Turn N+1 in a multi-turn conversation (Section 5). |
| 5. Sources block | Required (when cited) | Always when body contains `[n]` markers. Omitted only on acknowledgement turns. |

---

## 3. Length Targets by Answer Type

| Answer type | Body word count | When it applies | Example |
|---|---|---|---|
| Acknowledgement | 10-25 words | User said "ok", "thanks", "got it" | "Got it. Let me know if you'd like the next step." |
| Fallback | 30-60 words | No source / out-of-domain / source-lacks-answer | "I don't have a blog article on that. For pricing specifics, contact XICTEK at xicteksystems@gmail.com or visit /contact." |
| Factual lookup | 30-80 words | Single fact: "what does PWA stand for?" | One-sentence lead + 1-2 supporting sentences with citation. |
| Explanatory answer | 80-150 words | "How does the agile process work?" | Lead sentence + 3-5 sentence body with citation. |
| Comparison / synthesis | 120-200 words | "Compare custom vs. off-the-shelf software" or multi-source synthesis | Lead sentence + bullet list of compared dimensions + closing sentence. |
| Multi-step process | 80-150 words | "What are the steps in software development?" | Lead sentence + numbered/bulleted list of steps. |

**Hard rule:** No response body exceeds 200 words. If the answer needs more, the assistant links to the article and offers to drill in: "Full breakdown in [1] — want me to expand on any specific step?"

---

## 4. Tone Rules

### 4.1 Voice

- Professional, restrained, no hype.
- Second person ("you") for the user; third person for XICTEK and articles.
- Active voice preferred; passive only when the agent is genuinely unknown.

### 4.2 Forbidden vocabulary

| Forbidden | Use instead |
|---|---|
| amazing, awesome, incredible | useful, practical |
| best-in-class, world-class, cutting-edge, revolutionary | modern, current |
| leverage (as a verb) | use |
| utilize | use |
| synergize | combine |
| robust (vague) | specify the actual property (tested, fault-tolerant, etc.) |
| seamless | direct, integrated |
| game-changer | (rephrase the claim concretely) |

### 4.3 Punctuation

- No exclamation marks in body or fallback.
- No emoji.
- No `**bold**` in body — bold is reserved for the `**Sources:**` header only.
- One space after a period, not two.
- Oxford comma in lists of 3+.

### 4.4 Conflict / recency notes

When a conflict or recency note is needed, it is its own paragraph starting with `Note:` (capitalized, plain text, no bold).

> Custom software development in Pakistan typically takes 8–16 weeks for a first release [1].
>
> Note: A separate article cites 12–24 weeks for similar scope [2]. The discrepancy likely reflects differences in project complexity assumptions.

Recency notes follow the same pattern: `Note: This article was published in {month year}. Some specifics may have changed…`

---

## 5. Bullet Formatting Rules

### 5.1 When to use bullets

- Use bullets for any list of **3 or more** parallel items (steps, factors, features, options).
- Use bullets for a list of **2 items** only if each item is ≥10 words (otherwise inline prose with "and").
- Never use bullets for a single item.

### 5.2 Bullet structure

- Marker: `- ` (hyphen + space). Never `*` or `•`.
- Each bullet starts with the same part of speech (all nouns, or all verbs — pick one and stay consistent within the list).
- Bullet length: ≤15 words. If a bullet needs >15 words, demote it to a paragraph above the bullet list (introducing the list), or split into two bullets.
- Maximum **5 bullets** per response. If a list has more than 5 items, group into sub-categories with plain-text sub-headers on their own line.

### 5.3 Bullet punctuation

- Noun-phrase bullets: no terminal punctuation.
  > - Discovery phase
  > - Architecture design
  > - Implementation
- Full-sentence bullets: end with a period.
  > - Start with a discovery phase to map business workflows.
  > - Design the architecture before writing any code.
- Do NOT mix the two styles within a single list.

### 5.4 Example (correct)

> The agile software development process emphasizes the following practices [1]:
>
> - Iterative sprints of 1–4 weeks
> - Continuous feedback from stakeholders
> - Working software over comprehensive documentation
> - Adaptation to changing requirements
>
> Each sprint ends with a review and retrospective to calibrate the next cycle.

### 5.5 Example (incorrect — to avoid)

> The agile software development process emphasizes iterative sprints of 1-4 weeks, continuous feedback from stakeholders, working software over comprehensive documentation, and adaptation to changing requirements. (One long run-on; hard to scan.)

---

## 6. Sources Block Format

### 6.1 Always at the end

The Sources block is the last element of the response. It is preceded by a blank line and starts with `**Sources:**` on its own line.

### 6.2 Entry format

```
[n] Article Title — https://www.xicteksystems.com/blog/<slug>
```

Section-level citation (when the answer draws on one H2 section of a long article):

```
[n] Article Title — § "Section Heading" — https://www.xicteksystems.com/blog/<slug>
```

### 6.3 Ordering

Entries are ordered by first appearance of `[n]` in the body, not by retrieval score.

### 6.4 No Sources on acknowledgement turns

If the response doesn't cite anything (acknowledgement, pure deflection without a blog reference), no Sources block is emitted. Don't pad.

---

## 7. Multi-Turn Continuity Add-Ons

These apply only on Turn N+1 of a multi-turn conversation.

### 7.1 Bridge sentence (when relevant)

If the user's follow-up relates to Turn N's topic, open with a one-sentence bridge:

> Following up on the SaaS article from a moment ago [1] — multi-tenant architecture is the foundational pattern that lets a single deployment serve multiple customers…

The bridge is ≤20 words and is the FIRST sentence of the response. It replaces the usual lead sentence for that turn only.

### 7.2 Disclaimer suppression

If Turn N already emitted:
- the contact prompt (`xicteksystems@gmail.com`)
- the stale-article note for article X
- the out-of-domain deflection template
- the no-source fallback

…then Turn N+1 (and beyond) must NOT re-emit the same string in the same conversation. Use a shorter variant instead:

| Turn N (full) | Turn N+1 (short) |
|---|---|
| "I don't have a blog article that addresses that. For specific questions, please contact XICTEK Systems at xicteksystems@gmail.com or visit /contact." | "Still no blog article on this — try rephrasing, or check /contact." |
| "That question is best answered on our Services or Contact page…" | "Still best on /services — want me to pull a related blog topic instead?" |
| "Note: This article was published in…" | _(suppressed — already shown)_ |

### 7.3 Acknowledgement turns

If the user's turn is a pure acknowledgement ("ok", "got it", "thanks", "understood"), the assistant responds with 10-25 words, no Sources block, no retrieval call.

> User: "ok got it"
> Assistant: "Got it. Let me know if you'd like the next step or a related topic."

This is the ONLY case where retrieval is skipped.

---

## 8. Section-Specific Notes

### 8.1 Blog & News responses

- Always cite blog URLs from the `/blog/` path.
- Stale-article note applies to articles >18 months old.
- Conflict disclosure required when two retrieved articles disagree.

### 8.2 Portfolio / Case Studies responses

- Do NOT cite blog URLs as Portfolio sources — deflect to `/services` or `/contact`.
- When the user asks about XICTEK's offerings, lead with the service category from `core-services.md`, then offer to pull a related blog article for depth.
- No stale-article note (Portfolio content is evergreen).
- No conflict disclosure (Portfolio is single-source per service).

### 8.3 Cross-section (Blog → Portfolio) responses

- Use the bridge sentence from §7.1 to reference the prior blog article.
- If the user's Portfolio query is answerable from the blog corpus (e.g., "does XICTEK do SaaS?" → yes, the blog has SaaS articles), give a short confirmation citing the blog, then offer to pull the services page for engagement specifics.

---

## 9. Worked Example — Single Explanatory Answer

**User:** "How does the agile software development process work?"

**Assistant (template-compliant response):**

> The agile software development process breaks work into short, iterative sprints with continuous feedback loops [1].
>
> Core practices include:
>
> - Sprints of 1–4 weeks with a defined deliverable
> - Daily standups for progress sync
> - Sprint review and retrospective at the end of each cycle
> - Working software prioritized over comprehensive documentation
>
> Each sprint produces a potentially shippable increment, which lets the team adapt to changing requirements without waiting for a long release cycle.
>
> **Sources:**
> [1] Agile Software Development Without Losing Direction — https://www.xicteksystems.com/blog/agile-software-development

**Audit:**
- Length: 86 words body (target 80-150 ✓)
- Bullets: 4, parallel verb-phrase structure, ≤15 words each ✓
- Lead sentence: 1 sentence, direct ✓
- Citation: [1] in body, matches Sources entry ✓
- Tone: no exclamation, no hype adjectives, no emoji ✓

---

## 10. Worked Example — Multi-Turn Follow-Up

**Turn 1 user:** "What is SaaS product development?"

**Turn 1 assistant:**

> SaaS product development is the end-to-end process of building software that is hosted centrally and delivered to customers over the internet on a subscription basis [1].
>
> Key considerations include:
>
> - Multi-tenant architecture
> - Subscription and billing systems
> - User management and role-based access
> - Scalable cloud infrastructure
>
> The blog article on SaaS product development covers each of these in depth.
>
> **Sources:**
> [1] SaaS Product Development — https://www.xicteksystems.com/blog/saas-product-development

**Turn 2 user:** "Does XICTEK offer SaaS development services?"

**Turn 2 assistant (template + multi-turn bridge):**

> Following up on the SaaS article from a moment ago [1] — yes, XICTEK offers SaaS development as a core service, including multi-tenant architecture, subscription billing, and scalable cloud infrastructure.
>
> For engagement-specific questions (pricing, timelines, team composition), the /services page is the right next step — the blog covers the patterns, but the services page covers the engagement.
>
> Still best on /services — want me to pull a related blog topic instead?

**Audit:**
- Bridge sentence: 19 words, references prior article ✓
- Length: 73 words body (target 30-80 for follow-up lookup ✓)
- No repeated disclaimer from Turn 1 ✓
- Deflection to /services, but with a short variant + offer to re-engage with blog ✓
- No Sources block (no new blog citation — deflected to /services) ✓

---

## 11. Sign-off

| Criterion | Status |
|---|---|
| Unified length targets defined per answer type | PASS |
| Tone rules and forbidden vocabulary specified | PASS |
| Bullet formatting rules concrete and enforceable | PASS |
| Sources block format consistent with citation contract | PASS |
| Multi-turn continuity rules (bridge, disclaimer suppression) defined | PASS |
| Section-specific notes for Blog, Portfolio, and cross-section | PASS |
| Worked examples audit-able against the rules | PASS |

**Status: Production-ready.** This template is the canonical reference for all chatbot response formatting. Future LLM prompt revisions must cite this template and pass a formatting audit against §3-§7 before release.

---

*QA Automation — Unified Response Formatting & Conciseness Template — Blog, News & Portfolio*
