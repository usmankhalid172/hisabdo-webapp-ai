# Grounded Generation & Citations — Blog & News Section

**Owner:** QA Automation
**Task:** Grounded Generation & Citations — Blog & News Section
**Date:** 28 October 2026

---

## 1. Objective

Align prompts and response handling with retrieved blog and news sources. Display relevant source links and sections, provide citations only when the sources genuinely support the answer, and clearly explain conflicts when multiple sources provide contradictory information. Define fallback mechanisms for the Blog & News domain.

This spec consumes the retrieval pipeline tuned in the previous task (Hybrid α=0.5 + normalization, threshold=0.15, top-k=3) and defines how the LLM should use those retrieved articles to generate grounded, citation-backed responses.

**Companion implementation:** `/home/z/my-project/scripts/blog_grounded_generation.py` — runnable Python module that implements this spec against the live retriever and the 47 cleaned blog articles.

---

## 2. Aligned Prompts

### 2.1 System Prompt

The system prompt is sent once at the start of a conversation. It establishes the assistant's role, the citation contract, and the failure modes the assistant must avoid.

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

### 2.2 User Prompt Template

For each user turn, the retrieval pipeline fetches the top-k articles and assembles a context block. The user prompt template wraps the user's question with the retrieved context.

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

### 2.3 Prompt Alignment Notes

- The system prompt is sent **once** at conversation start; the user prompt template is sent **per turn** with fresh retrieval results.
- The retrieval pipeline (Hybrid α=0.5 + normalization, threshold=0.15, k=3) supplies at most 3 articles per turn. This keeps the context window small and forces the model to be selective about citations.
- Article bodies are passed as cleaned text (promotional sidebars, CTAs, JSON-LD schema, and duplicate paragraphs already removed by the previous Content Cleaning task).
- The similarity score is included in the context so the model can calibrate confidence — but the model is instructed to use the score only as a tiebreaker, not as a substitute for actually reading the article.

---

## 3. Citation-Handling Rules

### 3.1 When to Cite

| Situation | Action |
|---|---|
| Claim is a direct paraphrase of source text | Cite `[n]` after the claim |
| Claim is a verbatim quote from source text | Wrap in `"..."` and cite `[n]` after the closing quote |
| Claim is a numerical fact (price, time, count) from source | Cite `[n]` — numbers always need citations |
| Claim is a recommendation or conclusion drawn from source | Cite `[n]` — even interpretations need grounding |
| Claim is general knowledge (e.g. "React is a JavaScript library") | No citation needed — but do not extend with XICTEK-specific claims |
| Claim is the assistant's own structural framing ("There are three main considerations...") | No citation needed — but each substantive point under it must be cited |

### 3.2 When NOT to Cite

- **Do not cite** if the article was retrieved but not actually used. Padding the Sources list with unused articles undermines trust in the citations that are real.
- **Do not cite** a different article than the one that supports the claim. If article [2] supports a claim, cite `[2]`, not `[1]`.
- **Do not cite** the same article multiple times for the same claim. One citation per claim is enough.
- **Do not cite** out-of-scope URLs (/services, /contact, hisabdo.app, LinkedIn profiles). These are blocked by the scope rules in Section 2.1.

### 3.3 Citation Format

Inline citations use square-bracketed numbers: `[1]`, `[2]`, `[3]`. Numbers are assigned in the order articles first appear in the response.

Example:

> Custom software development in Pakistan typically starts with a discovery phase to map the business workflow before any code is written [1]. The cost varies based on scope, complexity, and team composition [2].

Sources section at the end:

> **Sources:**
> [1] Custom Software Development Guide for Growing Businesses — https://www.xicteksystems.com/blog/custom-software-development-guide
> [2] Software Development Cost in Pakistan: What Shapes the Budget — https://www.xicteksystems.com/blog/software-development-cost-pakistan

### 3.4 Section-Level Citations

When the response draws on a specific section of a long article (the "12 min read" guides are ~1,200 words with multiple H2 sections), include the section heading in the Sources entry:

> [1] Custom Software Development Guide for Growing Businesses — § "Start with the outcome, not the tool" — https://www.xicteksystems.com/blog/custom-software-development-guide

This helps the user verify the claim by jumping to the right section rather than scanning the whole article.

---

## 4. Conflict Resolution

### 4.1 Detection

A conflict exists when two retrieved articles make claims that cannot both be true — for example, different cost ranges, different recommended technology stacks, or different process step counts. The detection logic runs in the response post-processor (see `blog_grounded_generation.py`, function `detect_conflicts()`).

### 4.2 Resolution: Disclose and Cite Both

When a conflict is detected, the assistant must NOT silently pick one source. Instead:

