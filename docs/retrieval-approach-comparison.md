# Retrieval Approach Comparison — Day 1 Failed Queries

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-10-28 · **Branch:** `FahadZubairi_AI`
**Corpus:** `data/kb/approved/kb_chunks.jsonl` — 364 cleaned chunks from the 23 approved sources ([kb-content-cleaning.md](kb-content-cleaning.md))

## 1. Result

**Chosen configuration — C10:** router gate → query normalisation + Roman Urdu/Urdu rewrite → hybrid retrieval
(0.6 × bge-small-en cosine + 0.4 × saturated BM25) → **threshold 0.586, top-k 2, margin 0.05**.

| | Day 1 production | **C10 (chosen)** |
|---|---|---|
| Day 1 failed questions fully correct | 9 / 19 | **17 / 19** |
| Day 1 answerable questions with an answering passage | 1 / 7 | **5 / 7** |
| Held-out questions fully correct (cross-validated) | — | **101 / 120** |
| Held-out "must be empty" questions left empty | — | **68 / 68** |
| Held-out answerable questions with an answering passage in context | — | 32 / 51 |
| Unrelated passages in context (held-out) | — | 8 of 85 (precision 0.90) |

The two Day 1 questions C10 still fails are **router decisions, not retrieval**: D16 "Udhar aur payment mein kya farq
hai?" is routed `general` and D18 "Is my khata safe if I change my phone?" is still routed `correct_transaction` (the
Day 1 bug is still present in the router). Both have answering passages in the KB.

**Not achieved:** zero unrelated passages on held-out questions. No configuration tested reached it while still
answering most questions; the closest (C4) did so by answering only 10 of 51. See section 6.

## 2. Test sets

| Set | Size | Use |
|---|---|---|
| **Day 1 failed questions** (`queries_dev_day1.json`) | 19 | From the Day 1 review (22 Oct, table "Top 20 weak or failed questions"). #19-#20 are API/auth issues, not retrieval; #19 (100,000 characters) is covered by a test of the 512-character query cap. |
| **Held-out** (`queries_heldout.json`) | 120 | 108 team questions from the multilingual product sets (EN / Roman Urdu / Urdu), 9 release-acceptance cases not already in Day 1, 10 off-topic questions. Never used to pick a method or write the glossary. |

Each question has an expected outcome:

