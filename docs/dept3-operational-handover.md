# Department 3 Operational Handover

**From:** Fahad Zubairi (AI intern) · **Date:** 2026-11-04 · **Branch:** `FahadZubairi_AI` (pull request 103)
**Scope:** the HisabDo chatbot's account, balance, expense and knowledge components (`src/financial_assistant/`)

## 1. What is being handed over

| Component | What it does | Code | Docs |
|---|---|---|---|
| Approved knowledge base | 364 cleaned chunks from 23 official sources, with source, date, area, review policy | `data/kb/approved/`, `scripts/clean_knowledge_sources.py` | [kb-content-cleaning.md](kb-content-cleaning.md) |
| Retrieval | Router gate → Roman Urdu / Urdu rewrite → hybrid BM25 + bge (C10, threshold 0.566, top 2) or lexical fallback (C15) | `grounding/retrieval.py` | [retrieval-approach-comparison.md](retrieval-approach-comparison.md) |
| Grounded answers | Cited answers, conflict notices, clarifying questions, no-source fallbacks (R1–R9) | `grounding/answer.py`, `prompts.py` | [grounded-answer-rules.md](grounded-answer-rules.md) |
| Guardrails | Injection, jailbreak, secrets, privacy, unsafe, toxic, off-topic, output checks | `guardrails.py` | [safety-guardrails.md](safety-guardrails.md) |
| Intent router fixes | 10 misroutes fixed (account / balance / expense routing) | `dialogue/recognizer.py` | [dept3-quality-scorecard.md](dept3-quality-scorecard.md) |
| Telemetry and fallbacks | `chat_turn` logs (20 safe fields), `GET /api/v1/metrics`, safe fallbacks, validated KB reloads | `telemetry.py`, `service.py` | [dept3-monitoring-runbook.md](dept3-monitoring-runbook.md) |
| Final evaluation | Scorecard, baseline comparison, security clearance | `data/dept3_final/`, `tests/test_dept3_final_isolation.py` | [dept3-final-evaluation.md](dept3-final-evaluation.md), [dept3-security-release-checklist.md](dept3-security-release-checklist.md) |

## 2. Configuration for production

| Setting | Value | Note |
|---|---|---|
| `APP_ENV` | `production` | Refuses placeholder or short tokens |
| `INTERNAL_SERVICE_TOKEN` | 32+ random characters, secret | Shared with the backend only |
| `GUARDRAILS_ENABLED` | `true` (default) | Off only for diagnosis |
| `GROUNDED_ANSWERS_ENABLED` | `true` | Default is `false`; turn on with this release |
| `KB_RETRIEVER_MODE` | `auto` | Hybrid when `fastembed` is installed, lexical otherwise |
| `fastembed` | `pip install fastembed==0.7.3` | Optional dependency; local model, about 67 MB, no API key |
| `TELEMETRY_SALT` | random secret | Keeps `user_ref` stable across restarts |
| `LLM_PROVIDER` + key | per team decision | Knowledge answers work without a model (extractive); keys via environment only |

Startup cost: the hybrid index embeds 364 chunks once per process (about 1 to 1.5 minutes on a laptop CPU). The
knowledge route serves the `kb_unavailable` fallback until it is ready or if it fails (retry every 60 s).

## 3. Day-to-day operation

Follow [dept3-monitoring-runbook.md](dept3-monitoring-runbook.md):

* **Daily:** `/api/v1/metrics` (index loaded, hybrid mode, error counters, p95), `needs_review` turns, leak findings.
* **Every 30 days / within 7 days of an app release:** KB refresh (`clean_knowledge_sources.py --fetch`), then
  `service.reload_kb()` (validated swap, old index keeps serving on failure).
* **When the KB, glossary or embedding model changes:** recalibrate (`retrieval_eval.py run --only C10`, then `C15`),
  update the constants in `grounding/retrieval.py`.
* **Before every release:** full tests, release gate, safety suite v1.1 in all four configurations, scorecard.

## 4. Commands

```bash
python -m pytest tests                                                       # 781 pass; 26 XICTEK failures pre-existing
python scripts/release_acceptance.py                                         # critical 25/25, major 6/6
python scripts/safety_eval.py --suite 1.1 --model compliant --grounded on --label release
python scripts/dept3_scorecard.py --label release
python scripts/grounded_answer_eval.py --mode hybrid
python scripts/clean_knowledge_sources.py --fetch
```

## 5. Open items handed over

| # | Item | Owner | Where |
|---|---|---|---|
| 1 | Conflict C-06: is AED a supported currency? Fix the website or Google Play listing | Product owner / web | grounded-answer-rules.md §8 |
| 2 | 95 broken blog links (`/slug` instead of `/blog/slug`), stale "30 questions" FAQ count, 5 undated pages | Website owner | kb-content-cleaning.md §8 |
| 3 | Router: "galti ho gayi, 450 nahi 540 tha" not recognised as a correction; "customer ko payment reminder kaise likhun?" now `faq` (labelled `general`); "Have you sent the payment to my customer?" now routed `faq` | Intent router (Saba Talat) | dept3-quality-scorecard.md §2 |
| 4 | Urdu-script retrieval still the weakest language (glossary-based) | AI team | retrieval-approach-comparison.md §7 |
| 5 | Red-team the guardrails by another member (suite v1.2); add Hindi / Arabic patterns | AI team | safety-guardrails.md §6 |
| 6 | Metrics are in-process; export them for multi-worker deployments | Platform | runbook §6 |
| 7 | Re-baseline latency in production from `/api/v1/metrics` (all figures here are laptop CPU) | Platform | dept3-final-evaluation.md §3 |
| 8 | Approve the self-harm reply wording | Product owner | safety-guardrails.md §6 |
| 9 | Merge pull request 103 after review | Team Lead | — |

## 6. Contacts

| Area | Person |
|---|---|
| This work (KB, retrieval, grounded answers, guardrails, telemetry) | Fahad Zubairi |
| Intent router and conversation state | Saba Talat |
| Core services / backend auth | Hassan Hussain, Niha Batool (as proposed on Day 1; Team Lead to confirm) |
| Product facts and approvals | Mian Usman Khalid (Team Lead, founder) |