1. **Lead with the stronger source.** Strength is determined by:
   - Higher similarity score (primary)
   - More recent publish date (secondary)
   - More specific to the user's question (tertiary — judged by the LLM)
2. **Add a "Note:" line** disclosing the conflict and citing the second source.

Example:

> Custom software development in Pakistan typically takes 8–16 weeks for a first release [1].
>
> Note: A separate article cites 12–24 weeks for similar scope [2]. The discrepancy likely reflects differences in project complexity assumptions; both articles agree that timeline estimates require a discovery phase first.

### 4.3 When to Refuse Instead of Disclose

If the conflict is **material and unresolvable** (e.g., one article says "always use server-side rendering" and another says "always use client-side rendering"), the assistant should refuse to pick and instead present both positions:

> The retrieved sources give conflicting guidance on this point. Article [1] recommends X for reason A. Article [2] recommends Y for reason B. Both are legitimate approaches; the right choice depends on your specific constraints. I'd suggest reading both articles and consulting with XICTEK Systems for a recommendation tailored to your situation.

### 4.4 What Counts as a Conflict

- Different numerical claims (price, time, count, percentage)
- Different categorical recommendations (use framework A vs. use framework B)
- Different process descriptions (5 steps vs. 7 steps)

### 4.5 What Does NOT Count as a Conflict

- Two articles covering the same topic from different angles (complementary, not contradictory)
- One article being more specific than another (generalization, not contradiction)
- Different wording for the same idea (paraphrase, not contradiction)

---

## 5. Fallback Mechanisms

Six fallback scenarios are defined for the Blog & News domain. Each has a detection condition, a response template, and a logging hook for monitoring.

### 5.1 No Source Above Threshold

**Detection:** Retrieval returns 0 articles with similarity score ≥ 0.15.

**Response template:**
> I don't have a blog article that addresses that. For specific questions, please contact XICTEK Systems at xicteksystems@gmail.com or visit [/contact](https://www.xicteksystems.com/contact).

**Log:** `FALLBACK_NO_SOURCE | query="{query}" | top_score={top_score}`

### 5.2 Out-of-Domain Query

**Detection:** The user's question is about pricing, services, contact info, or careers — topics the blog doesn't cover. Detected via keyword match: `price`, `cost of service`, `hire you`, `contact`, `phone number`, `address`, `career`, `job`, `apply`.

