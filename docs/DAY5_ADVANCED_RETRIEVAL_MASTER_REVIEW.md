# Day 5 Advanced Retrieval — Master Review

**Review date:** 28 October 2026  
**Coordinator:** Hassan Hussain  
**Review status:** **Not ready for final approval**  
**Scope:** Submitted section-level evaluation packages plus Mujtaba’s global tuning ZIP.

## Executive summary

The submissions provide useful offline experiments and proposed settings, but they do not yet demonstrate a production-ready, grounded retrieval release across all domains. Mujtaba’s global evaluation is the most complete cross-domain artifact: its script reruns against its included 45-record fixture and reproduces the supplied 85-query summary. The selected configuration improves retrieval-hit metrics on that fixture. However, the benchmark does not exercise the live index or generated answers, its relevance labels are coarse, and its claimed answerability check is not implemented in the evaluator. Several domain reports are proposals or have incomplete/mismatched evidence.

**Recommendation:** accept the packages as an **offline evaluation draft**, but defer final approval and deployment claims until the evidence gaps in “Cross-submission issues to resolve” are closed. Do not copy thresholds between reports without confirming that they use the same score definition, index, and retrieval implementation.

## Submission review

| Domain / submission | Evidence reviewed | Review finding |
|---|---|---|
| **Global index — Muhammad Mujtaba Chohan** | ZIP includes 85 labelled queries, 45 tagged records, evaluation script, config, CSV/JSON results and run log. The script was rerun from an isolated extracted copy and reproduced the supplied metrics. | **Reproducible offline benchmark; provisional.** Selected TF-IDF `min_df=1`, normalization, metadata route, cosine threshold `0.06`, top-k `3` reports answerable hit `0.873` vs `0.563` baseline and previously-failed hit `0.905` vs `0.429`. It is not deployed. The evaluator’s hit definition is category/section-label matching, not answer correctness or source-link accuracy. It has no generated-answer grounding/refusal test. Eight of fourteen unanswerable queries still retrieve context at the selected setting (`no_context=0.429`), so retrieval alone cannot be treated as safe answerability. Per-domain sample sizes are small (e.g. Careers has only three cases). |
| **About Us & Core Services — Marsha Arif Muqri** | DOCX evaluation report; extracted text reviewed. | **Provisional sandbox experiment; insufficient for approval.** Report describes 22 cases and config E at 21/22, but uses an offline hashing/keyword-like embedder after model download failed. Its corpus/harness/results needed for independent reproduction were not supplied. The described corpus is `about_us.txt`; Core Services coverage is not separately demonstrated. It also says the configuration was created using the failed cases, so a holdout set is needed. |
| **Blog & News — Alisha Noor** | Markdown report. | **Evidence inconsistent and not independently reproducible.** Report’s method table says a 15-query set and 10 failed cases, while the per-query/results evidence contains 24 queries and 17 failed cases; metrics such as 95.8% and 94.1% correspond to the latter counts. The claimed “best” threshold/top-k does not align with the stated MRR objective or the grid metrics. Harness and raw result file are referenced at `/home/z/my-project/...` but were not included. MiniLM results therefore remain unverified and are not shown to match the current TF-IDF production retriever. |
| **Portfolio & Case Studies — Muhammad Mohsin** | Markdown report and Python script. | **Useful small offline lexical benchmark; limited reproducibility from submitted location.** Report gives 12 hand-labelled queries; normalization raises hit@3 from `0.250` to `0.417`, while hybrid and its simple reranker show no additional gain. Portfolio-filtered threshold `0.15` is explicitly on a hybrid score scale, not the application cosine scale. The supplied script is in Downloads and resolves corpus paths relative to its own location, so it needs to be placed in the repository’s expected `scripts` location with its corpus to reproduce as documented. Some relevance labels are weak/unsupported by the source text; add human-reviewed labels and negative cases before using the settings operationally. |
| **Careers & Job Openings — Muhammad Daniyal** | DOCX report. | **Design proposal, not a measured comparison.** It proposes section filtering, normalization, semantic reranking and settings such as top-k 5, but explicitly provides no production accuracy percentage or measured baseline-vs-optimized results. The report itself says parameters are starting values. Add an executable evaluator, corpus and labelled queries before calling the settings validated. |
| **HisabDo references — Muhammad Mohsin** | DOCX report (“Advanced Retrieval.docx”). | **Evaluation framework/proposal; quantitative work pending.** It explicitly states that no indexed retrieval system, Day 1 query log or measured benchmark was supplied. Its 10-query set, chunk settings and hybrid/RRF workflow are recommendations, not observed results. |
| **Contact & Locations — Ali Hassan** | ZIP includes 15-query/6-block corpus, TF-IDF/BM25 evaluator, config, CSV/Markdown, DOCX and tests. | **Reproducible offline lexical benchmark; limited.** I ran its evaluator and all seven included unit tests from an isolated extracted copy. It reproduced top-1 accuracy `0.933` baseline vs `1.000` normalized/hybrid, with MRR@3 `0.967` vs `1.000`. The report correctly states it is not a production vector-index test. One labelled relevant block per query makes precision@3 `0.333` expected by construction; retrieval of the correct “unknown” guidance does not prove the generated answer refuses to invent the missing detail. Source-link correctness is not separately scored. |

