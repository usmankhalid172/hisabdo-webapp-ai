# Department 3 Operational Maintenance & Deployment Runbook

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-17 · **Branch:** `FahadZubairi_AI`
**Audience:** whoever operates the HisabDo chatbot service (platform, QA, content owner)
**Related:** [Freeze spec](dept3-production-config-freeze-spec.md) · [Monitoring runbook](dept3-monitoring-runbook.md)
(log fields, metrics) · [Ingestion checklist](dept3-ingestion-master-checklist.md) · [Operational handover](dept3-operational-handover.md)

Rule for every procedure: **verify before you switch, keep the previous version, and write down what changed.**

## 1. Roles and when to call them

| Situation | Who |
|---|---|
| Alerts, deployment, rollback | Platform on call |
| Knowledge base content, conflicts (`needs_review`), new pages | Mian Usman Khalid (content owner) |
| Account figures, backend contract | Hassan Hussain (core services) |
| Dialogue, intents | Saba Talat |
| Retrieval, KB pipeline, guardrails, this runbook | Fahad Zubairi |
| Red-team and release QA | Syeda Isma Nazir |

## 2. Deployment

### 2.1 Pre-deployment gate (all must pass, on the release candidate)

```bash
python scripts/freeze_config.py --verify
```
```bash
python -m pytest tests
```
```bash
GROUNDED_ANSWERS_ENABLED=true python scripts/release_acceptance.py     # critical 25/25, major 6/6
```
```bash
python scripts/safety_eval.py --suite 1.1 --all --label release        # CLEARED x4
```
```bash
python scripts/conversation_ux_eval.py                                 # 8/8 journeys, 18/18 attacks
```
```bash
python scripts/e2e_regression.py                                       # no previously passing probe changed
```

### 2.2 Deploy

1. Set the production environment from `config/production.env.example` (secrets from the secret store).
2. Make sure `fastembed` is installed and `FASTEMBED_CACHE_PATH` points to a persistent folder.
3. Start the service. The index builds at start-up (about 45 s on CPU; the service answers only after it is built).
4. **Smoke test** (before sending traffic):

```bash
curl -s localhost:8000/api/v1/health
```

then `GET /api/v1/metrics` must show `kb.loaded = true`, `kb.mode = hybrid`, `kb.degraded` empty, `kb.chunks = 363`,
and one request each for a product question, an own-figures question, an injection attempt and "expenses" must give
a cited answer, a "demo data" line, a boundary reply and a clarifying question.

5. Send traffic. Watch section 5 alerts for 30 minutes.

## 3. Routine knowledge base update (every 30 days, and within 7 days of an app release)

Owner: Fahad Zubairi with the content owner.

1. **Dry run.** Fetch and compare without publishing:

```bash
python scripts/ingest_dept3.py --fetch --dry-run
```

Read `data/kb/dept3/ingestion/ingest_<date>_fetch_dryrun.md`. Stop and investigate when:
   * a **failed page** or **parse error** is listed (the report keeps the last good copy; fix the cleaner or the site before publishing),
   * `NOT FOUND ON PAGE` warnings appear,
   * more than 20% of records change, or a gate fails,
   * a new **conflict** is flagged.
2. **Content owner review** of every added and modified record, and removal of marketing copy (add its pattern to `PROMO` in `scripts/clean_knowledge_sources.py`).
3. **Publish:**

```bash
python scripts/ingest_dept3.py --fetch
```

4. **Evaluate the new KB** against the freeze: `e2e_regression.py`, `grounded_answer_eval.py --mode hybrid`,
   `safety_eval.py`. If more than 10% of records changed, recalibrate retrieval first (section 4.3).
5. **Load without a restart** (validation runs first; a bad file is rejected and the old index keeps serving):

```python
from src.financial_assistant import service
service.reload_kb()        # {"updated": True|False, "reasons": [...], "serving": {...}}
```

6. **Cut a new freeze** (freeze spec section 6) and tag it.