**Response template:**
> That question is best answered on our [Services](https://www.xicteksystems.com/services) or [Contact](https://www.xicteksystems.com/contact) page rather than in the blog. I'd suggest starting there — or if you'd like, I can answer a related question from our blog articles.

**Log:** `FALLBACK_OUT_OF_DOMAIN | query="{query}" | matched_keywords={kws}`

### 5.3 Source-Scope Violation (Day-1 Failure Prevention)

**Detection:** Before returning any URL to the user, the post-processor checks each URL against an allowlist: `^https://www\.xicteksystems\.com/blog/[a-z0-9-]+$`. Any URL that doesn't match is stripped from the response.

**Hard allowlist:**
- `www.xicteksystems.com/blog/<slug>` — approved
- `www.xicteksystems.com/services` — blocked (use Section 5.2 fallback)
- `www.xicteksystems.com/contact` — blocked (use Section 5.2 fallback)
- `hisabdo.app` — blocked (different product)
- `linkedin.com`, `facebook.com`, etc. — blocked (social profiles)

**Log:** `FALLBACK_SCOPE_VIOLATION | query="{query}" | blocked_url="{url}"`

This rule directly prevents the Day-1 audit failures where the chatbot returned `/services` URLs and `hisabdo.app` URLs in blog responses.

### 5.4 Source Lacks Answer

**Detection:** The retrieved article is topically related (similarity ≥ 0.15) but does not actually contain information that answers the user's question. Detected by the LLM in the generation step — the system prompt instructs it to refuse if the articles don't support an answer.

**Response template:**
> I found an article that's related to your question — [Article Title](url) — but it doesn't directly address what you're asking. If you can rephrase or be more specific, I can try again. Otherwise, the XICTEK Systems team can help directly at xicteksystems@gmail.com.

**Log:** `FALLBACK_SOURCE_LACKS_ANSWER | query="{query}" | retrieved_slug="{slug}" | score={score}`

### 5.5 Multiple Equally-Good Sources

**Detection:** Two or more articles have similarity scores within 0.05 of each other AND both scores are ≥ 0.20 (well above threshold).

**Response strategy:** Synthesize across sources with multiple citations, rather than picking one. Each substantive claim gets the citation(s) of the article(s) that support it.

**Example:**
> Both the Custom Software Development Guide [1] and the Software Development Process guide [2] emphasize starting with discovery before implementation. The first focuses on business outcome framing [1], while the second details the milestone structure [2].

**Log:** `FALLBACK_MULTIPLE_EQUAL | query="{query}" | slugs={slug1, slug2} | scores={s1, s2}`

### 5.6 Stale Article

**Detection:** The retrieved article was published more than 18 months ago (configurable). At time of writing (October 2026), articles published before April 2025 are flagged.

**Response strategy:** Answer normally with citation, but append a recency note:

**Note template:**
> Note: This article was published in {month year}. Some specifics (technology versions, pricing) may have changed since then — confirm with XICTEK Systems for current information.

**Log:** `FALLBACK_STALE_ARTICLE | query="{query}" | slug="{slug}" | publish_date="{date}"`

---

## 6. Implementation Reference

The Python implementation is at `/home/z/my-project/scripts/blog_grounded_generation.py`. It provides:

- `SYSTEM_PROMPT` — the system prompt from Section 2.1 as a string constant
- `build_user_prompt(query, retrieved_articles)` — assembles the user prompt from Section 2.2
- `format_citation(article, section=None)` — formats a single Sources entry per Section 3.3/3.4
- `detect_conflicts(response, cited_articles)` — runs the conflict detection from Section 4.1
- `check_scope_violations(response)` — enforces the URL allowlist from Section 5.3
- `apply_fallback(query, retrieved_articles)` — routes to the appropriate fallback per Sections 5.1–5.6
- `generate_grounded_response(query, llm_client=None)` — the main entry point: calls the retriever from yesterday's evaluation, builds the prompt, calls the LLM, post-processes for citations/conflicts/scope, and returns the final response

The module can be run standalone to test against the 47 cleaned blog articles:

```bash
python3 /home/z/my-project/scripts/blog_grounded_generation.py
```

This runs a small test suite of 5 sample queries (including 2 Day-1 failure patterns) and prints the generated responses with citations, conflict disclosures, and fallback handling applied.

---

## 7. Decision Flow

```
User query
   │
   ▼
[1] Out-of-domain? ──── yes ──→ Fallback 5.2 (deflect to /services or /contact)
   │
   no
   │
   ▼
[2] Retrieve top-k=3 via Hybrid α=0.5 + normalization, threshold=0.15
   │
   ▼
[3] Any source ≥ 0.15? ── no ────→ Fallback 5.1 (no source above threshold)
   │
   yes
   │
   ▼
[4] Build user prompt with retrieved articles
   │
   ▼
[5] Call LLM with system prompt + user prompt
   │
   ▼
[6] Post-process response:
    a. Check scope violations ──→ strip blocked URLs (Fallback 5.3)
    b. Detect conflicts ──→ add "Note:" disclosures (Section 4)
    c. Check for stale articles ──→ append recency note (Fallback 5.6)
    d. Check for "multiple equal sources" ──→ verify multi-citation (Fallback 5.5)
   │
   ▼
[7] Return response to user
   │
   ▼
[8] Log: query, retrieved slugs, scores, fallbacks triggered, response
```

---

## 8. Monitoring Hooks

Each fallback and conflict disclosure logs a structured event. Recommended dashboard:

| Metric | Source | Target |
|---|---|---|
| Fallback rate (5.1) | `FALLBACK_NO_SOURCE` logs | < 15% of queries |
| Out-of-domain rate (5.2) | `FALLBACK_OUT_OF_DOMAIN` logs | < 10% (higher = blog isn't covering what users ask) |
| Scope violations blocked (5.3) | `FALLBACK_SCOPE_VIOLATION` logs | Should be 0 after fix; non-zero = LLM ignoring system prompt |
| Source-lacks-answer rate (5.4) | `FALLBACK_SOURCE_LACKS_ANSWER` logs | < 10% (higher = retrieval is too liberal) |
| Multi-source synthesis rate (5.5) | `FALLBACK_MULTIPLE_EQUAL` logs | Track but no target — informational |
| Stale-article rate (5.6) | `FALLBACK_STALE_ARTICLE` logs | < 5% (higher = content needs refresh) |
| Conflict disclosure rate | `CONFLICT_DISCLOSED` logs | Track — high rate may indicate content contradictions to fix |

Review weekly. Spikes in any metric trigger content or prompt revisions.

---

## 9. Reproduction

```bash
# Run the test suite (5 sample queries, prints grounded responses with citations)
python3 /home/z/my-project/scripts/blog_grounded_generation.py

# Inspect the retrieval pipeline this spec consumes
cat /home/z/my-project/scripts/blog_retrieval_evaluation.py | head -100

# Re-read the cleaned blog articles this spec draws on
ls /home/z/my-project/download/blog/
```

---

*QA Automation — Grounded Generation & Citations — Blog & News Section*
