# Department 4 — Final Evaluation & Master Handover Package

**Date:** 4 November 2026  
**Coordinator:** Hassan Hussain  
**Package status:** Compiled for final review; cross-domain production approval is pending and the system-wide audit says **NOT CLEARED**.

## 1. Executive decision

The submitted scorecards and supporting files have been collected and summarized. Their evidence is not equivalent across teams: some results are offline retrieval benchmarks, some are local mock/API tests, and some are public-widget black-box checks. The system-wide audit reports that fixes are not deployed to the live build and that the platform does not pass release gates. Therefore this is a complete coordination package for review, not an approved production release. The team lead/release owner must provide final approval after the blocking gaps are closed.

The Blog scorecard is marked approved for that separate pipeline, but it does not establish clearance of the shared live assistant. The corporate, careers, contact, HisabDo, Portfolio, and system-wide evidence all include material limitations or failed gates.

## 2. Domain handover scorecard

| Domain | Evidence received | Key result | Handover status |
|---|---|---|---|
| Blog & News | Day-7 scorecard | 24 queries; Hit@3 100%, MRR 1.0; citation accuracy 30/30; separate pipeline | Scorecard says approved for its pipeline; production integration/sign-off not established |
| About Us & Core Services | Corporate final signoff | Live score as scored 1/25; 2 HTTP 502/47 calls; irrelevant FAQ-style answers and weak citations | Not cleared; signoff unmet |
| Careers & Jobs | Careers package plus performance report | Live 5/10 pass, 1 partial, 4 fail; offline archive retrieval Hit@5 9/10, but another snapshot reports empty chunks; local mock latency only | Not cleared; conflicting snapshots/build identity and live failures |
| Contact & Locations | Final Validation package | Local mock 15/15 HTTP 200, but exact contact URL in 6/15; public widget 0/3 passed and cross-domain leakage observed | Not cleared |
| HisabDo Product | Product validation report | 2/6 pass, 3 partial, 1 fail; only six of twelve planned cases run | Hold; incomplete validation |
| Portfolio & Case Studies | Final scorecard plus prior monitoring package | Filtered offline Hit@2 58.3%, MRR .500; no current live end-to-end results; historical p95 29.43s | Not cleared; see Portfolio quality/latency report |
| System-wide | Baseline/deployment audit | Offline retrieval improved; audit says fixes are not deployed; only 1/11 deployment gates passed | Not cleared; deployment blockers remain |

## 3. Cross-domain findings and risk

### Positive evidence

- The system audit's matched 85-query offline comparison reports answerable retrieval hit rate improving from 50.7% to 87.3%, MRR from 0.41 to 0.83, and context precision from 28.3% to 57.3%.
- Blog's separate evaluation reports strong retrieval and citation-link results on its 24-query set.
- Careers and Contact submissions include local automated test suites and reproducible result artifacts.
- Portfolio's URL-scoped filtering improved its offline top-2 hit rate by 16.6 percentage points in the supplied 12-query benchmark.

These are component-specific results. They do not demonstrate a deployment of those changes to the production widget.

### Release blockers

1. **No verified release build identity or deployment evidence.** The system audit says the fixes evaluated offline are not deployed to the live system.
2. **Live answer quality and reliability failures.** Corporate returned irrelevant FAQ lists and 502s; Careers had four failed and one partial response among ten; Contact failed all three public-widget checks and showed cross-domain leakage; Product had one failure and three partial results.
3. **Index and snapshot inconsistency.** Careers archive evaluation references 976 chunks, while the separate Careers performance report says its current local `chunks.json` is empty. No shared commit/build/index ID explains the difference.
4. **Insufficient unsupported-query safety.** System audit reports unanswerable/stress and injection cases still pass through too often, with three fabricated names/places/services not caught in its checks.
5. **Portfolio end-to-end evidence absent.** Current Portfolio index was reported empty; latest metrics are offline lexical retrieval only, without generated-answer/link accuracy or current latency/cost measurements.
6. **Deployment handover gates incomplete.** The system audit says one of eleven gates passed and two were partial; release clearance cannot be inferred from per-domain component tests.

## 4. Portfolio quality and latency summary

The accompanying `Portfolio_Quality_Latency_Report` documents the full results. In brief, Portfolio-only URL filtering with top-k 2 and hybrid score threshold 0.15 improved offline Hit@2 from 41.7% to 58.3% and MRR from .417 to .500. The threshold is a hybrid score cutoff, not a cosine threshold. The latest scorecard did not run live embeddings, generated answers, production citations, or current latency/cost tests.

An earlier 10-sample timing report recorded 3,505.986 ms mean, 621.66 ms median, and 29,430 ms p95/max for total response time. This earlier sample has no verified association to the current build, has no provider/cost telemetry, and includes an unexplained sample where total time was about 29 seconds above server wait. It is retained as a historical risk signal, not release proof.

## 5. Submitted package inventory

Original member submissions are preserved in `member_submissions/`; the prior Portfolio metrics evidence is preserved in `portfolio_prior_monitoring_submission/`.

| Submitted file | Coverage |
|---|---|
| Blog final evaluation scorecard | Blog & News |
| Corporate Domain Final Evaluation Signoff | About Us & Core Services |
| Career Domain Final Evaluation & Handover Package ZIP | Careers live/API/retrieval evidence |
| Career domain performance metrics | Careers latency/error and index snapshot |
| Final Validation ZIP | Contact & Locations |
| HisabDo Product Module Final Validation Report | HisabDo Product |
| 4 Nov System Baseline Comparison & Deployment Audit | System-wide baseline, safety, deployment status |
| Portfolio final evaluation scorecard | Portfolio retrieval benchmark |
| Portfolio Quality/Latency Monitoring Submission | Prior Portfolio metrics, workbook, and raw CSVs |

## 6. Handover actions before release

1. Team lead/release owner assigns one build ID, commit, index version, embedding/model configuration, and deployed environment as the acceptance target.
2. Rebuild and validate the shared index; resolve the Careers 976-chunk versus empty-index mismatch and confirm Portfolio chunks are present.
3. Rerun each domain's agreed final query set end to end against that build; save raw request/response, citations, status, and timing evidence.
4. Close the cross-domain leakage, factual-grounding, fallback, citation, and HTTP 502 issues; rerun prompt-injection and out-of-scope cases.
5. Record latency percentiles with adequate sample counts, warm/cold behavior, provider/model, tokens, cost, and error rates. Do not use mock timings as production timings.
6. Obtain the product/release owner's signed approval only after agreed gates pass. Until then, keep status at **not cleared**.

## 7. Approval record

**Compilation:** Complete — supplied domain artifacts collected and summarized.  
**Portfolio report:** Complete — measured results and evidence gaps documented.  
**Technical release approval:** Pending — system audit status is NOT CLEARED.  
**Approver / date:** ______________________________

This package records submissions and evidence as provided. It does not certify that each domain's claims were independently reproduced or that a production deployment is safe.
