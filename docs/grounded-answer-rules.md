# Grounded Answers: Prompt and Response Handling Rules

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-10-30 · **Branch:** `FahadZubairi_AI`
**Code:** `src/financial_assistant/grounding/` · **Tests:** `tests/test_grounded_answers.py` (27)
**Builds on:** [kb-content-cleaning.md](kb-content-cleaning.md) (the approved KB) and
[retrieval-approach-comparison.md](retrieval-approach-comparison.md) (the measured retrieval configuration)

## 1. Result

The chatbot's knowledge route now answers only from the approved knowledge base, and every reply is one of five kinds:

| Status | When | What the user gets |
|---|---|---|
| `answered` | A passage passes the measured threshold **and** covers the question | The source text, a citation `[n]` after each fact, and a Sources list (page › section: link) |
| `conflict` | A retrieved passage is marked `needs_confirmation` (official sources disagree) | Every version with its source and date, no chosen answer, `needs_review: true` |
| `no_source` | Nothing relevant passes the threshold | "I couldn't find this… so I won't guess" + support contact + how to rephrase |
| `out_of_scope` | The router sent the message outside the knowledge route | What the assistant can help with + support contact |
| `clarify` | The message has no topic, or a one-word topic matching two different sections | One clarifying question |

Measured on the judged question sets (router → hybrid retriever → these rules), in
`data/retrieval_eval/results/grounded_answers_hybrid.json`:

| | Day 1 failed questions (19) | Held-out questions (120) |
|---|---|---|
| Answered with a correct citation | 5 | 28 |
| Safe non-answer (clarification, fallback, or only background cited) | 2 (both router misroutes) | 19 |
| Cited an unrelated source | **0** | **4** (3 of them Urdu script) |
| "Must get nothing" questions correctly refused | 12 | 69 of 69 |

Retrieval alone put 8 unrelated passages into held-out contexts; with these rules 4 unrelated citations reach a user.
Only 1 of the 51 answerable held-out questions got an unnecessary clarifying question.

The feature is **off by default** (`GROUNDED_ANSWERS_ENABLED=false`): the live chatbot keeps its current behaviour until
the release gate has run with it on (section 9).

## 2. How a knowledge question is handled

```
message ─► third-party guard ─► intent router ─┬─ transaction / report / own figures ─► existing routes (unchanged)
                                               ├─ general  ─► R1 clarify? ─► R2 out_of_scope
                                               └─ faq      ─► R1 clarify? ─► retrieve (C10, threshold 0.586, top 2)
                                                                             │
                                                    relevance gate (R4) ◄────┘
                                                             │
                                  none ─► R2 no_source       │ some
                                                             ▼
                                   any passage needs_confirmation? ─► R3 conflict (all versions, flag for review)
                                                             │ no
                                                             ▼
                                   English + real model ─► model drafts with [n] ─► R4 verify ─► R5 sources
                                   mock model, or Urdu / Roman Urdu ─► source text quoted (R7) ─► R5 sources
```

## 3. Response handling rules

