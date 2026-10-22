# Final Documentation: Secure, Grounded and Multilingual HisabDo Chatbot

**Owner:** Fahad Zubairi · **Final update:** 2026-10-19 · **Branch:** `FahadZubairi_AI` · **Repository:** https://github.com/usmankhalid172/hisabdo-webapp-ai

**Release status (2026-10-22):** see [`release-candidate-review-and-handoff.md`](release-candidate-review-and-handoff.md). All 25 critical acceptance checks pass; recommended for staging or demo, not yet for production (private figures still come from the mock backend).

This branch adds three things to the HisabDo AI work:

1. **A secure, knowledge-grounded chatbot prototype** in `secure_kb_chatbot/`.
2. **Verified product guidance and PDF checks** for the real HisabDo app.
3. **Multilingual tuning of the team chatbot's intent router**, measured on held-out questions.

Everything is tested offline, without API keys, and nothing outside these files changes behaviour.

## What was delivered

| Deliverable | Where | Status |
|---|---|---|
| Secure chatbot prototype: login checks, business isolation, demo vs actual labelling, reporting periods | `secure_kb_chatbot/` | Done; 259 tests pass |
| Semantic knowledge base: embeddings, relevance threshold, source attribution, safe fallback, versioning | `secure_kb_chatbot/chatbot/` (`kb.py`, `retrieval.py`, `vector_store.py`) | Done; never run against live Gemini embeddings (no key available) |
| Verified knowledge base, version 1.1.0 | `secure_kb_chatbot/kb/v1/` | 11 entries verified against official sources; 1 kept as draft (sources conflict) |
| Conversation management: create, rename, archive, delete, purge | `secure_kb_chatbot/chatbot/conversations.py` | Done |
| Product guidance and PDF verification | `docs/product-guidance-and-pdf-verification.md` | Features verified; exact button labels still need the app |
| Multilingual test coverage (English, Urdu script, Roman Urdu) | `data/multilingual_product_test_cases*.json`, `scripts/evaluate_multilingual_coverage.py` | 93 cases in three sets |
| Intent-router tuning (Saba Talat's router) | `src/financial_assistant/dialogue/recognizer.py` | Two rounds; held-out results below |
| Step-by-step implementation guide | `secure_kb_chatbot/docs/IMPLEMENTATION_GUIDE.md` | Done |

## How the pieces fit

```
User message (English / Urdu / Roman Urdu)
  -> Intent router (src/financial_assistant/dialogue)     what does the user want?
       private figures   -> account_data route: only the authenticated backend, never the AI model
       product question  -> knowledge route: verified knowledge base, cited
       new entry         -> transaction route: step-by-step questions, then confirmation
       other             -> general assistant
```

The prototype in `secure_kb_chatbot/` shows how the knowledge and private-data routes can be made safe:

- **Grounding.** Answers about the business come only from that business's records, and every claim cites a record ID such as `[C-001]` or `[KB-003]`.
- **Citation checks.** A validator removes any citation to a record the model wasn't given, and flags amounts that don't appear in the data.
- **Retrieval threshold.** A question scoring below the threshold gets "I don't have verified information", never a guess.

## Final results

**Intent routing, multilingual product questions.** "Routed correctly" means the question reached the right part of the system. "Private on a public route" means a question about the user's own figures reached a route where the AI model could invent numbers.

| Measure | Start | Round 1 | Round 2 (final) |
|---|---|---|---|
| Fresh held-out v2 (27 cases, honest measure) | n/a | 18/27 (67%) | **22/27 (81%)** |
| Private questions on a public route (held-out v2) | n/a | 5 | **2** |
| Round-1 held-out (27 cases) | 10/27 (37%) | 22/27 (81%) | 27/27 (tuning material by then) |
| Saba's labelled set | 60/60 | 60/60 | 60/60 |
| Saba's held-out set | 30/33 | 30/33 | 30/33 |

Each held-out set was written **before** the changes it measures and was never used to choose rules. Round 1's held-out set became tuning material in round 2, which is why it reads 100%. The v2 set is the honest final number.

**Tests:**

| Suite | Result |
|---|---|
| `secure_kb_chatbot` (run inside the folder) | 259 passed |
| Saba's dialogue tests | 169 passed |
| Multilingual regression tests | 69 passed |
| Full repository suite | 26 failures in `tests/xictek_website_assistant`, which fail identically on `main` without this branch; no new failures |

## How to run

From the repository root:

```bash
python scripts/evaluate_multilingual_coverage.py --heldout
```

```bash
pytest tests/test_multilingual_product_coverage.py tests/test_dialogue_intents.py tests/test_dialogue_flows.py tests/test_dialogue_chatbot.py
```

The prototype (its tests only run from inside its folder):

```bash
cd secure_kb_chatbot
pip install -r requirements.txt
pytest
```

To index the verified knowledge base, `GEMINI_API_KEY` must be set as an environment variable (never committed). From inside `secure_kb_chatbot`:

```bash
python scripts/build_kb_index.py kb/v1 --activate
```

```bash
python scripts/calibrate_threshold.py kb/eval_questions.json
```

## Known limitations

| Limitation | Impact | Next step |
|---|---|---|
| 2 of 27 fresh private questions still reach a public route ("Bilal ka hisaab kholo", "بلال کا کھاتہ کھولیں") | The AI model could answer a ledger request with made-up figures | Add "hisaab", "kholo" and "کھولیں" ledger rules, then measure on a new held-out set |
| Live embeddings and real Supabase logins are untested | The relevance threshold (0.60) is a starting guess | Run `calibrate_threshold.py` with a Gemini key; confirm the token signing method with the auth team |
| Exact app button labels are not verified | The guidance stays at feature level | Check each instruction on an Android device; run PDF tests PDF-01 to PDF-08 |
| Currency list conflict (website: 3; Google Play: 4, adding AED) | KB-006 cannot be verified | Product team to confirm |
| 3 unsupported claims in the team's `data/faq_docs.json` (CSV export, category/tag filters, ML auto-categorization) | The live chatbot can repeat them | Product team to confirm or correct |
| The prototype stores data in SQLite | Not the shared Supabase database the team architecture requires | Port `Repository` and `VectorStore` to Supabase and pgvector |

## Related work by the same owner

These are on branch `Fahad-zubairi-ai-intern` of `usmankhalid172/hisabdo-ai`:

- Day 3 audit (`evals/day3-audit/`): the chat backend audited and tested against a fake model; 14 of 21 checks failed, including that anyone with a session ID could read that person's chat.
- Day 4 security verification (`evals/day4-security/`): an independent review of the secure financial API; 38 probes, 31 pass, 7 fail.
