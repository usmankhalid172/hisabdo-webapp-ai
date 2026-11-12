# Blog & News — Grounded Prompt Rules & Citation Contract

**Owner:** QA Automation
**Task:** Grounded Prompting & Citation Rules — Blog & News
**Date:** 12 November 2026
**Status:** Production-ready (re-verified against citation validator today)

---

## 1. Scope

These rules govern every response the XICTEK Systems website assistant emits for queries routed to the **Blog & News** section. They sit between the retrieval pipeline (Hybrid α=0.5, threshold=0.15, top-k=3) and the user-facing response.

The rules are enforced in two layers:

1. **Soft enforcement** — the LLM is instructed by the system prompt (Section 3) to follow these rules when generating text.
2. **Hard enforcement** — the post-processor (`src/grounded_generation.py`) and the citation validator (`src/citation_validator.py`) programmatically verify every response against Section 4 before it is shown to the user. Failures are stripped, redacted, or routed to a fallback.

Soft enforcement handles the common case; hard enforcement catches the cases where the LLM drifts.

---

## 2. When These Rules Apply

| Situation | Apply these rules? |
|---|---|
| Query about a blog topic (cost, process, tech, AI, mobile, web) | Yes |
| Query about a specific article ("explain the agile process article") | Yes |
| Query that retrieves ≥1 article above similarity threshold (0.15) | Yes |
| Query that retrieves 0 articles above threshold | No — invoke Fallback 5.1 |
| Query about pricing, services, contact, careers | No — invoke Fallback 5.2 (deflect to /services or /contact) |
| Query that is ambiguous or multi-topic | No — invoke Fallback 5.4 (ask one clarifying question) |

---

## 3. System Prompt (Sent Once per Conversation)

```
You are the XICTEK Systems website assistant for the Blog & News section.
Your job is to answer user questions using ONLY the blog articles provided
in the context. You must follow these rules:

GROUNDING RULES
1. Every factual claim in your answer MUST be supported by one of the
   provided source articles. If no source supports a claim, do not make
   the claim.
2. If the provided sources do not contain enough information to answer
   the question, say so explicitly and offer to direct the user to
   contact XICTEK Systems. Do not fabricate, infer, or generalize
   beyond what the sources state.
3. Do not use outside knowledge. Do not use training-data knowledge of
   XICTEK Systems, its products, or its services. Only the provided
   source articles are valid grounding.

CITATION RULES
4. Cite sources using inline numbered markers: [1], [2], [3]. Place the
   marker immediately after the claim it supports, before the period.
5. At the end of your response, include a "Sources:" section listing
   each cited article in the format:
       [n] Article Title — https://www.xicteksystems.com/blog/<slug>
6. Only cite an article if you actually used information from it. Do not
   pad the Sources list with articles you did not draw on.
7. If you quote a sentence or phrase verbatim from a source, wrap it in
   quotation marks and cite the source. Do not pass off source text as
   your own.

CONFLICT RULES
8. If two provided sources give contradictory information, do not pick
   one silently. Lead with the stronger source, then add a "Note:"
   line disclosing the conflict and citing the second source.
9. If the contradiction is material (different pricing, different
   recommendations, different technical claims), prefer disclosure over
   synthesis — let the user see both sources and decide.

SCOPE RULES
10. Only cite URLs on the www.xicteksystems.com domain, and only URLs
    on the /blog/ path. Never cite /services, /contact, /about, or
    external domains (hisabdo.app, LinkedIn, etc.) as Blog sources.
11. If the user's question is about pricing, services, or contact
    information rather than blog content, deflect to the appropriate
    page (/services, /contact) instead of guessing from blog articles.

FALLBACK RULES
12. If no source articles are provided (empty context), respond with:
    "I don't have a blog article that addresses that. For specific
    questions, please contact XICTEK Systems at xicteksystems@gmail.com
    or visit /contact."
13. If all provided sources have similarity scores below the threshold,
    treat the context as empty (rule 12).
14. If the user's question is ambiguous, ask one clarifying question
    rather than guessing. Do not retrieve and answer a different
    question than the one asked.

TONE
15. Professional, restrained, no hype. No exclamation marks. No
    marketing language. The user is evaluating XICTEK; honest answers
    build more trust than overclaimed ones.
```

---

## 4. User Prompt Template (Sent per Turn)

