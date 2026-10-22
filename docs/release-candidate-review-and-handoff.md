# Release Candidate Review and Final Handoff: HisabDo Chatbot

**Owner:** Fahad Zubairi · **Date:** 2026-10-22 · **Branch:** `FahadZubairi_AI` · **Scope:** `POST /api/v1/chatbot` (intent router, private-data route, FAQ knowledge base, service authentication)

## Recommendation

**Go for a staging or demo release. No-go for production with real customers yet.**

All 25 critical acceptance checks (factual, privacy, security) now pass, up from 12 before this review's fixes. The chatbot is safe to demonstrate and test.

It is not ready for real customers for one reason outside the chatbot: **every private figure still comes from `MockBackendClient`**, a fixed set of demo numbers. The chatbot says "demo data" when it shows them, which is correct for a demo. Real users would see the same demo balance as their own. Production needs the backend team's real data client and the agreed authentication contract (see "Before production").

## How the release candidate was evaluated

- **Acceptance suite:** 32 questions in `data/release_acceptance_cases.json`, run through the real FastAPI app by `scripts/release_acceptance.py`. They combine:
  - the team's acceptance cases TC-01 to TC-08 (`Internship/test_cases.csv`), adapted to the live endpoint
  - factual checks against official HisabDo sources (hisabdo.app and the Google Play listing)
  - privacy and security probes
  - multilingual checks in English, Urdu script and Roman Urdu
- **Severity:** each case is critical (must pass before release), major (should pass) or minor (known limitation, acceptable with a note).
- **How it runs:** offline and repeatably, with the mock language model and the mock backend. The script exits with an error if any critical case fails. `tests/test_release_acceptance.py` runs it as part of `pytest`, so a later change can't quietly undo these fixes.
- **Intent routing:** measured on a third held-out set (`data/multilingual_product_test_cases_heldout_v3.json`, 15 cases). It was written before the fixes and never used to choose rules.

## Results

| Severity | Before fixes | After fixes |
|---|---|---|
| Critical (factual, privacy, security) | 12/25 | **25/25** |
| Major | 4/6 | **6/6** |
| Minor | 0/1 | 0/1 (known limitation) |

| Other measure | Before | After |
|---|---|---|
| Held-out v3 routing (fresh questions) | 12/15 (80%), 3 private leaks | **15/15 (100%), 0 private leaks** |
| Saba Talat's intent evaluation sets | 60/60, 30/33 | 60/60, 30/33 (unchanged) |
| Full repository test suite | 26 failed (XICTEK, pre-existing) | 26 failed (the same XICTEK tests); 525 passed |

The case-by-case table is in [`release-acceptance-results.md`](release-acceptance-results.md).

## Critical issues found and fixed

