# Department 3 Monitoring and Maintenance Runbook

**Owner:** Fahad Zubairi (AI intern) · **Updated:** 2026-11-04 · **Branch:** `FahadZubairi_AI`
**Covers:** the chatbot's knowledge, account / balance and expense flows (`src/financial_assistant/`)
**Related:** [dept3-quality-scorecard.md](dept3-quality-scorecard.md) · [safety-guardrails.md](safety-guardrails.md) ·
[grounded-answer-rules.md](grounded-answer-rules.md) · [kb-content-cleaning.md](kb-content-cleaning.md)

## 1. What is logged (safe logging field definitions)

Every chat turn writes **one** JSON log line, `"message": "chat_turn"`, with a `turn` object. Only the fields below can
appear (`telemetry.SAFE_FIELDS`); anything else is dropped before writing, and any value that still looks like an
e-mail, phone number, CNIC, money amount, API key or a configured secret is replaced by `[redacted]` and counted
(`telemetry_redactions`).

| Field | Meaning | Example |
|---|---|---|
| `request_id` | Id of the HTTP request; also in the access log line | `5312a63b-…` |
| `user_ref` | Salted HMAC of the user id, 12 hex characters; groups one user's turns, cannot be reversed without `TELEMETRY_SALT` | `a91f03c27b4e` |
| `route` | `knowledge` · `transaction` · `account_data` · `general` · `guard` · `error` | `knowledge` |
| `intent` | Intent or block category | `product_faq`, `add_expense`, `blocked_prompt_injection` |
| `source` | What produced the reply (`rag`, `kb_fallback`, `clarification`, `backend_financial_api`, `dialogue`, `guardrail`, `output_guard`, `policy_guard`, `llm_general`, `greeting_fastpath`, `backend_unavailable`, `llm_unavailable`, `kb_unavailable`, `service_fallback`) | `rag` |
| `answer_status` | Knowledge route: `answered` · `conflict` · `no_source` · `out_of_scope` · `clarify` | `answered` |
| `language` | `en` · `roman_ur` · `ur` | `roman_ur` |
| `retrieval_mode` | `hybrid` · `lexical` · `tfidf_legacy` · `none` | `hybrid` |
| `retrieved_ids` | KB chunk ids that passed the threshold (public KB content) | `["off-01-002-is-hisabdo-free-to-use"]` |
| `cited_ids` | KB chunk ids cited in the reply | same |
| `retrieval_ms` | Retrieval time | `21.4` |
| `latency_ms` | End-to-end handling time (inside the service) | `44.0` |
| `llm_called` / `llm_provider` | Whether a model provider was called, and which | `false` |
| `tokens_used` | Tokens reported by the provider | `0` |
| `needs_review` | Official sources conflict (audit C-06) | `true` |
| `fallback` | `none` · `no_source` · `kb_unavailable` · `llm_error` · `backend_error` · `internal_error` | `none` |
| `error_category` | `none` · `llm_error` · `llm_timeout` · `backend_error` · `kb_unavailable` · `internal_error` | `none` |
| `kb_version` | First 12 hex of the KB index hash | `3be0c4f1a2d9` |
| `output_findings` | What the output guard removed | `["contact_or_identifier_removed"]` |

**Never logged** (enforced by `tests/test_dept3_operations.py`): message text, reply text, user id, amounts, names,
phone numbers, CNIC, e-mail addresses, the internal service token, API keys, prompt text. Other log events carry only
categories and ids: `guardrail_input_blocked` (`category`), `guardrail_output_blocked` (`findings`),
`kb_conflict_escalated` (`chunks`), `llm_call_failed` / `backend_call_failed` / `chat_failed` (`error_type` = the
exception class name only), `kb_index_unavailable`, `kb_index_degraded`, `kb_update_rejected` (`reasons`),
`kb_updated` (`kb`).

`TELEMETRY_SALT` must be set (a random secret, kept like the service token) in production so `user_ref` is stable
across restarts. If it is not set, a new random salt is used per process.

## 2. Metrics

`GET /api/v1/metrics` (same `X-Internal-Token` as the chatbot; 401 without it) returns:

* `counters`: `turns`, `source:<source>`, `answer_status:<status>`, `error:<category>`, `fallback:<name>`,
  `telemetry_redactions`, `telemetry_dropped_fields`
* `latency`: per route, over the last 2,000 turns: `n`, `p50_ms`, `p95_ms`, `max_ms`
* `kb`: `loaded`, `version`, `chunks`, `mode` (`hybrid` or `lexical`), `degraded` (reason or null)

Counters are per process and reset on restart; scrape them every minute into the monitoring system.

## 3. Alerts (thresholds from the measured baseline, scorecard section 3)

| Alert | Condition (5-minute window unless stated) | Why |
|---|---|---|
| Knowledge latency | `latency.knowledge.p95_ms` > 250 | Measured p95 on CPU is under 100 ms |
| Account / transaction latency | `latency.account_data.p95_ms` or `latency.transaction.p95_ms` > 150 | Measured p95 about 20 ms |
| Backend down | `error:backend_error` > 5% of `source:backend_*` | Users get "I can't load your figures right now" |
| Model provider failing | `error:llm_error` + `error:llm_timeout` > 5% of turns with `llm_called` | Knowledge falls back to source text; general chat to the error reply |
| Index not loaded | `kb.loaded == false` for 2 scrapes, or any `error:kb_unavailable` | Knowledge route answers "help library temporarily unavailable" |
| Index degraded | `kb.mode == "lexical"` in production, or `kb.degraded` set | Measured weaker: 9 wrong citations vs 3 (held-out) |
| Empty retrieval spike | `fallback:no_source` / `source:kb_fallback+rag` above twice its 7-day average | KB missing a topic, or retrieval broke |
| Conflicts | any `needs_review` | A product fact needs the owner's decision |
| Possible leak | any `guardrail_output_blocked` with `secret` or `prompt_text`, or `telemetry_redactions` > 0 | Investigate immediately (section 5.5) |
| Attack volume | `source:guardrail` above 3x its 7-day average | Abuse or a broken client |