A source that is added, changed or removed in `data/knowledge_source_audit.csv` follows the same steps. Never delete a
record by hand: remove its source row or fix the source page, then ingest.

> `ingest_dept3.py --offline` rebuilds from the **approved snapshot named in `index_manifest.json`**, never from a newer
> unreviewed folder. A `--fetch` run (without `--dry-run`) that publishes moves the approved snapshot forward.

## 4. Index rebuild

### 4.1 When

* after any KB change (section 3, the reload does this),
* after a model, library or glossary change,
* when `kb.degraded` is set, or the index failed to load.

### 4.2 Procedure

1. `python scripts/ingest_dept3.py --offline` rebuilds from the approved snapshot, embeds every record, checks each
   vector (384 dimensions, finite, non-zero) and writes `data/kb/dept3/index_manifest.json`.
2. Compare the manifest with the freeze: `embedding.onnx_sha256`, `embedding.checksum`, `records`.
   * Same hashes and checksum: the rebuild is reproducible. Done.
   * Different model hash or checksum: stop, see 4.3.
3. In the running service: `service.reload_kb()`, then `GET /api/v1/metrics` to confirm `kb.version` and `kb.chunks`.
4. A **vector error** (listed in the execution report) excludes that record. Fix its source text; never lower the checks.

### 4.3 Recalibrate (model file, KB content over 10%, or glossary change)

```bash
python scripts/retrieval_eval.py run --only C10      # hybrid
```
```bash
python scripts/retrieval_eval.py run --only C15      # lexical fallback
```

Run them one after the other (both write `comparison.json`). Take the new threshold, top-k and margin into
`grounding/retrieval.py` only when the 139-question result is at least as good as the freeze (120 correct, recall 0.724,
precision 0.908), then update the freeze.

## 5. Monitoring and alerts

Metrics at `GET /api/v1/metrics`; log fields in the [monitoring runbook](dept3-monitoring-runbook.md). Thresholds come
from the measured baseline (quiet machine: knowledge p95 about 28 ms, account about 11 ms).

| Alert | Condition (5-minute window) | Severity | First action |
|---|---|---|---|
| Service down | `/api/v1/health` fails 3× in a row | Page | Section 6.1 |
| Knowledge latency | `latency.knowledge.p95_ms` > 250 | Page | Check CPU, model cache; section 6.1 |
| Account / transaction latency | p95 > 150 | Warn | Check backend |
| Index not loaded | `kb.loaded == false` for 2 scrapes, or `error:kb_unavailable` | Page | `service.reload_kb()`; section 4 |
| **Index degraded** | `kb.mode == "lexical"` or `kb.degraded` set | Warn | fastembed missing or model file unreadable: install, rebuild. Lexical is measurably weaker (6 unrelated held-out citations vs 2) |
| Backend down | `error:backend_error` > 5% of `source:backend_*` | Page | Backend team; users get a safe message |
| Model provider failing | `error:llm_error` + `error:llm_timeout` > 5% | Warn | Provider status; answers fall back to source text |
| Possible leak | any `guardrail_output_blocked` with `secret` or `prompt_text`, or `telemetry_redactions` > 0 | **Page, immediate** | Section 7 |
| Attack volume | `source:guardrail` > 3× its 7-day average | Warn | Check client; review the sample of blocked categories |
| No-source spike | `kb_fallback` share > 2× its 7-day average | Warn | A topic is missing or retrieval broke: sample the questions, tell the content owner |
| Conflict | any `needs_review` | Info | Send chunk ids to the content owner (C-06 open) |
| **Human-support escalations** (new) | `source:escalation` > 3× its 7-day average | Warn | Possible outage or account problem wave: check login service and support inbox |
| **Limit notices** (new) | `source:limit_notice` > 30% of account questions | Info | Users hit backend limits (week, category, per-customer): prioritise D3-01 |
| Stale knowledge base | KB older than 35 days, or ingestion dry run shows changed pages | Warn | Section 3 |
| Freeze drift | `freeze_config.py --verify` fails in CI or on the server | Page before release | Section 8 |

