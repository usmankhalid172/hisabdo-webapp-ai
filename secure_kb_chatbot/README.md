# Business-Aware Chatbot + Conversation Management

> **About this folder.** A self-contained prototype by Fahad Zubairi. It is a separate FastAPI app
> with its own SQLite database and seed data (all flagged as demo), and it does not change any other
> code in this repository. It covers:
>
> - **Secure financial data:** login checks, no cross-customer access, demo vs actual labelling,
>   and reporting periods in Pakistan time.
> - **Semantic knowledge base:** embeddings instead of keyword matching, a relevance threshold,
>   source attribution, a safe fallback, and a versioned KB of verified entries.
>
> **Run the tests from inside this folder.** Its tests are skipped when pytest runs from the
> repository root, because they need this folder's own settings:
>
> ```bash
> cd secure_kb_chatbot
> pip install -r requirements.txt
> pytest
> ```
>
> All 259 tests run offline, without API keys. Every step is explained in
> [`docs/IMPLEMENTATION_GUIDE.md`](docs/IMPLEMENTATION_GUIDE.md). That guide was written for applying
> the changes to the original chatbot, so its `reference/` folder corresponds to this folder.
>
> **Knowledge base:** version 1.1.0 has 11 entries verified against official HisabDo sources
> (hisabdo.app and Google Play), each with its source link. KB-006 (currencies) stays a draft because
> the sources disagree. Product-team sign-off is still recommended.
>
> **Not tested yet:** real Supabase logins and live Gemini embeddings. The full picture is in
> [`../docs/fahad-zubairi-final-documentation.md`](../docs/fahad-zubairi-final-documentation.md).

Answers questions like **"How much does Ahmed owe?"** from the signed-in user's own business
data (customers, receivables, payables, tasks, notes) instead of giving generic replies, and won't
make up anything that isn't in that data.

## How a question is answered

```
POST /api/chat "How much does Ahmed owe?"
  1. Fetch    Repository (SQLite) loads this user's business data, scoped by business_id
  2. Select   ContextBuilder picks the relevant records: Ahmed Hassan, his invoices, related task/note
  3. Inject   system prompt = [grounding rules (cached)] + [<business_context> from the DB]
  4. Answer   Gemini (or Claude) returns {answer, citations, grounding, missing_information}
  5. Verify   citations must be records in the context; money figures must appear in the data
```

What the model actually sees for that question (abridged; `GET /api/context?q=...` shows the full text):

```xml
<customer id="C-001" name="Ahmed Hassan" company="Hassan General Store"
          outstanding_balance="85000.00" overdue_balance="40000.00" currency="PKR" .../>
<receivable id="R-001" invoice="INV-1041" amount="40000.00" outstanding="40000.00" due="2026-09-19" state="overdue">...
<receivable id="R-002" invoice="INV-1077" amount="65000.00" paid="20000.00" outstanding="45000.00" state="partially_paid">...
<note id="N-001">Ahmed promised to clear INV-1041 by 10 October...</note>
```

The answer looks like: *"Ahmed Hassan owes PKR 85,000.00 [C-001], of which PKR 40,000.00 (INV-1041)
is overdue [R-001]..."*

## AI team scope

| Item | Where |
|---|---|
| Business context model | `chatbot/models.py` (User, Business, Customer, Task, Note, Receivable, Payable) |
| User/business, customer, task, notes context | `chatbot/context_builder.py`. User, business, policies, team and summary totals are always included. Customers, receivables, payables, tasks and notes are selected per question. |
| Context-aware prompting | `chatbot/prompts.py`: grounding rules plus the context injected into the system prompt |
| AI response generation using business data | `chatbot/llm.py` (Gemini by default, Claude optional), `chatbot/service.py` (turn handling), `chatbot/grounding.py` (verification) |

How the context is selected:
- **Customer by name, company or ID.** "Ahmed", "Qureshi Mart" and "C-003" all work. If several customers share a name, all of them are loaded and the model asks which one you meant.
- **Who owes whom.** "Who owes us" loads open receivables. "What do we owe" or a vendor name loads payables.
- **Tasks.** "Overdue", "my tasks" and "this week" filter the task list.
- **Follow-ups.** A follow-up like "any tasks for him?" keeps the customer from the previous turn.
- **Totals.** Balances and totals are precomputed, so the model quotes numbers rather than calculating them.
- **Coverage.** `<retrieval_scope>` tells the model what wasn't loaded, so it can say "not in the records I was shown" instead of "doesn't exist".

## Conversation management

Conversations are stored in the database, so history survives restarts. The logic is in `chatbot/conversations.py`.

```
create ──► ACTIVE ──archive──► ARCHIVED
  (POST /conversations,  ▲  │ ◄─unarchive──  │
   or first /api/chat)   │  └────delete──────┴──► DELETED ──purge job──► gone
                    messages only here          (soft: 404 everywhere)    (hard delete)
```

