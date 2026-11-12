# Blog & News — Grounded Prompting & Citation Rules (Today's Task)

**Task:** Grounded Prompting & Citation Rules — Blog & News
**Date:** 12 November 2026
**Owner:** QA Automation

---

## Deliverables

This package contains today's three required deliverables:

| # | Deliverable | File |
|---|---|---|
| 1 | Blog & News grounded prompt rules | `reports/blog-grounded-prompt-rules.md` |
| 2 | Citation validation log | `results/verified_transcripts.json` + `reports/blog-citation-validation-report.md` |
| 3 | Verified example transcripts | `reports/verified_transcripts.md` |

Plus the runnable code that produced them:

| File | Purpose |
|---|---|
| `src/citation_validator.py` | The validator. Pure-function module implementing 4 mandatory + 1 informational citation-integrity checks. |
| `scripts/verified_transcripts.py` | The transcript generator. Runs 10 curated queries (7 positive + 3 negative controls) through the pipeline + validator, emits JSON + Markdown. |

---

## Quick Start

```bash
cd blog-citation-task

# Install dependencies (if not already present)
pip install -r requirements.txt

# Run the full transcript suite (writes results/ and reports/)
python3 scripts/verified_transcripts.py

# Or run the validator standalone as a smoke test
python3 src/citation_validator.py
```

Expected output:
```
======================================================================
SUMMARY
======================================================================
  Positive cases passed:          7/7
  Negative controls failed:       3/3
  Overall verdict:                PASS
```

---

## What This Package Adds on Top of Day-4

Day-4 (`blog-grounded-generation-spec.md` in the parent pipeline) defined the system prompt (15 rules), citation format, 6 fallbacks, and conflict disclosure. It also shipped a Python implementation.

Today's package adds the **verification layer** that was missing:

1. **A formal citation contract** (`reports/blog-grounded-prompt-rules.md` §5) — 4 mandatory checks + 1 informational check, each with a defined rule, failure mode it catches, and example.
2. **A pure-function validator** (`src/citation_validator.py`) — runs sub-millisecond per response, takes a response string + retrieved articles, returns structured pass/fail report with evidence.
3. **A verified transcript suite** (10 transcripts) — 7 real queries through the pipeline all pass; 3 manually corrupted responses all correctly fail with specific check identifications.

---

## Folder Structure

```
blog-citation-task/
├── README.md                              ← this file
├── requirements.txt                       ← Python deps (sentence-transformers, sklearn, numpy)
│
├── src/
│   ├── __init__.py
│   ├── citation_validator.py              ← NEW today — the validator
│   ├── grounded_generation.py             ← copied from pipeline (Day-4)
│   ├── retrieval.py                       ← copied from pipeline (Day-3)
│   ├── utils.py                           ← copied from pipeline
│   ├── monitoring.py                      ← copied from pipeline (Day-7)
│   └── content_cleaning.py                ← copied from pipeline (Day-2)
│
├── scripts/
│   └── verified_transcripts.py            ← NEW today — transcript generator
│
├── tests/
│   └── test_citation_validator.py          ← unit tests for the validator
│
├── data/
│   └── articles/                          ← 47 cleaned blog articles (corpus)
│
├── configs/
│   ├── retrieval_config.json
│   ├── synonyms.json
│   └── safe_logging_config.json
│
├── results/
│   └── verified_transcripts.json          ← structured log (machine-readable)
│
└── reports/
    ├── blog-grounded-prompt-rules.md      ← Deliverable 1 (rules + citation contract)
    ├── blog-citation-validation-report.md ← Deliverable 2 (validation log summary)
    └── verified_transcripts.md            ← Deliverable 3 (10 human-readable transcripts)
```

---

## The Four Mandatory Checks (Quick Reference)

| Check | Rule | Caught Failure |
|---|---|---|
| CHECK 1 | Every `[n]` in body has Sources entry | Orphan markers (LLM cites but forgets to list source) |
| CHECK 2 | Every Sources entry has `[n]` in body | Padded sources (LLM lists unused articles) |
| CHECK 3 | Every cited index ≤ len(retrieved) | Fabricated index (LLM hallucinates [5] when only 3 retrieved) |
| CHECK 4 | URL matches `^https://www.xicteksystems.com/blog/[a-z0-9-]+$` | Scope violation (/services, hisabdo.app, LinkedIn URLs) |

Plus one informational check (CHECK 5): verbatim `"..."[n]` quotes must appear in article `[n]` body. Absence of quotes is not a failure.

---

## Test Set

### Positive Cases (7 — real queries through the pipeline)

| ID | Query | Scenario |
|---|---|---|
| T1 | how much does custom software cost in pakistan | Normal citation |
| T2 | custom software development guide | Multi-source synthesis |
| T3 | what is the agile software development process | Normal citation |
| T4 | tell me about ai chatbot development | Normal citation |
| T5 | explain progressive web apps | Normal citation |
| T6 | how much do you charge for software development services | Out-of-domain fallback (5.2) |
| T7 | best recipe for chicken biryani | No-source fallback (5.1) |

### Negative Controls (3 — manually corrupted responses)

| ID | Injected Defect | Expected Failure |
|---|---|---|
| T8 | Body cites [3], Sources only has [1] | CHECK 1 (orphan) + CHECK 3 (fabricated) |
| T9 | Body cites [1], Sources lists [1] and [2] | CHECK 2 (padded) |
| T10 | Sources URL is `https://hisabdo.app/features` | CHECK 4 (URL allowlist) |

---

## Result

```
Positive cases passed:          7/7
Negative controls failed:       3/3
Validator verdict accuracy:     10/10 (100%)
Overall:                        PASS
```

---

## Production Wiring (Next Step)

The validator is ready to be inserted as the final gate in `generate_grounded_response()`:

```python
from .citation_validator import validate_citations

report = validate_citations(response, retrieved_articles)
if not report["overall_pass"]:
    logs.append({"event": "CITATION_VALIDATION_FAIL",
                 "query": query, "errors": report["errors"]})
    return apply_fallback(query, retrieved_articles)  # route to 5.4
```

This guarantees: **no response with broken citations is ever delivered to the user**. Latency impact: <1ms per response.

---

## References

- Parent pipeline: `../blog-news-pipeline/` (Day 1–9 deliverables)
- Day-4 spec: `../blog-grounded-generation-spec.md` (system prompt, 6 fallbacks, conflict rules)
- Day-8 release audit: `../blog-final-evaluation-scorecard.md`

---

*QA Automation — Grounded Prompting & Citation Rules — Blog & News*