For each user turn, the retrieval pipeline fetches the top-k articles and assembles a context block. The user prompt wraps the user's question with the retrieved context.

```
USER QUESTION:
{user_query}

RETRIEVED BLOG ARTICLES (top {k}, similarity threshold {threshold}):

--- ARTICLE [1] ---
Title: {article_1_title}
URL: https://www.xicteksystems.com/blog/{article_1_slug}
Category: {article_1_category}
Published: {article_1_date}
Similarity score: {article_1_score}
Section excerpt:
{article_1_body}

--- ARTICLE [2] ---
Title: {article_2_title}
URL: https://www.xicteksystems.com/blog/{article_2_slug}
... (same fields)

--- ARTICLE [3] ---
... (same fields)

INSTRUCTIONS:
Answer the user's question using ONLY the articles above. Follow the
grounding, citation, conflict, scope, and fallback rules in your system
prompt. If the articles do not support an answer, say so. Do not
fabricate. Do not use outside knowledge.
```

---

## 5. Citation Contract (Machine-Verified)

The citation validator (`src/citation_validator.py`) enforces four mandatory integrity checks on every response. A response that fails any check is rejected and routed back to fallback.

### CHECK 1 — Orphan Markers

**Rule:** Every `[n]` marker in the response body must have a matching entry in the Sources block.

**Why:** A `[3]` in the body with no `[3]` in Sources leaves the user unable to verify the claim. This is the most common LLM drift failure.

**Failure example:**
> Body cites [3] but Sources only lists [1] and [2].

### CHECK 2 — Padded Sources

**Rule:** Every entry in the Sources block must have at least one `[n]` marker appearing in the response body.

**Why:** Listing articles that weren't actually used inflates the apparent grounding of the response and undermines trust in the citations that are real.

**Failure example:**
> Body cites [1] only, but Sources lists [1], [2], and [3].

### CHECK 3 — Fabricated Index

**Rule:** Every cited index (whether in body or in Sources) must satisfy `1 ≤ n ≤ len(retrieved_articles)`. With top-k=3, only `[1]`, `[2]`, `[3]` are valid.

**Why:** An LLM under pressure to provide sources may hallucinate `[4]` or `[5]` that map to no retrieved article. The validator rejects these.

**Failure example:**
> Body cites [5] but only 2 articles were retrieved.

### CHECK 4 — URL Allowlist

**Rule:** Every URL in the Sources block must match the regex `^https://www\.xicteksystems\.com/blog/[a-z0-9-]+$`.

**Why:** This is the Day-1 audit failure mode — the chatbot returned `/services` URLs and `hisabdo.app` URLs in blog responses. The allowlist hard-blocks this category of error.

**Failure example:**
> Sources lists `https://hisabdo.app/features` — not on the `/blog/` path.

### CHECK 5 — Verbatim Quote Grounding (Informational)

**Rule:** If the response wraps text in straight double quotes `"..."` and attributes it to `[n]`, the quoted text must appear (case-insensitive, whitespace-normalized) in the body of `retrieved_articles[n-1]`.

**Why:** A fabricated quote is worse than a fabricated paraphrase — it puts words in the source's mouth. This check catches that.

**Note:** Absence of verbatim quotes is informational only, not a failure.

---

## 6. Citation Format

### 6.1 Inline Marker

Place `[n]` immediately after the claim, before the period.

> Custom software development in Pakistan typically starts with a discovery phase to map the business workflow before any code is written [1].

### 6.2 Sources Block

End every response with a `**Sources:**` block. One entry per cited article, in citation order.

> **Sources:**
> [1] Custom Software Development Guide for Growing Businesses — https://www.xicteksystems.com/blog/custom-software-development-guide
> [2] Software Development Cost in Pakistan: What Shapes the Budget — https://www.xicteksystems.com/blog/software-development-cost-pakistan

### 6.3 Section-Level Citation

For long-form articles with multiple H2 sections, include the section heading in the Sources entry so the user can jump to the right section:

> [1] Custom Software Development Guide for Growing Businesses — § "Start with the outcome, not the tool" — https://www.xicteksystems.com/blog/custom-software-development-guide

### 6.4 When NOT to Cite