## 4. Safe behaviour when things fail (implemented and tested)

| Failure | Behaviour | User sees | Logged as |
|---|---|---|---|
| KB index cannot be built at startup (file missing, unreadable, model error) | Knowledge route uses the `kb_unavailable` fallback; rebuild is retried after 60 s (not on every request) | "HisabDo's help library is temporarily unavailable, so I won't guess…" | `kb_index_unavailable`, `error:kb_unavailable` |
| Embedding model cannot load (`fastembed` missing, download or ONNX failure) | Retriever runs lexical (C15 threshold 3.857) | Normal cited answers, slightly weaker | `kb_index_degraded`, `kb.mode = lexical` |
| KB update file is bad | `reload_kb` validates first: readable, not empty, required fields, unique ids, not below 80% of the current size, `https` sources, no personal identifier; any failure keeps the current index serving | Nothing changes | `kb_update_rejected` with reasons |
| Empty retrieval | R2 no-source fallback | "I couldn't find this… so I won't guess" + support contact | `fallback:no_source` |
| Model provider error or timeout, knowledge route | The source text is quoted instead (extractive), still with citations | A cited answer | `error:llm_error` / `llm_timeout` |
| Model provider error, own figures | The backend's exact figures are shown as a fixed sentence, no model | "Balance: … PKR. Expenses this month: …" | `fallback:llm_error` |
| Model provider error, general chat | Fixed apology | "I can't answer that right now…" | `source:llm_unavailable` |
| Backend financial API error | Never estimate figures | "I can't load your figures right now, and I won't estimate them…" | `source:backend_unavailable`, `error:backend_error` |
| Any other exception | Safe reply, HTTP 200, no stack trace | "Sorry, something went wrong on my side…" | `chat_failed`, `error:internal_error` |

## 5. Procedures

### 5.1 Daily (5 minutes)

1. Open `/api/v1/metrics`: `kb.loaded`, `kb.mode = hybrid`, error counters near zero, p95 under the thresholds.
2. Any `needs_review` turns → forward the chunk ids to the product owner (conflict C-06 is open).
3. Any output-guard `secret` / `prompt_text` finding → 5.5.

### 5.2 KB refresh (every 30 days, and within 7 days of an app release: review policy P-FAQ)

```bash
python scripts/clean_knowledge_sources.py --fetch        # new snapshots + cleaned chunks
python -m pytest tests/test_clean_knowledge_sources.py tests/test_kb_privacy.py
python scripts/grounded_answer_eval.py --mode hybrid      # answer quality on the judged sets
```

Then reload without a restart (validation runs first; a bad file is rejected and the old index keeps serving):

```python
from src.financial_assistant import service
service.reload_kb()          # {"updated": True|False, "reasons": [...], "serving": {...}}
```

If cleaning reports `NOT FOUND ON PAGE` warnings, new conflicts or a large drop in chunks, stop and review before
reloading.

### 5.3 Recalibrate retrieval (when the KB, the glossary or the embedding model changes)

```bash
python scripts/retrieval_eval.py run --only C10   # hybrid
python scripts/retrieval_eval.py run --only C15   # lexical fallback
```

Copy the new production thresholds into `grounding/retrieval.py` (`HYBRID_*`, `LEXICAL_*`) and
`results/chosen_configuration.json`; `tests/test_grounded_answers.py` fails until they match. Run the two commands one
after the other, never in parallel: both write `comparison.json`.

### 5.4 Before every release

```bash
python -m pytest tests
python scripts/release_acceptance.py                                   # critical 25/25 and major 6/6 required
python scripts/safety_eval.py --suite 1.1 --model compliant --grounded on --label release
python scripts/dept3_scorecard.py --label release                      # compare with scorecard_after.json
```

A release ships only with the safety suite CLEARED and no scorecard metric worse than the last release without a
written reason.

### 5.5 Suspected leak

1. Find the `request_id` in the `guardrail_output_blocked` or redaction event; the reply was already replaced or
   redacted before it left the service.
2. If `secret`: rotate the internal service token and any provider key immediately; check which route produced it
   (`source`) and reproduce with `scripts/safety_eval.py --model compliant`.
3. Add the case to a new suite version (`attack_suite_v1.2.json`), fix, re-run all four configurations.

### 5.6 Backend or provider outage

Nothing to switch: the fallbacks in section 4 are automatic. Watch `error:backend_error` / `error:llm_*`; when the
counters stop growing, the service is healthy again. Do not enable estimated figures as a workaround.

## 6. Known open items

| Item | Owner |
|---|---|
| "galti ho gayi, 450 nahi 540 tha" is still routed `general`, not as a correction (missed before and after this change) | Intent router (Saba Talat) |
| "customer ko payment reminder kaise likhun?" is now routed `faq` (labelled `general` in the team's held-out set): one regression, accepted because the KB has a sourced answer | Intent router |
| Counters are in-process; a multi-worker deployment needs them exported (Prometheus or the log pipeline) | Platform |
| Latency figures are in-process timings on a development laptop CPU; production numbers must be re-baselined from `/api/v1/metrics` | Platform |
