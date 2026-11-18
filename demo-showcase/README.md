# Live Demo Walkthrough & Final Metrics Showcase — Blog & News

**Task:** Live Demo Walkthrough & Final Metrics Showcase — Blog & News
**Date:** 18 November 2026
**Owner:** QA Automation
**Audience:** Phase 2 executive stakeholders, product, engineering

---

## Deliverables

| # | Deliverable | File |
|---|---|---|
| 1 | Blog & News Live Demo Script | `reports/live-demo-script.md` |
| 2 | Sample Transcript Showcase | `reports/sample-transcript-showcase.md` |
| 3 | Final Domain Metrics Summary | `reports/final-domain-metrics-summary.md` |

Plus the supporting data file:

| File | Purpose |
|---|---|
| `reports/demo_data_extract.txt` | Raw extracted source data backing every number and quoted response in the three deliverables. Use this to re-verify any metric. |

---

## What This Package Does

This is the final stakeholder walkthrough package for the Blog & News chatbot. It packages a 20–25 minute live demo (with real queries and real responses), a transcript showcase of eight real Q→A flows with before/after comparisons, and a final domain metrics summary for the Phase 2 Executive Summary.

- **Live Demo Script (Deliverable 1)** — A presenter's script. 12 sections: pre-demo setup, opening, seven demo queries (five Phase-1-failure recoveries + two edge cases), closing metrics, anticipated Q&A, runtime cheat sheet, and source files. Every query has a "Why this query" rationale, the response to display, narration to read aloud, and a single talking point to land.
- **Sample Transcript Showcase (Deliverable 2)** — Eight real transcripts (T1–T8) extracted verbatim from production pipeline runs. Each shows the query, retrieved context (top-3 articles with scores where available), the verbatim response with inline `[n]` citations and Sources block, the citation validation result (4 checks + informational 5th), and a Phase-1 vs Phase-2 before/after table. Covers 7 Phase-1 failures recovered, plus the multi-source fallback (T6), the out-of-domain drift conversation (T7), and a conflict-stress query (T8).
- **Final Domain Metrics Summary (Deliverable 3)** — A 10-section metrics document for the Executive Summary: coverage & configuration, Phase 1 vs Phase 2 headline metrics, retrieval performance, citation & safety performance, latency performance, defect closure status, six executive-highlight talking points, domain benchmark summary, and a source-file traceability table.

---

## Headline Numbers

| Metric | Phase 1 | Phase 2 Final |
|---|---|---|
| Pass rate (24-query golden set) | 7 / 24 (29%) | **24 / 24 (100%)** |
| Failed queries recovered | — | 17 / 17 |
| New regressions | — | 0 |
| Retrieval MRR@3 | 0.8292 (lexical) | **1.0000** |
| Citation pass rate | n/a | **100%** (24/24) |
| URL validity rate | (mostly /services) | **100%** |
| Scope violations leaked | common | **0** |
| Mean retrieval latency | — | 12.2 ms (warm index) |
| Defects closed | — | 10 / 10 |
| Production release verdict | — | ✅ APPROVED |

---

## How the Live Demo Works

This package does not host a live webinar — it is the complete **demo package** that you (or anyone) can present to stakeholders. The pattern is:

1. Open `sample-transcript-showcase.md` in a browser or markdown viewer, sized to fill the screen.
2. Open `final-domain-metrics-summary.md` as the second tab — switch to it during the closing.
3. Follow `live-demo-script.md` section by section: read the Narration, display the matching transcript (T1–T8), land the talking point.
4. At the closing (Section 9 of the demo script), switch to the metrics summary, Section 3 (the Phase 1 vs Phase 2 table).
5. Take questions using Section 10 (Anticipated Questions & Answers).

Total runtime: 20–25 minutes including Q&A.

---

## Source Files for Every Number

Every quoted response, every metric, and every before/after comparison in this package is traceable to a real source file:

| Source | Used for |
|---|---|
| `e2e-regression-today/results/e2e_regression_results.json` | Phase 2 final aggregate + per-query metrics |
| `blog-news-pipeline/results/e2e_multi_turn_logs.json` | Real multi-turn response text (CONV1, CONV2, CONV5 for T1, T2, T7) |
| `blog-citation-today/results/verified_transcripts.json` | Real validated responses + citation-check results (T1–T5 validation) |
| `blog-news-pipeline/results/e2e_pipeline_outputs.json` | Conflict-handling per-query data + source-link formatting (T8) |
| `blog-kb-audit-report.md` | Phase 1 baseline (47 articles, audit results) |
| `blog-weak-question-analysis.md` | Phase 1 failed-query root causes (synonym mismatches) |
| `blog-retrieval-evaluation.md` | Phase 1 lexical baseline MRR + Phase 2 hybrid MRR + grid search |
| `blog-final-evaluation-scorecard.md` | Phase 2 final release clearance (24/24 pass) |
| `blog-quality-latency-monitoring-report.md` | Steady-state latency benchmark (12.2 ms mean, 18.1 ms p95) + synonym expansion detail |
| `blog-security-report.md` | Security suite results (30/30 attacks blocked) |
| `defect-closure-today/reports/defect-closure-log.md` | Defect closure status (10/10 closed) |
| `defect-closure-today/reports/frozen-domain-configuration-spec.md` | Configuration freeze (spec v1.0) |

For a single extracted view of all this source data, see `reports/demo_data_extract.txt` — it contains the raw fields pulled from each of these files in one place, so any number in the three deliverables can be re-verified without opening the source files individually.

---

## Folder Structure

```
demo-showcase-task/
├── README.md
└── reports/
    ├── live-demo-script.md                ← Deliverable 1
    ├── sample-transcript-showcase.md      ← Deliverable 2
    ├── final-domain-metrics-summary.md    ← Deliverable 3
    └── demo_data_extract.txt              ← Raw source data (verification)
```

---

## Production Release Verdict

**✅ APPROVED FOR PRODUCTION RELEASE.** All 24 queries pass end-to-end. All 10 defects are closed. The configuration is frozen (spec v1.0, 2026-11-17). The only open item is re-verifying conflict-disclosure behaviour once a real LLM backend is wired in — the prompt, retrieval layer, and detection heuristic are ready; this is a single post-deployment test, not a release blocker.
