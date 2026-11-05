# Portfolio Domain Failure Log

**Owner:** Muhammad Mohsin  
**Review date:** 2026-11-05  
**Scope:** Portfolio and case-study retrieval against the existing 12-query benchmark  
**Purpose:** Record weak retrieval behavior and prioritize source-cleaning work for Phase 2.

## Executive summary

The reproducible benchmark is a lexical passage-retrieval test over 1,086 FAQ facts from 115 URLs; it does not evaluate generated answers. On its all-source reranked top-3 results, 5 of 12 queries retrieve a labeled relevant fact (hit@3 0.417, precision@3 0.139, MRR 0.417). The portfolio-only hybrid comparison at top-2 improves hit rate to 0.583 and precision@2 to 0.292, but still misses 5 of 12 queries. These are small, hand-labeled benchmark results, not live-index or production quality measurements.

The clearest failure causes are cross-domain distractors, weak query-to-source wording alignment, and source facts that do not explicitly resolve questions about unavailable metrics or other published case studies. The benchmark also has at least one label-normalization issue: a semantically matching “offline-first” passage uses a non-breaking hyphen and is not marked relevant by the literal substring check.

The checked-in [`chunks.json`](../src/xictek_website_assistant/data/index/chunks.json) is 0 bytes. Therefore, the production retrieval path cannot currently be evaluated against a built local index. No generated-answer transcripts or live provider responses were collected, so this log does not claim that any generated response was inaccurate.

## Query-level failure log

“Relevant” below refers to the benchmark's literal expected-answer labels. Scores and ranked passages are from the reranked all-source top-3 output reproduced with `python scripts/evaluate_portfolio_retrieval.py`.

| # | Previous query | Observed retrieval | Failure category | Finding |
|---|---|---|---|---|
| 1 | What is HisabDo? | The portfolio fact ranks third, behind Android-platform and founder-role facts; the benchmark does not mark it as a hit. | Cross-domain competition; label normalization | The displayed portfolio answer is semantically relevant, but its `offline‑first` non-breaking hyphen does not match the benchmark's literal `offline-first digital ledger` label. This is a retrieval weakness and a benchmark-label defect, not evidence of a wrong generated answer. |
| 2 | Which technologies power HisabDo? | Portfolio technology fact ranks first; unrelated privacy and blog facts follow. | Cross-domain distractors | The answer is retrieved, but unrestricted results still include unrelated facts. Portfolio-only routing addresses this source of noise. |
| 3 | What challenge does the HisabDo project address? | Top three contain privacy, AI delivery, and analytics facts; the paper-register challenge is absent. | Query/source vocabulary mismatch | “Challenge” does not align well with the source phrasing about daily records being kept in paper registers. Add explicit question aliases and keep challenge facts together in a clearly labeled portfolio passage. |
| 4 | How does HisabDo solve that problem? | A customer-profile blog passage ranks first, the portfolio problem statement second, and a founder passage third; the solution fact is not in the top three. | Cross-domain competition; weak solution wording | The query asks for a solution, while the top portfolio fact describes the problem. Keep the solution sentence adjacent to the challenge and add query variants for offline-first workflows and digital record keeping. |
| 5 | What are the outcomes or measurable results? | Top three are general software-outcome passages; the portfolio's no-quantified-results statement is absent. | Unsupported-answer handling; generic-term collision | The source states that quantified business/customer impact is not published. Represent this explicitly as an unanswerable-for-metrics fact so general outcome claims cannot substitute for project evidence. |
| 6 | Show me the product screens or portfolio visuals. | Portfolio screenshots fact ranks first; unrelated development-service passages follow. | Cross-domain distractors | Relevant evidence is available at rank one, but source restriction remains important to prevent unrelated materials from entering the answer context. |
| 7 | What is XICTEK's flagship product? | The portfolio flagship fact ranks first; company/about facts follow. | Cross-domain duplication | The fact is found, but equivalent product statements on other URLs can compete or create duplicate context. Keep the canonical portfolio statement authoritative for this intent. |
| 8 | Does the portfolio include other published case studies? | Top three are post-release metrics from general service pages; no direct answer is retrieved. | Source coverage / ambiguity | “Publishes work only when it can be shared responsibly” does not directly state whether other public case studies exist. Add a verified, time-bounded statement of what the portfolio currently publishes; do not infer that no other work exists. |
| 9 | What services can I discuss after viewing their work? | AI consultation, general contact, and HisabDo report passages rank; the portfolio custom-project fact is absent. | Intent mismatch; cross-domain competition | “Services” is broad and is not tied to the portfolio's custom-software invitation. Add a direct portfolio FAQ linking viewed work to the supported follow-up conversation. |
| 10 | How can I start a custom project conversation? | Portfolio contact instruction ranks first; general service/contact facts follow. | Cross-domain duplication | The intended fact is retrieved. Prefer the portfolio contact fact as the sole answer evidence for portfolio-intent queries. |
| 11 | What does HisabDo do for customer balances and khata? | Product overview and outcome passages rank, but the expected explicit khata-definition label is not retrieved in the top three. | Fine-grained fact coverage | The product overview is broadly relevant, but the query asks for the meaning and handling of balances/khata. Add a direct, concise fact defining khata as credit/debit records and describing customer balances. |
| 12 | What platform and database are used for the ledger? | Portfolio technology fact ranks first; general AI/technology-service facts follow. | Cross-domain distractors | Relevant evidence is retrieved; portfolio-only routing should keep the unrelated technology facts out of the evidence set. |

