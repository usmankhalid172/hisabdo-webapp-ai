# Department 3 Quality Scorecard: Before / After

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-04 · **Branch:** `FahadZubairi_AI`
**Measured by:** `scripts/dept3_scorecard.py` → `data/dept3_scorecard/scorecard_before.json`, `scorecard_after.json`
**Runbook:** [dept3-monitoring-runbook.md](dept3-monitoring-runbook.md)

## 1. Scorecard

| Area | Metric | Before | After |
|---|---|---|---|
| Router (account, balance, expense routing) | Known misroutes from recent evaluations fixed | 0 / 10 | **10 / 10** |
| | Team labelled intent sets (6 sets, 201 questions) | 189 / 201 | **191 / 201** |
| Answers, hybrid (judged sets) | Day 1 failed questions: cited correct answers | 5 / 7 answerable | 5 / 7 |
| | Held-out: cited correct answers | 28 | **31** |
| | Held-out: unrelated source cited | 4 | **3** |
| | Held-out: "must be empty" refused | 69 / 69 | 68 / 69 |
| Answers, lexical fallback | Held-out: cited correct answers / unrelated cited | 25 / 9 | **27 / 8** |
| Retrieval (C10, cross-validated) | Held-out fully correct / unrelated passages | 101 / 8 | 100 / **7** |
| Release gate (grounded answers on) | critical · major · minor | 25/25 · 6/6 · 0/1 | 25/25 · 6/6 · **1/1** |
| Safety suite v1.1 (4 configurations) | Verdict | CLEARED | CLEARED |
| Fallbacks | Model error, backend error, index failure, bad index update, unexpected error | errors surfaced as 500 / 502 or a crash | **safe replies, all tested** |
| Logging | Per-turn outcome, source ids, latency, error category | request access log only | **`chat_turn` event, 20 allowlisted fields** |
| Tests | Passing (26 pre-existing XICTEK failures unchanged) | 730 | **759** |

## 2. What was fixed

### 2.1 Router (account / balance / expense flows)

| Case | Message | Before | After | Fix |
|---|---|---|---|---|
| R-1 | Is my khata safe if I change my phone? | correct_transaction | faq | "change" without an amount is not a correction |
| R-2 | Udhar aur payment mein kya farq hai? (and Urdu) | general | faq | "farq / difference / فرق" are concept questions |
| R-3 | What is the capital of France? · weather · install Python | faq | general | a "product question" must mention the app, bookkeeping or money |
| R-3d | What is my customer's phone number? | faq | account_query | stored private data, never the KB |
| R-4 | Should I register my shop for sales tax? | report | faq | "my … sales" is a figures request only with a figure word (how much, total, show) |
| R-5 | How long does HisabDo keep my data after I delete my account? | account_query | faq | an app-capability question beats "my account" when no figure is asked |
| R-6 | Who won the 1992 cricket world cup? | add_expense | general | a number in a wh-question with no money word is not an amount |

Labelled sets: 3 questions fixed (held-out v2), **1 regression**: "customer ko payment reminder kaise likhun?" is
labelled `general`, now `faq`. Accepted: the KB has a sourced answer ("Can HisabDo send payment reminders?"); listed in
the runbook's open items. Still open, unchanged: "galti ho gayi, 450 nahi 540 tha" is not recognised as a correction.

### 2.2 Urdu retrieval content

The query rewrite read the app's Urdu name "حساب دو" as "ledger account", "محفوظ کریں" (save) as "safe", and did not
know "wapis lena" (recover). Phrases now match before single words and are removed from the text first.
Effect on held-out answers (hybrid):

| Question | Before | After |
|---|---|---|
| حساب دو میں خرچہ کیسے درج کروں؟ (record an expense) | cited Customer Ledger (unrelated) | cites Expense Tracker |
| اسٹیٹمنٹ کو پی ڈی ایف میں کیسے محفوظ کریں؟ (save statement as PDF) | cited Data Security (unrelated) | cites "Can I export reports?" |
| کیا حساب دو مہینے کی رپورٹ پی ڈی ایف میں دیتا ہے؟ (monthly PDF report) | background only | cites Generating Reports with HisabDo |
| Have you sent the payment to my customer? | refused (out of scope) | **new wrong citation**: now routed `faq`, cites an overdue-balance article |

The last row is a regression from the router change and is the one "must be empty" question no longer refused.
The retrieval threshold was re-measured after both fixes (C10 0.566, C15 3.857) and updated in code.

