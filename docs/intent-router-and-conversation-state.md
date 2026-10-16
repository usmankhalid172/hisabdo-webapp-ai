# Intent Recognition & Conversation State — HisabDo chatbot (`src/financial_assistant/dialogue/`)

Owner: Saba Talat · Task: Intent recognition & conversation state (intent router + multi-turn handling)

The chatbot (`POST /api/v1/chatbot`) works out **what the user wants** (the intent) and handles **multi-turn conversations**. When information is missing it asks follow-up questions, remembers the answers between messages, and confirms before anything is final.

## Intents and routes

| Intent | Example messages | Route | Answered by |
|---|---|---|---|
| `add_expense` | "Aaj 500 ka petrol dala", "I paid 1200 for electricity", "آج 500 کا پٹرول خریدا" | transaction | step-by-step flow (templates) |
| `add_income` | "Ali se 2000 mile", "Aaj 3000 ki sale hui", "I received 5000" | transaction | step-by-step flow |
| `correct_transaction` | "last wali entry 600 kar do", "pichli entry ki category Rent kar do", "delete the last entry" | transaction | step-by-step flow |
| `categorize` | "petrol kis category mein aayega?" (or on a pending/last entry) | transaction | suggestion or category change |
| `report` | "is mahine ki report dikhao", "How much did I spend last month?" | **account_data (private)** | `BackendClient` only (current month; other months: "not available yet") |
| `account_query` (returned as `own_financial_data`) | "mera balance kitna hai?", "What is my balance?" | **account_data (private)** | `BackendClient` only |
| `faq` | "HisabDo kya hai?", "How do I categorize an expense?" | knowledge | existing FAQ RAG + LLM (unchanged) |
| `greeting` / `general` | "salam", "give me tips to grow sales" | general | existing small-talk fast path / LLM (unchanged) |
| `confirm` / `deny` | "haan", "ji", "yes" / "nahi", "cancel", "rehne do" | (inside a flow) | |

**Private questions are separated from FAQs.**
- The user's own numbers come only from `src/integration/backend_client.py`. They never come from RAG or the LLM.
- They are shown with fixed templates. On the private route neither RAG nor the LLM is called.
- The current backend client is the mock, so the answers say "demo data".
- The third-party guard ("my brother's balance") still runs first and refuses as before.

## Slots (the information each flow needs)

| Flow | Required (asked for if missing) | Filled automatically | Optional |
|---|---|---|---|
| Expense / income | direction (spent or received?), amount, currency, category | date = today, Asia/Karachi (shown in the summary so it can be changed); currency = the user's account currency from `BackendClient` | counterparty ("Ali ko"), note |
| Correction | what to change: amount / category / date, or delete | target = the last entry confirmed in this chat | |
| Report | period (this month, last month, "September"…) | report type from words (kharcha → expenses); account if only one | |
| Balance | account (only asked if the user has several) | | |

**Rules:**
- The flow asks **one short question at a time**.
- It **never guesses an amount**. If there is no clear amount, or there are two different ones, it asks.
- It **never assumes a currency**. If the message doesn't say one, it uses the user's business-profile currency, otherwise it asks.

## A conversation, step by step

```
User: Ali ko 500 diye
Bot:  Yeh kharcha kis cheez ka tha? Jaise: Utilities, Transport, Groceries, ...        status: collecting (category)
User: sabzi aur doodh
Bot:  Yeh kharcha confirm karein: PKR 500, Groceries, Ali, 14 Oct 2026. Save karun?   status: awaiting_confirmation
User: nahi 700 tha
Bot:  Yeh kharcha confirm karein: PKR 700, Groceries, Ali, 14 Oct 2026. Save karun?
User: HisabDo kya hai?                                   (side question: answered from the KB, entry kept)
Bot:  <answer> … Aap ki adhoori entry abhi baqi hai: Yeh kharcha confirm karein: …
User: ji
Bot:  Ho gaya: PKR 700, …                                status: completed, action: create_expense
User: last wali entry 600 kar do
Bot:  Pichli entry (PKR 700, …) ko yeh kar dun: PKR 600, …? (haan / nahi)
User: haan
Bot:  Ho gaya. Tabdeeli app ko lagane ke liye bhej di gayi hai …   action: update_transaction
```

