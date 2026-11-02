# Portfolio & Case Studies — E2E Pipeline Integration Submission

**Student:** Muhammad Daniyal  
**Assignment:** 3 — E2E Pipeline Integration — Portfolio & Case Studies  
**Target:** XICTEK Systems AI Assistant / HisabDo

## Package contents

- `report/` — detailed technical report (DOCX).
- `logs/conversation_flow_logs.jsonl` — seven user-supplied live production conversation observations. No extra production conversations have been invented.
- `benchmarks/` — the ten user-supplied production timings, CSV and JSON statistics.
- `citations/` — source relevance and claim-support audit for T01–T07.
- `tests/` — standalone deterministic Python validation helpers and pytest tests.
- `results/` — test execution output and validation summary.
- `evidence/repository_audit.json` — verified repository paths, code findings and deployment limitations.

## Run offline tests

Python 3.10+ and pytest are required. From this directory:

```bash
python -m pytest -q tests/test_portfolio_e2e_pipeline.py
```

The tests are deterministic and offline. They validate the supplied evidence baseline, URL syntax/relevance rules, context-preservation proposal, fallback behavior and benchmark arithmetic. They do **not** call the deployed chatbot or prove the live application uses the uploaded repository.

## Evidence categories

1. **Live production observations (user supplied):** seven conversations, actual responses and links; captured `POST /api/assistant/chat` returning HTTP 200; ten Chrome DevTools timings; and a separate earlier ~1.9-minute observation.
2. **Repository code findings (inspected from ZIP):** knowledge records, retrieval and history handling, TF-IDF implementation, stale embedding metadata/config, API routes, provider selection, widget integration and fallbacks.
3. **Offline automated tests (executed here):** 19 deterministic pytest tests, all passing.

## Important findings

- Portfolio records `faq-33`–`faq-37` explicitly document HisabDo and the stack **Flutter, Supabase, PostgreSQL**.
- `service.py` embeds only the latest message (`embed_query(message)`); history is passed separately to the LLM. Pronoun-based follow-ups can therefore retrieve poorly.
- `embeddings.py` uses `TfidfVectorizer`, while `config.py` and `data/index/metadata.json` still identify multilingual MiniLM with a configured 384 dimensions. The persisted matrix is actually 976 × 2,109 and a TF-IDF pickle is present.
- Repository route/widget use `/api/v1/xictek/chat`; the live browser evidence supplied by the user shows `/api/assistant/chat`. The ZIP contains no verified mapping between them.
- The default provider is Mock unless Groq is configured. Local mock execution cannot reproduce production LLM behavior.
- The widget's client-side `X-Internal-Token` exposure is explicitly identified as unsafe in its source comments.
- Nine of ten production total durations were below one second. Request 4 was 29,430 ms total but only 421.19 ms in the recorded waiting phase.

## Limitations

- No production API request was made from this environment.
- No live URL reachability checks were performed; HTTPS syntax and path relevance are not reachability proof.
- The full repository pytest collection was blocked because `slowapi==0.1.9` was declared but absent. Installing it was attempted but package-index network access was unavailable.
- The 19 passing tests are offline fixture/rule tests, not production E2E tests.
- Ten latency observations are too few for stable tail-percentile estimates.