Daily 5-minute check: `kb.loaded`, `kb.mode = hybrid`, error counters near zero, p95 under thresholds, escalation and
limit-notice counts, any `needs_review`.

## 6. Rollback protocols

Every rollback ends with the smoke test of 2.2 step 4 and a written note (what, when, why).

### 6.1 Code or configuration rollback

1. Redeploy the previous tag (`git checkout dept3-freeze-v1.<N-1>`), with the previous settings file.
2. `python scripts/freeze_config.py --verify` on that tag must pass.
3. Restart, smoke test.

### 6.2 Knowledge base rollback

The approved KB, the standardized set and the manifest are in git; ingestion keeps previous snapshots.

```bash
git checkout dept3-freeze-v1.<N-1> -- data/kb/approved data/kb/dept3
```

then `service.reload_kb()` (or restart). `reload_kb()` refuses a file that fails validation and keeps serving the
current index, so a bad KB can never half-load. After the rollback, re-run `ingest_dept3.py --offline`: the vector
checksum must equal the frozen one.

### 6.3 Emergency switches (no deployment needed)

| Problem | Switch | Effect |
|---|---|---|
| Grounded answers misbehave in production | `GROUNDED_ANSWERS_ENABLED=false` and restart | Previous single-source path over the small FAQ file; the safety suite is CLEARED in this mode too, but answers are far weaker (Day 1 baseline). Use only for hours |
| Index cannot build | `KB_RETRIEVER_MODE=lexical` and restart | BM25 fallback, no embedding model needed; alert "Index degraded" stays on |
| Provider misbehaves | `LLM_PROVIDER=mock` | Extractive answers from the sources |
| Guardrail false positives flood support | Do **not** disable guardrails. Add the case to the suite, fix the rule, release (section 2) | |

`GUARDRAILS_ENABLED=false` is never an acceptable rollback.

## 7. Incidents

### 7.1 Suspected leak (secret, prompt text, someone else's data)

1. Find the `request_id` in the output-guard event (the reply was replaced or redacted before it left the service).
2. Secret: rotate the internal service token and any provider key at once. Check the route (`source`) and reproduce with
   `python scripts/safety_eval.py --model compliant`.
3. Add the case to a new suite version (v1.2), fix, re-run all four configurations and the conversation evaluation,
   release with a new freeze.

### 7.2 Wrong answer reported by a user

1. Get the question and the `request_id`; check `retrieved_ids` and `cited_ids` in the `chat_turn` log (no message text is logged: ask the reporter for the text).
2. Source text wrong: content owner fixes the page, then section 3.
3. Source right, answer wrong: add the question to `data/retrieval_eval/` with a judgment, fix, and confirm the regression run shows no previously passing case changed.

### 7.3 Account-level problems from users

The chatbot already replies with the support channels (hisabdo.app@gmail.com, https://hisabdo.app/contact, 48 hours,
never share a password or one-time code). The support inbox owner handles them; platform only checks the
escalation alert.

## 8. Change control

| Change | Needs |
|---|---|
| Prompt, rule file, constant, KB, glossary | Evaluation (2.1), freeze update, tag |
| New source page | Register row, approval, section 3 |
| Real model provider | The 2.1 gate with that provider, plus a wording review of 40 answers; new freeze |
| New language | Glossary, router cues, guard patterns, judged questions in that language, new freeze |
| Backend contract | Re-run `tests/test_dept3_final_isolation.py` and the 22 isolation tests; update the "demo data" labels |

## 9. Known limits at freeze

* The account backend is a mock (D3-01); week, category and per-customer figures are stated limits.
* The live site has changed since the approved snapshot (OFF-02, OFF-03 redesigned, OFF-01 no longer parseable);
  the approved KB is kept until section 3 is completed with the content owner.
* No official pages for edit, budget, recurring entries, receipts, multi-user; those questions get a no-source reply.
* Urdu script retrieval is the weakest language.
