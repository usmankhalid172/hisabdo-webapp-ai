# Defect Closure & Production Config Freeze — Blog & News

**Task:** Defect Closure & Production Config Freeze — Blog & News
**Date:** 17 November 2026
**Owner:** QA Automation

---

## Deliverables

| # | Deliverable | File |
|---|---|---|
| 1 | Blog & News Defect Closure Log | `reports/defect-closure-log.md` |
| 2 | Frozen Domain Configuration Spec | `reports/frozen-domain-configuration-spec.md` |
| 3 | Content Update Runbook | `reports/content-update-runbook.md` |

Plus the supporting script:

| File | Purpose |
|---|---|
| `scripts/validate_new_article.py` | Ingestion-time content validator. Runs on every new or updated blog article before it is indexed. Closes Defect D10 (article corpus integrity assumes CMS trust). |

---

## What This Package Does

It closes every retrieval, formatting, and citation edge case logged during Day-8 regression testing and the subsequent verification tasks (Day-9 citation validation, Day-10 multi-turn UX, Day-11 end-to-end regression), freezes the production configuration for the Blog & News domain, and documents the routine content update process.

- **Defect Closure Log (Deliverable 1)** — 10 defects catalogued with root cause, fix, verification, and closure status. All 10 closed (7 fixed in code or resolved by configuration; 3 accepted limitations with documented mitigations). Production release: UNBLOCKED.
- **Frozen Domain Configuration Spec (Deliverable 2)** — 12-section spec pinning every parameter value: chunking (single chunk, ≤512 tokens), retrieval (hybrid α=0.5, threshold=0.15, top-k=3), query normalization (lowercase + punctuation + stopwords + synonyms), metadata filter (DISABLED), MMR (DISABLED), citation contract (4 mandatory + 1 informational check), 6 fallbacks, URL allowlist, safety boundaries, logging config, latency SLO, regression acceptance criteria, and change-control process.
- **Content Update Runbook (Deliverable 3)** — 11-section runbook for routine content updates: roles & cadence, ingestion-time validation (8 rules), single-article procedure, batch updates, article removal, drift detection, emergency rollback, escalation, and a quick-reference cheat sheet.

---

## Quick Start

```bash
# Validate a new article before adding it to the corpus
python3 scripts/validate_new_article.py data/articles/new-article.md

# Validate the whole corpus as a sanity check
python3 scripts/validate_new_article.py data/articles/

# Strict mode (long bodies and base64 blobs become errors)
python3 scripts/validate_new_article.py --strict data/articles/new-article.md
```

Expected output (single article):
```
======================================================================
INGESTION-TIME CONTENT VALIDATOR — Blog & News
======================================================================
Target: data/articles/new-article.md
Articles checked: 1

  ✓ [PASS  ] new-article.md

======================================================================
RESULT: 1 passed, 0 rejected
======================================================================
```

---

## Validation Rules (Quick Reference)

The validator rejects an article if any of these fire:

| Rule | What it checks |
|---|---|
| R1 | Required frontmatter (`Source`, `Category`, `Reading time`, `Published`, `Author`) |
| R2 | Source URL on the production blog allowlist |
| R3 | Body length within 50–5000 chars (warn if longer) |
| R4 | No prompt-injection patterns in body |
| R5 | No dangerous URI schemes (`javascript:`, `file:`, `data:`, `vbscript:`) |
| R6 | No non-blog URLs in body (`/services`, `hisabdo.app`, external domains) |
| R7 | No base64-looking blobs over 200 chars (warn; error in strict) |
| R8 | No exfiltration patterns (`curl`, `wget`, `fetch()`, `eval()`, `XMLHttpRequest`) |

---

## Source Artifacts Reviewed

This package was built by reviewing the following prior-task artifacts:

- `blog-news-pipeline/results/e2e_test_summary.json` — Day-8 baseline (4-test e2e suite)
- `blog-news-pipeline/reports/blog-e2e-pipeline-report.md` — Day-8 findings (5 follow-up edge cases)
- `blog-news-pipeline/reports/blog-security-report.md` §9 — Documented Fixes & Blockers (5 blockers)
- `blog-news-pipeline/reports/blog-retrieval-evaluation.md` §6-7 — Recommended config + grid-search results
- `blog-news-pipeline/configs/retrieval_config.json` — Frozen retrieval config values
- `blog-news-pipeline/configs/synonyms.json` — Synonym expansion map
- `blog-news-pipeline/configs/safe_logging_config.json` — Safe logging config
- `blog-news-pipeline/src/grounded_generation.py` — Fallback trigger logic, stale-article check, conflict detection
- `e2e-regression-today/results/e2e_regression_results.json` — Day-11 regression results (24/24 PASS)
- `multi-turn-ux-today/reports/multi-turn-ux-test-log.md` — Day-10 multi-turn findings
- `blog-citation-today/reports/blog-citation-validation-report.md` — Day-9 citation findings

---

## Folder Structure

```
defect-closure-task/
├── README.md
├── reports/
│   ├── defect-closure-log.md              ← Deliverable 1
│   ├── frozen-domain-configuration-spec.md ← Deliverable 2
│   └── content-update-runbook.md           ← Deliverable 3
└── scripts/
    └── validate_new_article.py             ← Ingestion-time content validator (D10 mitigation)
```

---

## Production Release Verdict

**UNBLOCKED.** All 10 defects are closed. The 3 HIGH-severity items (D3, D4, D9, D10) are either fixed in code (D3, D4) or accepted with mitigations in place (D9 input sanitiser + output filter + post-deployment red-team; D10 ingestion-time content validator added in the runbook). The frozen configuration is ready for production release on the Blog & News domain.
