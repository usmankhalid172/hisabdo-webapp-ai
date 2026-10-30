# Blog & News — E2E Pipeline Integration

This package is a configurable QA harness for the Blog & News chatbot. It is adapted from the supplied `blog_e2e.py` and reuses the evaluation/testing approach in the teammate's About Us/Core Services package. It does **not** contain the actual chatbot, retriever, LLM, or proprietary article corpus.

## 1. Setup

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set the values. Load `.env` in your shell or export the variables; this script intentionally does not require python-dotenv.

Required configuration:
- `QA_BASE_URL`: live chatbot base URL.
- `QA_CHAT_PATH`: actual chat endpoint, e.g. `/chat`.
- `QA_DOMAIN`: exact approved hostname (e.g. `www.xicteksystems.com`).
- `QA_ALLOWED_PREFIXES`: comma-separated approved paths. Keep `/blog/` unless News uses a separately verified path.
- `QA_RESPONSE_TEXT_FIELD`: preferred answer field, commonly `reply` or `response`.
- `QA_HISTORY_MODE`: `payload` sends history; `server` relies on conversation_id server-side.

## 2. Run

```bash
python blog_e2e.py
```

Outputs:
- `blog_pipeline_results.csv` — one row per tested turn.
- `logs/blog_multiturn_log.jsonl` — request, history, and raw API response.
- `citation_report.md` — run summary and limitations.

## 3. Before claiming completion

1. Replace generic questions in `CONVERSATIONS` with questions supported by your real corpus.
2. Add real, verified conflict pairs to `CONFLICTS` (see `data/conflict_cases_template.json`). An empty conflict list means conflict handling has not been tested.
3. Confirm the API request/response schema. The runner supports `reply`, `response`, or `answer`, and `sources` or `citations` with URL fields.
4. Review every citation with `tests/manual_review_checklist.md`.
5. Attach the CSV, JSONL log, and reviewed report to the task submission.

## Important limitations

- URL checks verify syntax, exact host, path allowlist, and basic HTTP reachability; they do not prove source relevance.
- Lexical matching is only a screening aid. The runner marks citation accuracy as `REVIEW`, not `PASS`, because word overlap cannot prove semantic support.
- Conflict cases are intentionally manual-review rows until real source pairs are provided and reviewed.
- A successful local run is not evidence that the live backend is correct unless it uses the actual deployed endpoint and corpus.

## Reused teammate material

The teammate's package contributed the general concepts of grounding, allowlisting, benchmark evaluation, and multi-turn drift testing. Its About Us-specific prompt, URL, facts, and test expectations were not copied as Blog & News truth. The Blog & News pipeline must use its own retrieved article context and approved URL paths.