| Feature | How it works |
|---|---|
| Create / start | `POST /api/conversations` creates an empty conversation. Alternatively, `POST /api/chat` without a `conversation_id` starts one with the first question. |
| Conversation IDs | `conv_` followed by 32 random hex characters. They're never sequential, so they can't be guessed. |
| Titles | The first question becomes the title (first line, cut at a word boundary, at most 60 characters). A title the user sets is never overwritten. |
| Rename | `PATCH {"title": "..."}` works in both the active and archived states. |
| Archive / unarchive | `PATCH {"status": "archived" \| "active"}`. An archived conversation is read-only, and sending to it returns **409**. |
| Delete | `DELETE` is a soft delete. The conversation then returns 404 everywhere and disappears from lists. `purge_deleted_conversations.py --days 30` permanently removes it later. |
| Privacy | A conversation is visible only to the user who created it, not to colleagues or other businesses. Their requests get 404, the same as for an ID that doesn't exist. |
| History | The last 12 question/answer pairs are replayed to the model. Turns that fail or are refused aren't stored. |
| Race safety | Turns in the same conversation are processed one at a time. If a conversation is archived while the model is still answering, the late answer isn't saved. |

Endpoints:
- `POST /api/conversations`
- `GET /api/conversations?status=active|archived&limit=&offset=`
- `GET`, `PATCH`, `DELETE` `/api/conversations/{id}`
- `POST /api/conversations/{id}/messages`

## SQA scope: `pytest` (161 tests)

| Area | File |
|---|---|
| Customers, Tasks, Notes, CRUD operations | `tests/test_crud.py` |
| Validation | `tests/test_validation.py` |
| Empty states, error states | `tests/test_states.py` |
| Data isolation | `tests/test_data_isolation.py` |
| Context model, prompting, grounding | `tests/test_context_and_chat.py` |
| Conversation lifecycle (create, IDs, rename, archive, delete, purge, privacy, history) | `tests/test_conversations.py` |
| Gemini client (request mapping, safety blocks, quota and key errors) | `tests/test_gemini_client.py` |

The tests use a fake AI client, so they run offline and don't need an API key.

API contract:

| Code | Meaning |
|---|---|
| 200, 201, 204 | Success |
| 401 | Missing or unknown `X-User-Id` |
| 404 | Record not found. Records belonging to another business also return 404, with exactly the same response. |
| 409 | Deleting a customer who still has invoices, or sending a message to an archived conversation |
| 422 | Validation error, including links to another business's records |
| 503 | AI or database unavailable. CRUD keeps working when the AI is down. |

Endpoints:
- `GET`, `POST` `/api/{customers|tasks|notes|receivables|payables}`
- `GET`, `PATCH`, `DELETE` `/api/{kind}/{id}`
- `POST /api/chat`
- the conversation endpoints listed above
- `GET /api/context?q=`
- `GET /api/me`

Seed data for testing:

| User | Business | Data |
|---|---|---|
| `U-001`, `U-002`, `U-003` | Al-Madina Traders (B-001) | Full data set |
| `U-101` | GreenLeaf (B-002) | Has its *own* "Ahmed" (Ahmed Malik), for isolation tests |
| `U-201` | Fresh Start Bakery (B-003) | No records, for empty-state tests |

Note N-004 contains a planted prompt-injection line, for security testing.

## Run

```bash
pip install -r requirements.txt
```

```bash
pytest
```

### Gemini API key

Get a free key at https://aistudio.google.com/apikey.

**Never paste the key into code, chat or a file you commit.** Set it as an environment variable instead.

For the current PowerShell window only:

```powershell
$env:GEMINI_API_KEY = "your-key-here"
```

To save it for all future terminals, run this, then open a new terminal:

```powershell
setx GEMINI_API_KEY "your-key-here"
```

### Start the server

```powershell
$env:CHATBOT_TODAY = "2026-10-07"; uvicorn app:default_app --factory --reload
```

- Open http://localhost:8000 for the chat UI (with a conversation sidebar), or http://localhost:8000/docs to try every endpoint.
- If the key is missing or rejected, or the free-tier quota runs out, chat returns 503 with a clear message. The rest of the app keeps working.
- The database is `data/app.db` (override with `CHATBOT_DB`) and is seeded from `data/seed.json` on first run.
- `CHATBOT_TODAY` fixes "today" so the seed data's overdue states stay stable. Leave it unset in real use.

Settings:

| Variable | Default | Purpose |
|---|---|---|
| `CHATBOT_PROVIDER` | `gemini` | Set to `claude` to use Anthropic instead (needs `ANTHROPIC_API_KEY`) |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Any Gemini model your key can use |
| `CHATBOT_MODEL` | `claude-opus-5-5` | Model used when the provider is Claude |
| `CHATBOT_EFFORT` | `medium` | Effort setting used when the provider is Claude |

## Before production

- **Identity.** Take the user from your auth session, not the `X-User-Id` header. Remove `/api/demo-users`.
- **Database.** To use your real database, implement `Repository`'s methods (`get_user`, `get_business`, `list`, `get`, `create`, `update`, `delete`) against it. Keep the `business_id` filter in every query.
- **Retention.** Schedule `purge_deleted_conversations.py` to run daily.
- **Multiple server processes.** The per-conversation lock only works within one process. If you run several workers, add a row lock or version column to the database.
- **Free-tier data use.** Google may use free-tier prompts to improve its products. That data includes customer names and balances, so use a paid key for real customer data.
