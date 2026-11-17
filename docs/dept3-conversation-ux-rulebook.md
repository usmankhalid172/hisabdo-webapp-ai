# Department 3 Conversation UX & Formatting Rulebook

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-13 · **Branch:** `FahadZubairi_AI`
**Code:** `src/financial_assistant/conversation.py` (new), `service.py`, `grounding/answer.py`
**Evaluation:** `scripts/conversation_ux_eval.py` → [dept3-conversation-transcripts.md](dept3-conversation-transcripts.md)
(8 journeys, 22 turns, **8/8 verified**) and [dept3-adversarial-test-log.md](dept3-adversarial-test-log.md)
(18 attacks, **18/18 held**) · **Tests:** `tests/test_conversation_ux.py` (5)
**Builds on:** [dept3-grounded-rulebook.md](dept3-grounded-rulebook.md) (R1–R12), safety suite v1.1

## 1. Result

| Check | First run (13 Nov) | After fixes |
|---|---|---|
| Multi-turn journeys verified (8 journeys, 22 turns) | 4/8 | **8/8** |
| Adversarial attacks held (18; 7 multi-turn turns) | 16/18 | **18/18** |
| Safety suite v1.1, worst-case "compliant" model, grounded on | cleared | **cleared** (critical 43/43, major 36/36, minor 8/8) |
| Grounded transcripts (12 Nov) | 19/19 | **19/19** |
| Judged evaluation: correct answers / wrong citations | 36 / 3 | **36 / 3** |
| Tests (excluding the separate xictek module and the slow ingestion tests) | 710 passed | **715 passed** |

Problems found by the first run and fixed:

| # | Problem | Fix |
|---|---|---|
| 1 | "I can't log in to my account and my records are gone" showed the demo balance | U4 human-support escalation before routing |
| 2 | "My synced data disappeared after the update" started an entry correction | U4 |
| 3 | "please delete my account" showed the balance again | U4 |
| 4 | After "expenses" → clarifying question, "how expense tracking works" started an expense entry ("How much was it?") | U6 follow-up mapping |
| 5 | The same 3-sentence fallback repeated word for word in consecutive turns | U5 short follow-up forms |
| 6 | The same off-topic boundary message repeated in consecutive turns | U5 |
| 7 | "Does it support recurring expenses?" produced the **currency conflict notice** (shared word "support") | Conflicted passages need ≥ half the question's topic words |
| 8 | A related-topic list answer ran to 967 characters | U2: related-topic answers ≤ 2 sentences, excerpts ≤ 450 characters |

## 2. Response structure by flow

| Flow | Structure | Length | Example |
|---|---|---|---|
| **Transaction** (add, correct, confirm) | One line: what will be saved (amount · category · date), then one yes/no question. After "yes", one line: "Done: …" | ≤ 260 characters | "Please confirm this expense: PKR 2,500, Transport, 13 Nov 2026. Save it? (yes / no)" |
| **Missing detail** | One short question, in the user's language | ≤ 220 | "Kitne paise the?" |
| **Account figures / summary** | One line, label + figures + period + "demo data" while the backend is a mock | ≤ 260 | "Your account (November 2026, demo data): income PKR 62,000, expenses PKR 18,420, net PKR 43,580." |
| **Product help** | The answer first (source text), `[n]` after the fact, blank line, `Sources:` list | ≤ 900 (excerpt ≤ 450) | "Yes. HisabDo is offline-first… [1]" |
| **Related topic only** | "I found this on the related help topic "…":" + ≤ 2 sentences + source | ≤ 900 | |
| **Clarification** | One question offering the options | ≤ 220 | "Do you want to add an expense, see your expense totals, or learn how expense tracking works in HisabDo?" |
| **No documentation** | First time: full fallback with support channels. Later in the same conversation: one-line short form | first ≤ 400, then ≤ 160 | "That one isn't in HisabDo's help pages either. Support at hisabdo.app@gmail.com can help with anything the pages don't cover." |
| **Boundary (off-topic, unsafe)** | One or two sentences: what it can help with. Short form on repeat | ≤ 300 | |
| **Human support (U4)** | Why support is needed, the channel, what to include, never share a password or OTP, response time. Short form on repeat | ≤ 450 | see U4 |

## 3. Rules