Measurement note: the held-out questions were already seen in earlier tasks, so after-numbers on them are optimistic
for the fixes made today; the 201 labelled router questions also include sets the router was tuned on before.

### 2.3 Latency: regex recompilation on every request

Profiling the knowledge route showed most of its time spent **recompiling regular expressions**: the query rewrite
built about 140 patterns per call and the router built one per cue, overflowing Python's regex cache so every pattern
was recompiled on every message. All three are now compiled once. In-process timing after the fix: knowledge turn
42 ms (of which about 15 ms is the embedding model), expense turn 9.6 ms, balance turn 10.4 ms.

## 3. Latency and error metrics (end to end, `POST /api/v1/chatbot`, 40 requests per flow)

| Flow | Before p50 / p95 ms | After p50 / p95 ms |
|---|---|---|
| Knowledge answer (hybrid retrieval, cited) | 35.0 / 44.3 | 65.7 / 70.6 |
| Knowledge, no source (fallback) | 34.9 / 40.8 | 65.2 / 72.2 |
| Balance / account (backend mock) | 11.7 / 16.9 | 25.3 / 34.7 |
| Expense entry (dialogue) | 9.5 / 10.9 | 24.6 / 33.6 |
| Guard blocked | 6.2 / 8.1 | 22.1 / 29.6 |
| Off-topic boundary | 7.5 / 10.9 | 21.9 / 25.9 |
| Retrieval only | 19.1 / 21.3 | 30.7 / 34.9 |
| One-off index build (embeds 364 chunks) | 62.8 s | 94.7 s |

**Read with care.** The after run was slower on every flow, including the one-off index build, which today's changes
do not touch (63 s → 95 s). That points to a busier machine during the second run rather than to the code; the
in-process timing in 2.3, taken on the same build, is faster. Each flow added about 1 ms of telemetry and guardrail
work in a direct measurement. Both runs are on a development laptop CPU: production must be baselined from
`/api/v1/metrics` (runbook section 2). Every flow stays far inside the alert thresholds (knowledge p95 < 250 ms).

**Errors in the measurement runs:** 0 `llm_error`, 0 `backend_error`, 0 `kb_unavailable`, 0 `internal_error`. Each
fallback was exercised by fault injection in `tests/test_dept3_operations.py` instead (model timeout, backend down,
index build failure, bad index update, unexpected exception, embedding model failure).

## 4. Provider usage and cost

| Item | Per knowledge request | Cost |
|---|---|---|
| Embedding calls | 1 query embedding (bge-small-en-v1.5, local ONNX) | **No API cost**: runs on the service's CPU; one-off index build about 1 minute per process start |
| LLM calls, default deployment (mock) and every Urdu / Roman Urdu answer | 0 (answers quote the source text) | none |
| LLM calls with a real provider, English knowledge answers | 1 | about **1,509 prompt tokens** per call (system prompt + grounding rules + 2 sources + question; estimated as characters / 4) plus a short answer |
| Account, balance, expense flows | 0 model calls for expense entries and figures from the backend; 1 call to word the balance summary when a real provider is configured | balance summary prompt is about 1,000 tokens |
| Guard-blocked and off-topic messages | 0 | none |

Monthly cost with a real provider = English knowledge requests × (about 1,509 input tokens × the provider's input
price + answer tokens × its output price). Prices change, so they are not hard-coded here: read `tokens_used` per turn
from the `chat_turn` logs and multiply by the current price of the configured provider.

## 5. Delivered

| Item | Where |
|---|---|
| Router fixes (7 rules) | `src/financial_assistant/dialogue/recognizer.py` |
| Urdu glossary and phrase-first rewrite; compiled patterns | `src/financial_assistant/grounding/retrieval.py`, `dialogue/categories.py` |
| Re-measured thresholds | `grounding/retrieval.py`, `data/retrieval_eval/results/` |
| Safe telemetry, metrics endpoint | `src/financial_assistant/telemetry.py`, `router.py` (`GET /api/v1/metrics`) |
| Fallbacks and index updates | `service.py` (`handle_chat`, `_generate`, `get_grounded_answerer`, `reload_kb`), `grounding/answer.py`, `retrieval.validate_kb` |
| Tests | `tests/test_dept3_operations.py` (29) |
| Scorecard runner and results | `scripts/dept3_scorecard.py`, `data/dept3_scorecard/` |
| Runbook with safe logging fields | `docs/dept3-monitoring-runbook.md` |