## Failure categories

1. **Cross-domain competition and duplication:** Broad terms such as “HisabDo,” “challenge,” “outcomes,” and “services” retrieve Android FAQs, blogs, people pages, or general service guidance. Portfolio URL filtering improves the aggregate top-2 hit rate from 0.417 to 0.583 in the benchmark, but the current empty index prevents verifying that behavior against application embeddings.
2. **Weak source/query alignment:** The benchmark queries use paraphrases (“challenge,” “solve,” “after viewing their work”) that do not consistently match how portfolio facts are phrased. This is most visible for the challenge, solution, and custom-services questions.
3. **Incomplete or ambiguous source facts:** The source does not directly resolve whether there are other published case studies. The absence of quantified impact must also be represented as explicit negative evidence, not left to compete with generic metrics pages.
4. **Evaluation-label fragility:** The script judges relevance by literal substring matching. Unicode punctuation and paraphrases can make a semantically correct passage appear as a miss, while the hand-labeled set may omit valid supporting passages. Per-query hit labels should be reviewed before interpreting aggregate changes.
5. **Application-index validation gap:** The local chunk metadata is empty. The lexical benchmark reads FAQ source facts and cannot establish retrieval quality, source inclusion, generated-answer accuracy, latency, or live behavior.

## Priority recommendations for Phase 2 source cleaning

| Priority | Recommendation | Acceptance evidence |
|---|---|---|
| **P0 — release blocker** | Rebuild the index from approved, current sources, including the canonical portfolio content in [`hisabdo.md`](../src/xictek_website_assistant/data/portfolio/hisabdo.md); verify chunk count, non-empty metadata, and the portfolio URL/source boundary before running answer tests. | A non-empty index with an auditable portfolio chunk/source list; all 12 prior queries run through the application retrieval path. |
| **P1 — source clarity** | Normalize the portfolio facts into compact, self-contained passages for project overview, challenge, solution, technology, supported outcomes, screenshots, portfolio publication scope, and custom-project contact. Keep related challenge/solution facts together and avoid duplicate competing versions across pages. | Each passage has a clear subject and can answer its corresponding prior query without relying on unrelated page context. |
| **P1 — negative evidence** | Make the lack of published quantified outcomes explicit and distinguish it from general company-wide outcome metrics. State the current public case-study scope only after verifying it with the content owner; do not turn missing evidence into a claim that no other projects exist. | Outcome and “other case studies” queries return a bounded, source-backed answer or deterministic no-evidence behavior, with no generic metrics substituted. |
| **P1 — intent wording** | Add source FAQ variants for the observed weak phrasings: paper registers/challenge, offline-first solution, discussing custom work after viewing the portfolio, and khata/customer balances. | Previously weak queries retrieve the intended portfolio facts in the top two results after rebuilding. |
| **P2 — benchmark repair** | Replace brittle single-substring relevance labels with reviewed acceptable fact IDs or normalized text matching (including Unicode hyphen variants). Separate answerable, explicitly unsupported, and genuinely out-of-scope test cases. | Per-query evaluation output reports label rationale and no false miss for punctuation-only differences. |
| **P2 — answer validation** | Once the index is rebuilt, run the 12-query set against the target provider and record the response, cited sources, and grounded/unsupported outcome. Keep retrieval and generation results separate. | A reviewed answer-level failure log with evidence citations; no claims based solely on lexical retrieval scores. |

## Evidence and limitations

- Benchmark and query definitions: [`evaluate_portfolio_retrieval.py`](../scripts/evaluate_portfolio_retrieval.py).
- Prior retrieval interpretation and scorecards: [`portfolio-retrieval-evaluation.md`](./portfolio-retrieval-evaluation.md), [`portfolio-final-evaluation-scorecard-2026-11-04.md`](./portfolio-final-evaluation-scorecard-2026-11-04.md), and [`portfolio-quality-latency-monitoring-2026-11-03.md`](./portfolio-quality-latency-monitoring-2026-11-03.md).
- Canonical local case-study content: [`hisabdo.md`](../src/xictek_website_assistant/data/portfolio/hisabdo.md).
- The benchmark was rerun on 2026-11-05. It reports 12 hand-labeled lexical queries and does not invoke the application embedding index or LLM.
- The application has automated source-filter, citation, and no-evidence tests, but these tests use fixtures/mocks and do not establish live generated-answer correctness.
- No production query sample, live provider answer set, or user-reported response failures were available for this review.