| Rule | Rule | Enforced by |
|---|---|---|
| **U1 Context across turns** | Follow-ups keep the conversation's context without repeating it: a correction ("actually it was 2700") updates the pending entry; "and my balance?" answers with the balance only; "what about backup?" / "and if I uninstall the app?" are answered as product questions. The client sends `history`; pending entries live in the per-conversation state store | Dialogue manager, router; checked by `context` in every journey |
| **U2 Concise and direct** | Answer first. No opening restatement, no filler ("Great question", "I'd be happy to", "As an AI", "In response to:", "Here's what I found"). One question at most per reply. Quoted excerpts ≤ 450 characters, cut at a word boundary with "…". Related-topic answers ≤ 2 sentences | `SYSTEM_PROMPT` consistency rules, `MAX_EXCERPT_CHARS`, `RELATED_SENTENCES`; checked by `no_robotic`, `concise`, `one_question` |
| **U3 Tone** | Plain, respectful and calm, with no blame or alarm. Fallbacks say what is missing and what to do next. Language and script follow the user (English, Roman Urdu, Urdu) | `TEMPLATES`, `ESCALATION`, `REPEAT` |
| **U4 Human-support escalation** (new) | Account-level problems need HisabDo's team, not the chatbot. Triggers: cannot log in, locked or hacked account, someone else logged in, lost or disappeared data, delete or close the account, charges or refunds, app crashes, and Roman Urdu equivalents. The reply explains why, gives hisabdo.app@gmail.com and the Contact page, asks for the signup email or phone and a short description, and warns: **never share a password or one-time code, even with support**. It runs after the injection checks and **before** routing, so these messages never get demo figures or an entry flow. Logged as `support_escalation` (no user text) | `conversation.escalation`, `service._guarded_core` |
| **U5 No repeated paragraphs** (new) | A reply without citations (fallback, boundary, escalation) whose long sentences the user already saw in this conversation is replaced by its one-line short form, in the user's language. Disclaimers are said once per conversation | `conversation.dedupe`, `service._guarded_chat` |
| **U6 Clarification follow-up** (new) | The reply to the "expenses" clarifying question is mapped to the option picked: "how / learn / works" → product help, "total / show / kitna" → the month's summary. Anything else continues normally | `conversation.follow_up` |
| U7 Figures | Never invent or estimate figures. Label the period and "demo data" while the backend is a mock. Only the user's own account | Account data route, third-party guard |

## 4. Safety and privacy guardrails (layers, in order)

| Layer | Blocks | Verified by |
|---|---|---|
| Input guard | Prompt injection and instruction override (EN, Roman Urdu, Urdu), prompt extraction (repeat, translate, summarize instructions), secrets and token requests, jailbreak personas (DAN, developer mode), unsafe requests (tax evasion, fraud), toxic text | Suite v1.1 (87 cases) + AX-01–07, AX-15, AX-18 |
| Escalation (U4) | Account-level problems → human support | AX-16, AX-17, J7 |
| Clarification (R1/R10) | Topic-less and expense-only messages | J6 |
| Off-topic question check | Questions outside HisabDo and bookkeeping (poems, weather, code), **including in the middle of a valid conversation** | AX-08 (3 turns), AX-09 |
| Third-party guard | Anyone else's data (relatives, "user 1042", "I am the admin") | AX-13, AX-14 |
| Grounding (R4–R12) | Unsupported facts, citations and links | Grounded transcripts |
| Output guard | Prompt text, tokens, key shapes, env var names, unverified e-mail and phone numbers, CNICs and card numbers, even when the model itself is fooled | Suite v1.1 "compliant" model run |
| Sensitive data the user types | A card number, CNIC or password in a message is **never repeated back** | AX-10–12 (`no_pii_echo`) |
| Logs | `chat_turn` keeps 20 allowlisted fields. No message text, amounts or replies | Telemetry tests |

## 5. Verified multi-turn journeys

| Journey | Turns | Shows |
|---|---|---|
| J1 Expense entry + correction | 3 | Petrol 2,500 → "actually it was 2700" updates the pending entry → "yes" → "Done" |
| J2 Roman Urdu entry, missing amount | 3 | "aaj bijli ka bill diya" → "Kitne paise the?" → 3200 → confirm |
| J3 Summary + follow-ups | 3 | Month summary → "and my balance?" → "thanks" (no figures repeated) |
| J4 Budget → export → WhatsApp | 3 | No budget feature claimed; PDF export; sharing as a related topic |
| J5 Product help, topic switch | 3 | Offline → "what about backup?" (one clarifying question) → uninstall |
| J6 Ambiguous start | 2 | "expenses" → clarifying question → "how expense tracking works" → the expense tracker page |
| J7 Account problem | 2 | Escalation with support channels → second account issue gets the one-line short form |
| J8 Three unanswerable questions | 3 | Full fallback once, then short forms; no currency conflict |

Full text and per-turn checks: [dept3-conversation-transcripts.md](dept3-conversation-transcripts.md).

## 6. Limits

* Replies come from templates and the mock model. Wording quality with a real model is not measured yet (D3-16);
  the same checks run unchanged once a provider is enabled.
* Escalation is pattern-based. An account problem described in unusual words falls through to the normal routes,
  which are still safe (no figures for anyone else, no guesses).
* The backend is still a mock (D3-01), so summaries are labelled "demo data".
