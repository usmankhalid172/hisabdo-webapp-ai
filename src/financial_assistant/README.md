# Financial Assistant / Chatbot

Use this folder for code related to:

- AI Financial Assistant
- Chatbot processing
- NLP/LLM logic
- RAG / retrieval
- Prompt handling
- Response validation
- Financial question answering

Keep implementation modular. Add module-specific notes to this README when the design is finalized.

## Intent router + multi-turn conversation state (`dialogue/`)

`service.handle_chat` now runs in this order:

1. **Third-party guard** (unchanged). Questions about someone else's data are refused before anything else runs.
2. **Intent router** (`dialogue/manager.py`). It works out what the user wants: add expense, add income, categorize, correct/delete an entry, report, balance, product FAQ or general. It works in English, Roman Urdu and Urdu.
   - **Transaction flows** ask for missing details (amount, category, currency, expense-or-income) one question at a time and remember them between messages. They then show a summary and ask for confirmation. Only after "haan / yes" is a confirmed `action` returned (`create_expense`, `create_income`, `update_transaction`, `delete_transaction`). The backend saves it through its own authenticated API; this service never writes to the database.
   - **Private figures** (balance, this month's report) come only from `BackendClient`. They are shown with fixed templates, never via RAG or the LLM. The mock backend is labelled "demo data". Other months are answered with "not available yet" instead of an estimate.
3. **Everything else** (FAQ, small talk, general) uses the original single-turn flow: small-talk fast path → RAG → LLM. If an entry is still unfinished, a reminder is added to the reply.

The state is kept per `(user_id, conversation_id)` in `dialogue/state_store.py`. It is in memory for one process and needs shared storage (Redis/DB) for several instances. It contains no message text. Expense categories are the team's existing ones from `expense_categorization/rules.py`, with Roman Urdu/Urdu words added. The income categories are a proposal.

Full write-up: `docs/intent-router-and-conversation-state.md`. Tests: `tests/test_dialogue_*.py`. Accuracy: `python scripts/evaluate_intent_router.py`.
