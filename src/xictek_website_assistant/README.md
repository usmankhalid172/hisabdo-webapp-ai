# XICTEK Website Assistant

AI chat assistant for **XICTEK Systems' own public website**
(xicteksystems.com) — answers visitor questions about the company,
its services, technologies, portfolio, its HisabDo product, careers,
and blog content.

Deliberately separate from [`src/financial_assistant`](../financial_assistant)
(the HisabDo *product* chatbot): different owner content, different
knowledge base, different audience (public website visitors vs.
HisabDo app users). Kept as its own top-level package so it can be
lifted out wholesale once the real xicteksystems.com integration is
scoped with the team lead.

**Status:** backend-only, demoed via Swagger inside this repo (per the
team lead's instruction). The real xicteksystems.com widget
integration — dropping `widget/` into the live Next.js site — is
deferred until repo/hosting access is sorted; see "Current scope &
what's deferred" below.

---

## Architecture

```
Visitor message
      │
      ▼
┌─────────────────────────┐
│ 1. Guardrails (deterministic, no LLM call)          guardrails.py │
│    - length cap                                                    │
│    - prompt-injection / system-prompt-extraction heuristics        │
│    - secret/credential probe heuristics                            │
└─────────────────────────┘
      │ passes
      ▼
┌─────────────────────────┐
│ 2. Retrieval                                        service.py    │
│    - embed the query (local model)          embeddings.py         │
│    - cosine-similarity search over the        vector_store.py     │
│      persisted index, top_k + threshold                            │
└─────────────────────────┘
      │ (context chunks, may be empty)
      ▼
┌─────────────────────────┐
│ 3. Generation                                                      │
│    - SYSTEM_PROMPT + retrieved context + history    prompts.py    │
│    - Groq (or Mock, if unconfigured)               llm_client.py  │
└─────────────────────────┘
      │
      ▼
XictekChatResponse { reply, sources, intent, tokens_used }
```

`router.py` exposes this at `POST /api/v1/xictek/chat`, behind the
same `X-Internal-Token` auth as the rest of this service
(`src/security.py`) plus its own per-IP rate limit (`rate_limit.py`).

### Why guardrails run *before* the LLM

`SYSTEM_PROMPT` tells the model to refuse instruction-override /
prompt-extraction attempts, but a system prompt is a strong hint to
the model, not a security boundary — it can, in principle, be talked
around. `guardrails.py` is a second, deterministic layer: a set of
regex/heuristic checks that run first and short-circuit the request
(`intent: "declined_prompt_injection"`) without ever calling the LLM
for the attempts they catch. This isn't a claim that regex alone
stops every injection attempt ever devised, but it closes off the
common/scripted ones deterministically. See
`tests/xictek_website_assistant/test_qa_checklist.py` for the
question set this was built against.

## RAG flow — building the knowledge base (`ingest.py`)

```
crawl_seed_urls  --(same-domain BFS crawl, allow-listed domains only)-->
  raw HTML pages --(strip nav/header/footer/script/style, extract text)-->
    page text --(chunking.py: paragraph-aware, ~1200 chars, 200 overlap)-->
      chunks --(embeddings.py: sentence-transformers, local)-->
        vectors --(vector_store.py: VectorStore.save())-->
          data/index/embeddings.npy + data/index/chunks.json
```

Run from the repo root:

```bash
python -m src.xictek_website_assistant.ingest
```

This crawls `XICTEK_CRAWL_SEED_URLS` (default: xicteksystems.com and
hisabdo.app), restricted to `XICTEK_ALLOWED_CRAWL_DOMAINS` (it will
never follow a link off those domains), extracts readable page text,
chunks and embeds it, and overwrites whatever index already exists
under `data/index/`. It's a full rebuild every time — no incremental
indexing — which is fine at this content scale (a few hundred pages).

**Re-run required after the multilingual embedding model change:**
both models happen to output 384-dimensional vectors, so an old index
built with `all-MiniLM-L6-v2` will *load* without error under the new
`paraphrase-multilingual-MiniLM-L12-v2` — but the two models' vector
spaces aren't compatible with each other, so similarity scores against
a stale index would be meaningless. If you built an index before this
change, you must re-run `ingest.py` — there's no way to detect this
automatically from the file, so nothing will warn you if you skip it.

**Re-run this any time xicteksystems.com or hisabdo.app content
changes** (new blog post, updated services page, etc.) and restart the
service afterward so it picks up the new index (`service.py` caches
the loaded store for the process lifetime).

**Network requirement:** `ingest.py` needs real outbound HTTPS access
to xicteksystems.com / hisabdo.app. It has **not** been run yet in
this environment — a sandboxed dev container without that network
path — so `data/index/` doesn't exist yet and `GET
/api/v1/xictek/index-status` will currently report
`index_built: false`. Run it from a normal dev machine or CI runner
with outbound internet access, then commit/deploy the resulting
`data/index/` files (or re-run ingest as part of deployment).

## Embeddings

- **Model:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
  (local, via the `sentence-transformers` package) — free, no API cost,
  no network dependency at *query* time once the model's cached
  locally. Multilingual (officially supports `ar`/`hi`/`ur`/`en` + 50
  more) rather than the English-only `all-MiniLM-L6-v2`, so a query in
  Urdu, Hindi, or Arabic still retrieves the right chunks from the
  site's English-language content — bigger download (~470MB vs ~90MB),
  same inference cost at this index's size.
- Chosen over TF-IDF (used by HisabDo's smaller `financial_assistant`
  FAQ) because this knowledge base is larger and more varied
  (50+ blog posts plus company/product pages) — semantic similarity
  meaningfully beats keyword overlap at this scale.
- Vectors are L2-normalized at embed time, so retrieval is a plain dot
  product (`vector_store.py`) rather than needing a separate
  cosine-similarity step.
- No vector DB — a flat `numpy` array + parallel JSON file
  (`data/index/embeddings.npy` / `chunks.json`) is the right scale for
  a few hundred chunks, keeps the module dependency-light, and is easy
  to inspect/debug. Swapping in a real vector DB later only touches
  `vector_store.py`'s internals — `service.py` only ever sees
  `VectorStore.query()`'s return shape.

## Multilingual support (English / Urdu / Roman Urdu / Hindi / Arabic)

Per the team lead's request after reviewing the initial build:
`SYSTEM_PROMPT` (prompts.py) instructs the model to detect the
visitor's language **and script** and reply matching both — English,
Urdu (Urdu script), Roman Urdu (Urdu in Latin letters — a distinct,
very common style in Pakistan, not the same as English), Hindi, or
Arabic — translating facts from the (English) retrieved context as
needed. This needed the embedding model swap above too: an
English-only embedder wouldn't reliably match a non-English query
against English site content, so retrieval would silently degrade for
non-English visitors even if the LLM could technically reply in their
language.

The widget (`widget/xictek-widget.js`) sets `dir="auto"` on message
bubbles and the input box, so the browser's own bidi detection renders
Urdu/Arabic right-to-left and Hindi/English/Roman Urdu left-to-right
automatically per message, with no language-detection logic needed in
JS.

**Known limitations:**
- `guardrails.py`'s deterministic prompt-injection patterns are
  English-only regex. An injection attempt phrased in Urdu, Hindi, or
  Arabic won't be caught by that layer — it falls through to
  `SYSTEM_PROMPT` alone (still instructed to refuse, just a weaker
  defense-in-depth than English gets). Translating those patterns
  accurately enough to trust is real work on its own — a wrong or
  overly literal translation gives false confidence — so this is
  flagged as a follow-up rather than shipped untested.
- Roman Urdu retrieval quality is less certain than the other four
  languages. `paraphrase-multilingual-MiniLM-L12-v2`'s official
  language coverage is for Urdu in its standard (Perso-Arabic) script
  — informal Latin-script transliteration isn't a distinct language
  code the model was explicitly trained on, so a Roman Urdu query
  embedding may not align with English site content as reliably as a
  proper-script Urdu, Hindi, or Arabic query would. The LLM will still
  correctly *reply* in Roman Urdu either way (that part only depends on
  the LLM, not the embedder) — it's specifically retrieval accuracy for
  Roman Urdu *queries* that's the open question. Worth extra manual
  testing with real Roman Urdu questions before treating it as
  equally reliable to the other languages.

### Result diversification (MMR)

A real issue found while testing against the live index: several
xicteksystems.com "pillar guide" blog pages share a templated
intro/CTA paragraph with only the topic name swapped in (a
content-generation quirk on their end — confirmed by fetching a few of
these pages directly and finding the same section headers and near-
identical wording across totally different topics). Their embeddings
are near-identical, so a plain top-k-by-score query could return 3-4
near-duplicate intro paragraphs from different pages — all scoring the
same to 4 decimal places — instead of chunks that actually differ.

`VectorStore.query()` defaults to Maximal Marginal Relevance (MMR):
after picking the most relevant chunk, later picks are penalized for
being redundant with what's already selected, so results spread across
genuinely different content. Pass `diversify=False` to get plain
top-k-by-score back if needed for debugging. See
`tests/xictek_website_assistant/test_vector_store_mmr.py` for the
before/after behavior on a reproduction of the real pattern.

## Environment variables

All `XICTEK_*` settings have defaults in `config.py` — you only need
to set one in `.env` to override it. See `.env.example` at the repo
root for the current list. Notable ones:

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | *(unset)* | Chat generation (shared with HisabDo's chatbot by default). With `LLM_PROVIDER=mock` (repo default), no key is needed — see below. |
| `XICTEK_GROQ_API_KEY` | *(unset — falls back to `GROQ_API_KEY`)* | Optional: give this module its own Groq key, separate from HisabDo's chatbot |
| `XICTEK_LLM_PROVIDER` | *(unset — falls back to `LLM_PROVIDER`)* | Optional: override the provider (e.g. `groq`) independent of the shared setting |
| `XICTEK_EMBEDDING_MODEL` | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Local embedding model |
| `XICTEK_TOP_K` | `4` | Chunks retrieved per query |
| `XICTEK_RELEVANCE_THRESHOLD` | `0.35` | Minimum cosine similarity to count as a match |
| `XICTEK_ALLOWED_CRAWL_DOMAINS` | xicteksystems.com, hisabdo.app (+ `www.`) | `ingest.py`'s crawl allow-list |
| `XICTEK_RATE_LIMIT` | `20/minute` | Per-IP rate limit on `POST /chat` |
| `XICTEK_WIDGET_ALLOWED_ORIGINS` | `[]` (locked down) | CORS origins allowed to call these endpoints from a browser — see "Local widget testing" below for dev, and set to the real xicteksystems.com origin for production |
| `XICTEK_MAX_MESSAGE_CHARS` | `2000` | Hard cap so one request can't blow up embedding/LLM cost |

Shared, cross-cutting secrets (`INTERNAL_SERVICE_TOKEN`) live in the
repo-root `src.config.Settings`, not duplicated here — see
`config.py`'s module docstring. `GROQ_API_KEY` / `LLM_PROVIDER` default
to the same shared values too, but can be overridden per-module via
`XICTEK_GROQ_API_KEY` / `XICTEK_LLM_PROVIDER` above, if you want this
module's chat generation on its own key.

## Setup

```bash
pip install -r requirements.txt          # from repo root
cp .env.example .env                     # then fill in GROQ_API_KEY (optional — see below)
python -m src.xictek_website_assistant.ingest   # build the knowledge-base index (needs real internet access)
uvicorn src.main:app --reload --port 8000
```

Then open `http://localhost:8000/docs`, click **Authorize**, and paste
your `INTERNAL_SERVICE_TOKEN` value — every protected endpoint's "Try
it out" will send it automatically from there.

### Demoing with no external services at all

`LLM_PROVIDER=mock` (the repo's default) makes `POST /chat` fully
functional with zero external calls: it returns a deterministic reply
built from whatever context was retrieved (or a fallback message if
the index isn't built / nothing matched). This is enough to demo auth,
guardrails, retrieval, and response shape end-to-end without a Groq
key or a built index. Set `LLM_PROVIDER=groq` + `GROQ_API_KEY` for
real generated replies.

## Testing

```bash
pytest tests/xictek_website_assistant/
```

Covers: chunking, the vector store (build/query/save/load), the
guardrail regex layer (parametrized over injection attempts + benign
messages), and the wired `/chat` + `/index-status` endpoints. See
`test_qa_checklist.py` for the task brief's 20-30-question QA set
(safety questions + realistic visitor questions) — it runs today
against the deterministic guardrail layer and an *unbuilt* index (this
sandbox has no network path to xicteksystems.com/hisabdo.app, so
`ingest.py` hasn't been run here). Once `ingest.py` has been run for
real against a live network, re-run this file and tighten the content
question assertions from `intent == "general"` to `intent ==
"answered"` with non-empty `sources` — that's the actual
knowledge-base grounding QA pass.

## Deployment / re-indexing checklist

1. `python -m src.xictek_website_assistant.ingest` from somewhere with
   real outbound internet access (not required at request time, only
   for building/rebuilding the index).
2. Deploy `data/index/embeddings.npy` + `data/index/chunks.json`
   alongside the service (or run step 1 as part of the deploy
   pipeline).
3. Restart the service so `service.py`'s cached `VectorStore` picks up
   the new index.
4. Set `XICTEK_WIDGET_ALLOWED_ORIGINS` to the real xicteksystems.com
   origin once the widget is actually embedded there (empty/locked
   down until then — Swagger's own page is served by this app itself so
   it's same-origin and unaffected either way, but widget/demo.html
   (served on a different port) genuinely is cross-origin — see "Local
   widget testing" below).
5. Re-run step 1 any time site content changes.

## Local widget testing (CORS)

`widget/demo.html` is served on its own port (e.g. `:5500`, per its own
instructions) while the API runs on `:8000` — different ports count as
different origins under browser same-origin policy, so this genuinely
needs `XICTEK_WIDGET_ALLOWED_ORIGINS` configured, or the browser will
silently block every request the widget makes (its `fetch()` calls will
fail with something like "Sorry, something went wrong reaching the
assistant" in the widget UI, with the real reason only visible in the
browser's own dev console as a CORS error — not in this app's logs at
all, since the browser blocks the request before it's even sent for a
failed preflight).

Add this to `.env` for local testing:
```
XICTEK_WIDGET_ALLOWED_ORIGINS=["http://localhost:5500"]
```
(match whatever port you're actually serving `demo.html` on). Restart
`uvicorn` after changing this — it's read at process start.

## Widget

`widget/` contains a portable, framework-agnostic HTML/CSS/JS embed
(no React/build step) — see `widget/README.md` for embed instructions.
It's demoable standalone today and can be dropped into the real
Next.js site once repo access is available, without needing this
module to know anything about that site's stack.

## Current scope & what's deferred

Per the team lead's instruction: this task was appointed solo, without
access to the real xicteksystems.com codebase (Next.js/Vercel) or its
hosting. So for now:

- **In scope, done:** backend endpoint, RAG knowledge-base pipeline,
  guardrails, rate limiting, CORS scaffolding, a standalone embeddable
  widget, tests, this documentation.
- **Deferred, to be discussed with the team lead:** actually dropping
  the widget into the live site, confirming the real CORS origin, and
  running `ingest.py` against production content (needs the real
  outbound network access this sandbox doesn't have).