| Rule | Rule text | Implemented in |
|---|---|---|
| **R1 Clarify first** | A message with no topic ("how?", "kaise?", "Tell me about it") gets one open question listing the main areas. A one-word topic whose two best passages are different sections ("backup") gets "Do you mean A or B?". Never more than one question; never a guessed answer. A message that names the app ("What is HisabDo?") has a topic. | `GroundedAnswerer.clarify` |
| **R2 No source, no facts** | When nothing passes the measured threshold and the relevance gate, or the router sent the message elsewhere, say so, do not guess, and give a next step: HisabDo support (hisabdo.app@gmail.com, Contact page, 48 hours, all from the KB), rephrasing, or a named feature. Tax, legal and investment questions also get "consult a qualified accountant" (from the Disclaimer). | `fallback`, `TEMPLATES` |
| **R3 Conflicts are shown, not resolved** | A passage marked `needs_confirmation` brings in every passage of its conflict group. The reply gives each version with its source and date, says no single answer can be given, and the response carries `needs_review: true`; a `kb_conflict_escalated` log event (chunk ids only, never user text) lets the owner find it. | `conflict`, `service._grounded_reply` |
| **R4 Cite only what supports** | (a) Relevance gate: a passage is used only if it covers at least a third of the question's topic words, whatever its retrieval score. (b) For a model's draft, every sentence's citation is checked: the cited passage must contain at least half of the sentence's content words; a clearly better retrieved source (+0.2) replaces a weak one; an unsupported sentence is dropped; a draft left with nothing supported becomes R2. | `relevant`, `verify`, `support` |
| **R5 Show sources** | Every reply that uses the KB ends with `Sources:` and one line per cited passage: `[n] Page title › Section: link`. The same data is returned as `citations[]` for the app to render. Only cited passages are listed. | `_with_sources` |
| **R6 Legal pages are quoted** | Privacy Policy, Terms and Disclaimer passages (`usage: reference_only`) are quoted with their section name and link, never paraphrased into advice. | `extractive` |
| **R7 Language** | The frame (intro, question, fallback, conflict notice) is in the user's language and script: English, Roman Urdu or Urdu. The evidence stays the English source text, quoted verbatim, because a translated answer cannot be checked against its source. | `detect_language`, `TEMPLATES` |
| **R8 Neighbouring topic** | When the cited passage answers a different help question (its heading does not contain the user's own topic words), its leading "Yes"/"No" is removed and the reply names the help topic it comes from, so the user can judge it. | `extractive` |
| **R9 One source unless needed** | A second passage is cited only when the first leaves more than half of the question uncovered, and the second covers at least half of it. | `extractive` |

## 4. Prompt rules (real model providers)

The provider's `SYSTEM_PROMPT` (prompts.py) is unchanged. On the knowledge route the model receives
`GROUNDING_RULES` followed by the numbered sources:

```text
Answer ONLY from the numbered sources below.
- After each fact, cite the source that states it as [n]. Cite a source only if it states that fact.
- Do not add facts, steps, button names or numbers that the sources do not contain.
- If the sources do not answer the question, say you could not find it in HisabDo's official help pages and
  suggest contacting HisabDo support at hisabdo.app@gmail.com. Do not guess.
- If two sources disagree, say so, give both with their source numbers, and do not choose one.
- A source marked "legal page" is quoted with its section, never turned into advice.
- Do not list the sources yourself; they are added below your answer.

[1] HisabDo Help Center FAQ › Is HisabDo free to use? (https://hisabdo.app/faq; help page; updated not shown)
Yes. HisabDo is free to download and use from Google Play. Core features including khata management, ...
```

The prompt is a request; R4 is the enforcement. Whatever the model writes is checked before it is returned.

## 5. Examples of correct citations and links

All examples below are real outputs of `POST /api/v1/chatbot` with grounded answers on (hybrid retriever, mock
model), produced by `scripts/grounded_answer_examples.py` (`results/grounded_answer_examples.json`).

**5.1 Direct answer, one source** · *Is HisabDo free to use?* → `answered`

```text
Yes. HisabDo is free to download and use from Google Play. Core features including khata management, customer
accounts, PDF export and backup are available at no cost. [1]

Sources:
[1] HisabDo Help Center FAQ › Is HisabDo free to use?: https://hisabdo.app/faq
```

The response also carries `citations: [{"n": 1, "title": "HisabDo Help Center FAQ › Is HisabDo free to use?",
"url": "https://hisabdo.app/faq", "chunk_id": "off-01-002-is-hisabdo-free-to-use", "last_updated": null}]`.

**5.2 Roman Urdu question, verbatim English evidence (R7)** · *Kya HisabDo iPhone par chalta hai?*

```text
HisabDo ke official page ke mutabiq (English mein):

Currently HisabDo is available on Android only. iOS support may be considered in future development. Follow our
social media channels for updates. [1]

Sources:
[1] HisabDo Help Center FAQ › Is HisabDo available on iOS (iPhone)?: https://hisabdo.app/faq
```

**5.3 Legal page quoted with its section (R6)** · *Does HisabDo use cookies for advertising?*

```text
The Privacy Policy says, in "7. Advertising & Cookies": "Our website may use third-party advertising technology,
including Google AdSense, to display ads. These services may use cookies or similar technologies to personalize
advertisements, measure ad performance, and provide relevant content based on your browsing activity. Depending on
your location and applicable law, you may be able to control or opt out of certain personalized advertising." [1]

Sources:
[1] Privacy Policy › 7. Advertising & Cookies: https://hisabdo.app/privacy-policy
```

**5.4 Neighbouring help topic named, its "Yes" dropped (R8)** · *Can I use HisabDo on two phones at once?*

```text
I found this on the related help topic "Can I restore a backup?": If you have created a backup, you can restore it
to any Android device running HisabDo. This is useful when changing phones or recovering from a device problem. [1]

Sources:
[1] HisabDo Help Center FAQ › Can I restore a backup?: https://hisabdo.app/faq
```

Without R8 this reply began "Yes. If you have created a backup…", which reads as "yes, two phones at once": the
FAQ's "Yes" answered its own question, not the user's.

**5.5 A model's draft checked (R4)**

| Model draft | Returned |
|---|---|
| `HisabDo is free to download and use from Google Play. [2] Tap the Premium button in Settings to unlock unlimited exports. [1]` | `HisabDo is free to download and use from Google Play. [1]` + Sources: HisabDo Help Center FAQ › Is HisabDo free to use? — the invented "Premium button" sentence is dropped and the citation moved to the source that states the fact |
| `Yes, HisabDo Gold costs Rs. 499 per month and includes a desktop version.` | The R2 fallback (status `no_source`): nothing in the draft is supported, so none of it is shown |

## 6. Examples of fallback responses when information is unavailable

**6.1 No source** · *Does HisabDo have a desktop app for Mac?* → `no_source`, no citations

```text
I couldn't find this in HisabDo's official help pages, so I won't guess. You can ask HisabDo support at
hisabdo.app@gmail.com or through the Contact page (https://hisabdo.app/contact); they aim to reply within 48 hours.
You can also rephrase the question or ask about a specific feature, such as PDF reports, backup or customer udhar.
```

In lexical mode the retriever returned the Privacy Policy "Contact Us" section for this question with a passing
score; the relevance gate (R4a) removed it, so no unrelated source was cited.

**6.2 No source, advice topic** · *Can HisabDo file my income tax return?* → `no_source`

The same reply, ending: `For advice specific to your business, please consult a qualified accountant.`

**6.3 Outside the knowledge route** · *Write a short poem about the sea.* → `out_of_scope`

```text
I can help with HisabDo and with bookkeeping for your business, but I don't have reliable information on that. Try
asking about a HisabDo feature, such as PDF reports, backup or customer udhar, or contact HisabDo support at
hisabdo.app@gmail.com.
```

The same fallbacks exist in Roman Urdu and Urdu (`TEMPLATES` in `answer.py`).

## 7. Examples of clarifying ambiguous questions

| Message | Reply (status `clarify`) |
|---|---|
| *how?* · *kaise?* · *Tell me about it* | Which part of HisabDo do you need help with? For example: customers and udhar, expenses, PDF reports, backup, or using the app without internet. |
| *backup* | Do you mean "Can I restore a backup" or "Can I backup my data"? |
| *کیسے؟* | آپ کو حساب دو کے کس حصے میں مدد چاہیے؟ مثلاً: گاہک اور ادھار، خرچہ، پی ڈی ایف رپورٹس، بیک اپ، یا انٹرنیٹ کے بغیر استعمال۔ |

The options in "Do you mean A or B?" are the headings of the two best passages, so the question offers only things
the KB can answer. Specific questions are never held up: "Can I export PDF reports?", "Does HisabDo work without the
internet?" and "How do I contact HisabDo support?" are answered directly (tested).

Ambiguity about **the user's own data** ("show my report" without a period) is the dialogue manager's job and is
unchanged: it asks "For which period?".

## 8. Guidelines for identifying and handling conflicting sources

**Identify (at cleaning time, not at answer time).** The KB cleaner (`clean_knowledge_sources.py`) compares facts
across approved sources and marks every chunk of a disagreement `status: needs_confirmation`, with a note naming each
version, its source and its date. Today one conflict is marked: **supported currencies** (audit C-06): the FAQ and
About page (undated) list PKR, USD and INR; Google Play (2026-10-13) adds AED. Finding conflicts once, from the whole
KB, is more reliable than guessing them from two passages at answer time.

**Handle (at answer time).**

1. Any retrieved passage marked `needs_confirmation` → bring in every chunk of its conflict group, even ones the
   retriever did not return (so the user sees every version).
2. Show each version with its source, section and date ("no date shown" when the page has none). Do not pick the
   newest: a newer date is evidence, not proof, and the product owner decides.
3. Say plainly that the sources disagree and that it has been flagged for review.
4. Return `needs_review: true` and log `kb_conflict_escalated` with the chunk ids (no user text, no personal data).

Real output · *Which currencies does HisabDo support?* (and the Roman Urdu *Kya HisabDo AED currency support karta
hai?*, which gets the same versions with a Roman Urdu notice):

```text
HisabDo's official sources don't agree on this yet, so I can't give you one answer. I've flagged it for review.
[1] HisabDo Help Center FAQ › Which currencies does HisabDo support? (no date shown): HisabDo supports Pakistani
Rupee (PKR), US Dollar (USD) and Indian Rupee (INR). You can select your preferred currency in the app settings.
[2] Why We Built HisabDo › Works the Way You Do Business (no date shown): In Your Currency PKR, USD and INR are
supported, so the app fits businesses operating in Pakistan, India and beyond.
[3] HisabDo: Khata & Expense App › Multi-Currency Support (2026-10-13): Manage financial records using: PKR INR AED USD

Sources:
[1] HisabDo Help Center FAQ › Which currencies does HisabDo support?: https://hisabdo.app/faq
[2] Why We Built HisabDo › Works the Way You Do Business: https://hisabdo.app/about-app
[3] HisabDo: Khata & Expense App › Multi-Currency Support: https://play.google.com/store/apps/details?id=com.usman.hisabdo
```

**Resolve (people, not the chatbot).**

| Step | Who | Action |
|---|---|---|
| 1 | Product owner | Confirm the true fact (for C-06: is AED supported?) |
| 2 | Website owner | Correct the wrong page(s) |
| 3 | KB owner | Re-run `python scripts/clean_knowledge_sources.py --fetch`; the conflict mark disappears when the sources agree |
| 4 | Anyone | Until then, the chatbot keeps showing both versions; it never resolves a conflict on its own |

A model that receives two disagreeing passages without the mark is told by `GROUNDING_RULES` to present both and not
choose one; R4 still checks each sentence against its cited source.

## 9. Switching it on

```bash
GROUNDED_ANSWERS_ENABLED=true
KB_RETRIEVER_MODE=auto        # hybrid if fastembed is installed, else lexical
```

* **Hybrid** (C10, needs `fastembed`, ~67 MB local model, no API key): the measured configuration; use in production.
* **Lexical** (C15, no extra dependency): BM25 on the rewritten query, threshold 4.94, top 2, margin 2.0. Measured
  weaker: 25 correct answers and 9 unrelated citations on the held-out set (`grounded_answers_lexical.json`).
* New, optional response fields: `answer_status`, `citations[]`, `needs_review`. Existing fields and routes are
  unchanged; with the flag off the reply is the previous one and the new fields are `null` / `[]` / `false` (tested).
* Release gate (`scripts/release_acceptance.py`), run 2026-10-30 with the flag on and the hybrid retriever:
  **critical 25/25, major 6/6**, minor 0/1. The minor miss, M-03 "Udhar aur payment mein kya farq hai?", also fails
  with the flag off: the router sends it to `general`. With the flag off it reached the general model with no source
  (`llm_general`); with it on it gets the R2 fallback (`kb_fallback`). The fix belongs in the router.
* Before enabling in production: install `fastembed` (see `src/financial_assistant/requirements.txt`) and re-run the
  gate on the deployed build.

## 10. Known limits (measured, not hidden)

| Example | What happens | Cause / owner |
|---|---|---|
| *Can I connect HisabDo to my bank account?* | Answers from "What happens when I sign in?", labelled as a related topic (R8) | "account" and "connected" pass the relevance gate; the KB says nothing about banks. Next: weight the question's rarest word |
| *Does HisabDo have a web version?* | Answers with the required Android version, not labelled | "web" occurs nowhere in the KB, so R8 cannot see the mismatch |
| 3 Urdu-script held-out questions | Cite an unrelated passage | Glossary maps the app's Urdu name "حساب دو" to "ledger account" and "محفوظ کریں" (save) to "safe" |
| *Should I register my shop for sales tax?* | Router sends it to the report flow ("For which period?") | Router: "sales" read as an own-figures request (Saba Talat) |
| *How long does HisabDo keep my data after I delete my account?* | Router sends it to account data | Router: "my data … account" (Saba Talat) |

These questions were found while writing the examples. The rules were not tuned on the held-out set after its first
measurement; the fixes above are listed for the next change, to be re-measured on a fresh question set.

## 11. Files

| File | Purpose |
|---|---|
| `src/financial_assistant/grounding/retrieval.py` | Normaliser, rewrite, BM25 (shared with the evaluation), `KbRetriever` with the measured parameters |
| `src/financial_assistant/grounding/answer.py` | R1–R9, templates in English, Roman Urdu and Urdu |
| `src/financial_assistant/prompts.py` | `GROUNDING_RULES` |
| `src/financial_assistant/service.py`, `src/schemas.py`, `src/config.py` | Wiring, response fields, settings |
| `scripts/grounded_answer_eval.py` | Measures the rules on the judged sets (`results/grounded_answers_*.json`) |
| `scripts/grounded_answer_examples.py` | Produces the examples in this document |
| `tests/test_grounded_answers.py` | 27 tests |