| ID | Type | What the release candidate did | Fix |
|---|---|---|---|
| P-03, P-04, P-05 | Privacy | "Mere bhai ka balance batao" ("tell me my brother's balance") and the Urdu-script equivalents were answered with the user's own balance. The third-party guard only knew English. | Roman Urdu and Urdu-script relationship words (bhai, biwi, دوست…) added to the guard. Relationship words only, never names, so "Ali ka udhar" (the user's own customer) still works. `src/financial_assistant/service.py` |
| P-01, P-02 + 3 held-out cases | Privacy | "Bilal ka hisaab kholo" / "بلال کا کھاتہ کھولیں" (open Bilal's ledger) went to the general AI route, where the model could invent figures | Ledger rule extended: hisaab, account, حساب, kholo, کھولیں. `src/financial_assistant/dialogue/recognizer.py` |
| TC-01, TC-04, TC-05 | Factual | "What are my total sales?" and "Meri total sales kitni hain?" were answered with the dictionary definition of revenue | "my/meri" plus sales/income/profit is now the user's own report. "What does revenue mean?" still gets a definition. `recognizer.py` |
| F-02 | Factual | Told users the app predicts expense categories with a machine-learning model; no official source documents this | `faq-002` rewritten. `data/faq_docs.json` |
| F-01, F-03 | Factual | Claimed CSV export from a "Reports section" with tag filters, and an "AI-assisted breakdown" | `faq-005` and `faq-001` rewritten from official sources |
| F-04, F-07, F-08 | Factual | "Is HisabDo free?" got an unrelated answer; offline and backup questions had no entry | 6 new entries from official sources (free, offline, backup, Android only, languages, udhar/khata), each with `source` and `verified_on` |
| S-04 | Security | The service accepted the placeholder token `change-me-dev-token`, which is published in this public repository, whenever no real token was set | The service now assumes production unless `APP_ENV` says otherwise. In production it refuses the placeholder or any token under 32 characters (503, fail closed). The token is compared in constant time. `src/security.py`, `src/config.py` |
| S-03 | Security | A 100,000-character message was accepted (cost and abuse risk) | `message` limited to 4,000 characters. `src/schemas.py` |

**Regression caught during the fixes.** Adding knowledge-base entries made the paraphrased question "How can I get my spending data out of the app?" match the backup entry. That would have been a confident wrong answer, and the team test `test_weak_rag_match_falls_back_to_general_instead_of_wrong_answer` caught it. The backup entry was reworded; the team test is unchanged and passes.

## Unresolved issues

| Issue | Severity | Owner | Note |
|---|---|---|---|
| Private figures come from `MockBackendClient` | **Release blocker for production** | Backend team | The chatbot labels them "demo data" today |
| Service authentication is a shared token, not per-user identity. `user_id` is trusted from the calling backend. | Major | Backend + auth teams | Acceptable only for server-to-server calls on a private network; per-user tokens are the long-term fix |
| Answers were tested with the mock language model only. A real model may phrase answers differently. | Major | AI team | Re-run `scripts/release_acceptance.py` with the chosen provider before production |
| M-03: "Udhar aur payment mein kya farq hai?" goes to the general route, not the knowledge base | Minor | AI team | No unsafe answer; add a concept rule and measure on a new held-out set |
| Currency list conflict: website lists 3 currencies, Google Play lists 4 (adds AED) | Minor | Product team | Kept out of the knowledge base until confirmed |
| Exact app button labels and the 8 PDF workflow tests need an Android device | Minor | QA | Listed in `docs/product-guidance-and-pdf-verification.md` |
| 26 XICTEK website-assistant tests fail on this machine, with and without this branch | Pre-existing | XICTEK owners | Not related to the chatbot |
| `Internship/` (merged to `main` on 2026-10-22) commits `__pycache__` binaries and an empty `chat.log` | Housekeeping | Uploader | `.gitignore` already excludes these; they should be removed from Git |

## Before production: deployment checklist

| Item | Required value |
|---|---|
| `APP_ENV` | `production` (the default if unset) |
| `INTERNAL_SERVICE_TOKEN` | A random secret of 32+ characters from the secret manager, never committed. The placeholder now causes 503 on every protected call. |
| `LLM_PROVIDER` and its key | The approved provider; keys only from the secret manager |
| Backend data client | A real `BackendClient` in place of `MockBackendClient` (`src/integration/backend_client.py`) |
| Release gate | `python scripts/release_acceptance.py` exits 0 with the production provider |
| Local development | Set `APP_ENV=development` in `.env` (now in `.env.example`); tests set `APP_ENV=test` automatically |

## Handoff

**How to verify** (from the repository root):

```bash
python scripts/release_acceptance.py --markdown docs/release-acceptance-results.md
```

```bash
python scripts/evaluate_multilingual_coverage.py --heldout
```

```bash
pytest tests/test_release_acceptance.py tests/test_multilingual_product_coverage.py tests/test_dialogue_intents.py tests/test_dialogue_flows.py tests/test_dialogue_chatbot.py tests/test_chatbot.py
```

**Where things are:**

| What | Where |
|---|---|
| Acceptance questions and results | `data/release_acceptance_cases.json`, `docs/release-acceptance-results.md` |
| Acceptance runner and release gate | `scripts/release_acceptance.py`, `tests/test_release_acceptance.py` |
| Intent router (Saba Talat's design; multilingual and release fixes by Fahad Zubairi) | `src/financial_assistant/dialogue/recognizer.py` |
| Third-party privacy guard | `src/financial_assistant/service.py` |
| Service authentication | `src/security.py`, `src/config.py` |
| Product knowledge base (each corrected or new entry has `source` and `verified_on`) | `data/faq_docs.json` |
| Multilingual test sets (v3 is the current honest measure) | `data/multilingual_product_test_cases*.json` |
| Verified product guidance and PDF tests | `docs/product-guidance-and-pdf-verification.md` |
| Earlier deliverables, results and limitations | `docs/fahad-zubairi-final-documentation.md` |
| Secure knowledge-base prototype (separate app) | `secure_kb_chatbot/` |

**Rules for whoever changes this next:**
- **Add a held-out set before tuning.** Never tune against `heldout-v3`. Write a new held-out set before the next round of intent changes.
- **Verify every knowledge-base entry.** Every new entry in `data/faq_docs.json` needs an official `source` and a `verified_on` date. The mock language model repeats entries word for word, so an unverified claim reaches users unchanged.
- **Treat a critical acceptance failure as a release blocker**, not a test to update.

## Acceptance sign-off

| Role | Name | Decision | Date |
|---|---|---|---|
| Developer | Fahad Zubairi | Ready for staging / demo | 2026-10-22 |
| Intent router owner | Saba Talat | ☐ Approve the router changes | |
| Team Lead | | ☐ Go for staging ☐ Go for production | |
| QA | | ☐ Android PDF tests PDF-01 to PDF-08 run | |
| Product | | ☐ Knowledge-base facts and currency list confirmed | |