## What the global results support

Within the included 45-record fixture and the evaluator’s labels, the chosen configuration improves retrieval coverage over the script’s baseline. At threshold `0.06`, top-k `3`, normalized query and metadata routing, the run reports:

- Answerable retrieval hit: `56.3%` to `87.3%`.
- Previously failed-query hit: `42.9%` to `90.5%`.
- MRR: `0.546` to `0.833`.
- Context precision: `0.754` to `0.573` (a decrease), with average returned passages rising from `0.8` to `2.1`.
- For unanswerable queries, empty retrieval remains `42.9%`; the evaluator notes 8/14 still retrieve results.

These figures are retrieval measurements on the included fixture only. They do not establish response accuracy, link accuracy, abstention behavior, latency, or production performance. Threshold `0.06` is tied to this specific TF-IDF vocabulary, corpus, preprocessing and candidate-scoring code; it is not interchangeable with the `0.15` hybrid thresholds in some domain reports.

## Cross-submission issues to resolve

1. **Use one declared test protocol.** Freeze and version a held-out query set per domain, with answerable and unanswerable cases, query provenance, expected source/chunk IDs, and reviewed relevance labels. Separate tuning queries from final acceptance queries.
2. **Align score scales before comparing thresholds.** Each report uses different indexes and scoring functions: cosine, normalized cosine, hybrid cosine/BM25, or lexical/hashing scores. Record the score formula and apply each setting only to the evaluator that produced it.
3. **Verify the live implementation.** Attach the exact production index snapshot, retriever revision/config, and a repeatable command. The global script describes itself as a copied retriever; the package says “validated offline; not deployed.”
4. **Measure generation grounding and links.** For each query, check whether the final response is supported by retrieved source text, whether unsupported facts are refused, and whether each returned URL is the correct official source. Retrieval-hit alone does not cover these acceptance criteria.
5. **Resolve domain coverage.** Include adequate Core Services queries and more than a handful of Careers cases. Keep separate domain-level metrics so strong domains cannot conceal weak sections.
6. **Correct and rerun inconsistent reports.** Blog query counts and selected settings/results must be reconciled. About/Core and HisabDo need their referenced harnesses, corpora, and raw results. Careers needs measured results rather than proposed values.
7. **Review routing fallbacks.** Global config falls back to the full corpus when a filtered search returns no above-threshold record; test that this does not surface unrelated content as if it were relevant.

## Approval decision

**Decision: hold final master-package approval.** The global package and Contact package are reproducible as offline lexical tests, which is useful evidence. The remaining submissions range from provisional/sandbox results to unexecuted proposals, and none of the supplied packages demonstrates acceptance against the deployed chatbot with grounded-answer and source-link checks. Re-review after the follow-up items are supplied and evaluated on a frozen holdout set.

## Evidence reviewed

- `mujtaba_global_retrieval_tuning.zip` — included script, config, 85-query set, 45-record fixture, run log and result files; rerun completed successfully in an isolated copy.
- `retreival and query evaluation.zip` — included Contact evaluator and tests; evaluator reproduced and 7/7 unit tests passed in an isolated copy.
- About/Core Services, Blog, Careers, HisabDo and Portfolio reports/scripts supplied in Downloads.

This document is a review of the supplied artifacts. It does not claim that any configuration has been merged into or deployed on the production service.