* **answer** — the approved KB answers it: an answering passage must reach the context, and nothing unrelated.
* **none** — not a knowledge question (own figures, someone else's account, a transaction, a correction, off-topic):
  the context must be empty.
* **no_answer_in_kb** — a knowledge question the sources don't answer (e.g. "How does automatic expense
  categorization work?", audit C-02): nothing unrelated may reach the context.

A question is **fully correct** only if it meets its expectation completely.

### Relevance judgments (`qrels.json`)

* Pooling: the union of the top 5 of every method (C1–C7) for every knowledge question — 60 questions, ~990 pairs,
  each judged by hand: **2** answers the question · **1** same topic, does not answer · **0** unrelated.
* An answering passage that every method missed was added by hand where it was known (12 questions, listed in
  `qrels.json` "method"; 4 of them Urdu-script questions that take the answers of their English twin), so the miss
  counts against retrieval instead of turning the question into "unanswerable".

## 3. Approaches compared

| | Lexical | Semantic | Rewrite | Rerank | Metadata filter |
|---|---|---|---|---|---|
| C1 | TF-IDF (production algorithm, `faq_rag.py`) | | | | |
| C2 | BM25 | | | | |
| C3 | | bge-small-en-v1.5 | | | |
| C4 | | multilingual MiniLM-L12 | | | |
| C5 | BM25 | bge | | | |
| C6 | BM25 | bge | ✓ | | |
| C7 | BM25 | bge | ✓ | ms-marco MiniLM cross-encoder (top 20) | |
| C8 | BM25 | bge | ✓ | ✓ | rule gate (regex: own figures, third party, transactions) |
| C9 | BM25 | bge | ✓ | ✓ | rule gate + legal-scope filter |
| **C10** | **BM25** | **bge** | **✓** | | **router gate (intent `faq` only)** |
| C11 | BM25 | bge | ✓ | ✓ | router gate (`faq`) |
| C12 | BM25 | bge | ✓ | | router gate (`faq` + `general`) |
| C13 | BM25 | bge | ✓ | ✓ | router gate (`faq` + `general`) |
| C14 | BM25 | bge | ✓ | ✓ | router gate (`faq` + `general`) + legal-scope filter |

* Models run locally on CPU through `fastembed` (ONNX): no API key, nothing sent to a third party.
* **Rewrite** = normalise (NFKC, lower case, punctuation, 512-character cap) + append English KB terms for Roman
  Urdu / Urdu words (`GLOSSARY`, written from the Day 1 questions and general finance vocabulary before the held-out
  questions were read, then frozen).
* **Router gate** = the team intent router that already decides routes in production (`dialogue/recognizer.py`);
  only messages it labels `faq` reach the KB.
* **Legal-scope filter** = Privacy Policy / Terms / Disclaimer chunks only for privacy or legal questions.

## 4. How threshold and top-k were set (measured, not estimated)

For every configuration a grid is swept on actual results: thresholds at the midpoints between scores observed on
the tuning questions, top-k ∈ {1, 2, 3, 4, 5, 8}, margin-to-best ∈ {none, 0.05 … 3.0}. Objective: most questions
fully correct, then fewest unrelated passages; among equal thresholds the middle of the longest tied run.

* **Two-fold cross-validation** (the numbers in section 5): the held-out set is split in two halves stratified by
  expected outcome; parameters are tuned on Day 1 + one half and tested on the other half, then swapped. Every
  held-out question is scored by parameters that never saw it.
* **Production parameters**: tuned on Day 1 + all held-out questions. For C10 the cross-validated thresholds were
  0.58556 and 0.58540 and the production value is 0.58580 — stable across folds.

**Tuning on the 19 Day 1 questions alone is not enough** — measured, column "Day 1 only" below. None of the Day 1
"must be empty" questions are off-topic, so with a gate in front nothing pushes the threshold up. The first run
picked "no threshold" for the gated configuration and let 124 unrelated passages into held-out contexts. The Day 1
set is kept as the tuning core, extended by cross-validation.

## 5. Results

Held-out = 120 questions, cross-validated. "Answer" = answerable questions with an answering passage in context and
nothing unrelated. Latency = measured per question on CPU in this run (reranker scores are cached between
configurations that share candidates, so C7 shows the true reranker cost).

| Config | Day 1 (prod params) | Held-out, Day 1-only tuning (unrelated) | **Held-out, CV** | Answer | Must-be-empty | Recall | Context precision | Unrelated | ms |
|---|---|---|---|---|---|---|---|---|---|
| C1 TF-IDF (production algorithm) | 14/19 | 68/120 (15) | **72/120** | 5/51 | 66/68 | 0.10 | 0.67 | 3 | 5 |
| C2 BM25 | 16/19 | 73/120 (3) | **73/120** | 6/51 | 66/68 | 0.12 | 0.67 | 3 | 1 |
| C3 Dense bge-small-en | 16/19 | 77/120 (11) | **79/120** | 17/51 | 61/68 | 0.35 | 0.69 | 15 | 50 |
| C4 Dense multilingual MiniLM | 16/19 | 75/120 (8) | **79/120** | 10/51 | 68/68 | 0.20 | 1.00 | 0 | 18 |
| C5 Hybrid BM25+bge | 16/19 | 81/120 (1) | **80/120** | 12/51 | 67/68 | 0.24 | 0.93 | 1 | 37 |
| C6 Hybrid + query rewrite | 16/19 | 79/120 (10) | **83/120** | 23/51 | 59/68 | 0.49 | 0.80 | 11 | 21 |
| C7 Hybrid + rewrite + rerank | 16/19 | 78/120 (10) | **82/120** | 14/51 | 67/68 | 0.29 | 0.92 | 2 | 1983 |
| C8 C7 + rule gate | 16/19 | 79/120 (13) | **78/120** | 22/51 | 55/68 | 0.45 | 0.74 | 16 | 29 |
| C9 C8 + scope filter | 16/19 | 79/120 (13) | **78/120** | 22/51 | 55/68 | 0.45 | 0.74 | 16 | 546 |
| **C10 C6 + router gate (faq)** | **17/19** | 97/120 (6) | **101/120** | **32/51** | **68/68** | **0.67** | 0.90 | 8 | 155 |
| C11 C7 + router gate (faq) | 17/19 | 92/120 (0) | **95/120** | 27/51 | 67/68 | 0.55 | 0.92 | 5 | 148 |
| C12 C6 + router gate (faq+general) | 16/19 | 95/120 (8) | **98/120** | 31/51 | 66/68 | 0.65 | 0.87 | 10 | 174 |
| C13 C7 + router gate (faq+general) | 17/19 | 91/120 (2) | **93/120** | 27/51 | 65/68 | 0.55 | 0.90 | 7 | 165 |
| C14 C13 + scope filter | 17/19 | 91/120 (2) | **93/120** | 27/51 | 65/68 | 0.55 | 0.91 | 6 | 164 |

Full per-question results, chosen parameters per fold and the sweep grids: `data/retrieval_eval/results/comparison.json`.
Day 1 production reproduction: `results/day1_baseline.json`. Raw top-10 rankings: `results/rankings_top10.json`.

## 6. What the measurements show

1. **A threshold alone cannot keep unrelated content out.** Without a gate, own-figure questions ("What were my
   expenses in September?") score as high as real product questions against the expense articles: for the best
   method only 21 of 47 found answers score above every "must be empty" question. Every ungated configuration
   either leaks or misses most answers.
2. **The router is the right metadata filter; a second set of regexes is not.** The regex gate never blocked a
   product question but caught only 15 of 68 held-out negatives (it was written from 19 questions). The team router
   blocks 64 of 68; the threshold then removes the 4 off-topic questions it lets through (weather, capital of
   France, installing Python, a customer's phone number). C10 leaves all 68 empty.
3. **Hybrid beats either half.** BM25 alone finds exact words but misses paraphrases (recall 0.12); dense alone
   finds paraphrases but leaks (15 unrelated). Combined (C5) recall rises and leakage falls.
4. **Query rewrite is the largest single gain for Roman Urdu / Urdu.** C5 → C6 doubles answerable questions
   answered (12 → 23). It also lets more unrelated text in without a gate, which the router then removes (C10).
5. **The reranker does not pay for itself here.** It lowers unrelated passages (C10 8 → C11 5) but loses 5
   answered questions, costs ~2 s per question on CPU, and its threshold is unstable across folds (-7.8 vs -4.7).
   Worth revisiting with a multilingual reranker on a GPU.
6. **Letting `general` messages reach the KB (C12) does not help overall**: D16 becomes answerable, but more
   off-topic text reaches the threshold (98 vs 101). Better to fix the router for concept questions.
7. **The legal-scope filter changes nothing measurable** (C13 vs C14): legal chunks were rarely the problem.

## 7. Where C10 still fails (19 held-out questions)

* **Urdu script: 7 of 16 answerable** questions answered. Glossary gaps — e.g. `محفوظ کریں` ("save") is mapped only
  to "safe", so "save a statement as PDF" retrieves the Data Security section; `wapis` (back) is missing, so "how
  to get udhar back" never reaches the follow-up articles. The glossary was frozen before the held-out test, so
  these were not patched; they are the next improvement, to be re-measured on a fresh set.
* **How-to questions with no step-by-step source** ("How do I record udhar given to a customer?"): the KB has
  feature descriptions, not instructions, so only background passages (grade 1) come back — the chatbot will say it
  has no exact steps rather than invent them.
* **8 unrelated passages** reached 8 answerable-question contexts: 4 Urdu-script questions, 2 next to an answering
  passage (H-EXP-EN-1, H-KHA-EN-2) and 2 Roman Urdu khata questions (H-H-KHA-RU-1, H-H2-KHA-RU-2). None reached a
  "must be empty" question.

## 8. Issues for other owners

| # | Issue | Owner |
|---|---|---|
| R-1 | Router still sends "Is my khata safe if I change my phone?" to `correct_transaction` (Day 1 #17) | Saba Talat (intent router) |
| R-2 | Router sends Roman Urdu / Urdu concept questions ("Udhar aur payment mein kya farq hai?") to `general`, so they never reach the KB | Saba Talat |
| R-3 | Router labels "What's the weather in Lahore?", "capital of France", "install Python" and "my customer's phone number" as `faq`; C10's threshold catches them, but the router should not | Saba Talat |

## 9. Limits of this evaluation

* One judge (the author). Criteria are written in `qrels.json`; a second judge on a sample would measure agreement.
* Router accuracy on these sets is optimistic: its rules were tuned on the same multilingual sets (commit 0f2a1b1).
* The production threshold (0.5858) sits exactly at D12's score ("What is HisabDo?"). Recalibrate with
  `python scripts/retrieval_eval.py run` whenever the KB, the glossary or the embedding model changes.
* Not wired into `/api/v1/chatbot`: switching the live retriever needs `fastembed` in production, the KB swap from
  `faq_docs.json` to `kb_chunks.jsonl`, and the release gate. That is a separate change.

## 10. Reproduce

```bash
python -m pip install fastembed==0.7.3
python scripts/retrieval_eval.py heldout   # rebuild the held-out set from the team files
python scripts/retrieval_eval.py pool      # list any (question, passage) pairs still to judge
python scripts/retrieval_eval.py run       # tune, cross-validate, write results/comparison.json
python -m pytest tests/test_retrieval_eval.py
```