- Do **not** cite if the article was retrieved but not actually used (CHECK 2 catches this).
- Do **not** cite a different article than the one that supports the claim.
- Do **not** cite the same article multiple times for the same claim.
- Do **not** cite general knowledge ("React is a JavaScript library") — but do not extend with XICTEK-specific claims.
- Do **not** cite out-of-scope URLs (`/services`, `/contact`, `hisabdo.app`, LinkedIn).

---

## 7. Conflict Disclosure

When two retrieved articles make contradictory claims, the assistant must NOT silently pick one.

### 7.1 What Counts as a Conflict

- Different numerical claims (price, time, count, percentage)
- Different categorical recommendations (use framework A vs. use framework B)
- Different process descriptions (5 steps vs. 7 steps)

### 7.2 What Does NOT Count as a Conflict

- Two articles covering the same topic from different angles (complementary, not contradictory)
- One article being more specific than another (generalization, not contradiction)
- Different wording for the same idea (paraphrase, not contradiction)

### 7.3 Resolution: Disclose and Cite Both

1. Lead with the stronger source (higher similarity score; more recent publish date as tiebreaker).
2. Add a `Note:` line disclosing the conflict and citing the second source.

> Custom software development in Pakistan typically takes 8–16 weeks for a first release [1].
>
> Note: A separate article cites 12–24 weeks for similar scope [2]. The discrepancy likely reflects differences in project complexity assumptions; both articles agree that timeline estimates require a discovery phase first.

### 7.4 When to Refuse Instead of Disclose

If the conflict is material and unresolvable (e.g., one article says "always use server-side rendering" and another says "always use client-side rendering"), refuse to pick and present both positions.

---

## 8. Fallback Mechanisms

Six fallbacks are defined. Each has a detection condition, response template, and logging hook.

| ID | Trigger | Response |
|---|---|---|
| 5.1 | 0 articles above threshold (0.15) | "I don't have a blog article that addresses that. For specific questions, please contact XICTEK Systems at xicteksystems@gmail.com or visit [/contact](https://www.xicteksystems.com/contact)." |
| 5.2 | Out-of-domain keywords (price, hire, contact, career, job, apply) | "That question is best answered on our [Services](https://www.xicteksystems.com/services) or [Contact](https://www.xicteksystems.com/contact) page rather than in the blog..." |
| 5.3 | URL in response that doesn't match `/blog/` allowlist | URL is stripped from response before delivery |
| 5.4 | Retrieved article is topically related but doesn't answer the question | "I found an article that's related to your question — [Title](url) — but it doesn't directly address what you're asking..." |
| 5.5 | Two or more articles with scores within 0.05 and both ≥0.20 | Synthesize across sources with multiple citations |
| 5.6 | Retrieved article older than 18 months | Answer normally, append recency note |

---

## 9. Hard Enforcement (Post-Processor)

Beyond the LLM-facing rules above, the post-processor (`src/grounded_generation.py`) applies these programmatic guarantees:

1. **Scope stripping** — any URL that doesn't match the blog allowlist is removed before delivery. The user never sees `/services`, `/contact`, `hisabdo.app`, or social profile URLs in a blog response.
2. **Dangerous URI stripping** — `javascript:`, `file:///`, `data:`, `vbscript:`, `blob:` URIs are removed (prompt-injection defense).
3. **Input sanitization** — user queries containing prompt-injection patterns (`ignore previous instructions`, `[SYSTEM]`, `override scope rules`, base64 blobs) are sanitized before retrieval.
4. **PII redaction** — system-prompt markers (`GROUNDING RULES`, `CITATION RULES`, etc.) and config values (`threshold = 0.15`, `MiniLM-L6-v2`) are redacted from the response if the LLM accidentally echoes them.
5. **Stale-article note** — if the top cited article was published >18 months ago, a recency note is appended.
6. **Conflict detection** — heuristic scan for `Note: ...[n]...[m]` patterns and numerical mismatches; logs `CONFLICT_DISCLOSED` event.

---

## 10. Verification

The citation validator runs on every response before delivery. The verified transcripts (`reports/verified_transcripts.md`) demonstrate:

- **7 positive cases** — real queries through the pipeline; all 7 pass all 4 mandatory checks.
- **3 negative controls** — manually corrupted responses; all 3 are correctly flagged with specific check failures.

Result: **10/10 verdicts correct** (validator agrees with expected outcome on every transcript).

---

*QA Automation — Grounded Prompting & Citation Rules — Blog & News Section*