**Other behaviour:**
- A new entry with its own amount replaces an unfinished one, and the bot says so.
- "nahi" / "cancel" stops the flow, and nothing is saved.
- An unfinished flow is forgotten after **30 minutes**, or after **6** unclear replies.

## What "save" means here
This AI service **does not write to the database**: the tables and write APIs belong to the backend team. After the user confirms, the response contains an `action`:

```json
{"action_id": "…", "type": "create_expense", "status": "confirmed", "requires_client_execution": true,
 "payload": {"amount": "700.00", "currency": "PKR", "category": "Groceries", "date": "2026-10-14", "counterparty": "Ali"}}
```

The backend saves it through its own authenticated API. Corrections return `update_transaction` / `delete_transaction` with `target_action_id`.

## API response additions (`POST /api/v1/chatbot`, optional fields — backwards compatible)
- `dialogue` contains:
  - `status`: collecting | awaiting_confirmation | completed | cancelled | none
  - `route`, `awaiting` and `missing_slots`
  - `collected`: the slots understood so far
- `action` is set only after the user confirms.
- `source` is `"dialogue"` for transaction templates and `"backend_financial_api"` for private figures. Other sources are unchanged.
- `intent`: the router's intent name (`add_expense`, `add_income`, `correct_transaction`, `categorize`, `report`, `own_financial_data`, …).

## Conversation state
- The backend sends plain-text `history` with each request, but slot filling needs structured state.
- That state is kept in `dialogue/state_store.py`, keyed by **(user_id, conversation_id)**. One user can never load another user's state.
- It holds:
  - the active intent, the slots, what is being waited for and the reply language
  - the IDs of the last 5 confirmed entries, so "change the last entry" works
- It holds no message text.
- **In-memory**, so it is fine for one process. Several instances or restarts need shared storage (Redis / backend DB): a team decision.
- Logs (`hisabdo.ai.dialogue` / `dialogue_turn`) record the intent, route, status, missing slot **names** and action type. They never record amounts, categories or names.

## Configuration
| Variable | Default | Meaning |
|---|---|---|
| `DIALOGUE_ENABLED` | `true` | `false` = previous single-turn flow only |

## Measured
- Intent recognition, `python scripts/evaluate_intent_router.py`:
  - **60/60** on the set used while writing the rules.
  - **30/33 (91%)** on a held-out set written afterwards and not used for tuning.
  - **0** private questions sent to a non-private route.
- Known misses on the held-out set:
  - "got 15000 for the installation job" → expense instead of income. The confirmation step shows "kharcha", so the user can say no.
  - "galti ho gayi, 450 nahi 540 tha" → general.
  - "Give me 3 ideas to reduce costs" → treated as an amount of 3, so the bot asks expense or income. Safe, but not ideal.

## Proposed, needs a decision
- **Categories:** expense categories are the team's existing list in `expense_categorization/rules.py`, with Roman Urdu/Urdu words added. **Income categories are a proposal** (Sales, Services, Customer Payment Received, Salary / Wages Received, Other Income).
- **Reports:** reports for other months need a period parameter in the backend financial data contract.
- **Shared state storage:** needed for multi-instance deployment.
- **Rule-based recognizer.** It is predictable, free and testable. An AI-model recognizer can be added behind the same `IntentRecognizer` interface and compared on the same eval sets.
- **Saving actions.** The backend team needs to accept the `action` contract (or propose another) to actually save entries.

## Tests
- Run from the repo root: `pytest tests/test_dialogue_intents.py tests/test_dialogue_flows.py tests/test_dialogue_chatbot.py -v`.
  - 169 new tests: labelled intent set, slots, 33 flow tests, 13 HTTP/route/privacy tests.
- Full suite: `pytest tests` → 480 passed (on `main` before this change: 311 passed). The same 1 failure exists on `main` before this change (`test_index_status_reports_unbuilt_index_by_default`, XICTEK), so it is not caused by this work.
- **Mutation check:** 10 controls were broken on purpose, and the tests failed every time:
  - confirmation step, per-user state, private route, third-party guard order
  - other-month estimate, demo labelling, amounts in logs, reminder
  - concept-vs-private questions, team categories
