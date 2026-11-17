# Department 3 Production Configuration Freeze Spec (v1.0)

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-17 · **Branch:** `FahadZubairi_AI`
**Machine-readable freeze:** `config/production_freeze_v1.json` (written by `scripts/freeze_config.py`)
**Enforced by:** `python scripts/freeze_config.py --verify` and `tests/test_config_freeze.py` (fails the build on any difference)
**Production settings template:** `config/production.env.example` (no secrets)

## 1. What is frozen

Everything that changes what a user is told. A change to any item below requires a new freeze version (section 6).

### 1.1 Retrieval and hybrid weights

| Parameter | Frozen value |
|---|---|
| Embedding model | `BAAI/bge-small-en-v1.5`, loaded by fastembed 0.7.3 as the quantized ONNX build `qdrant/bge-small-en-v1.5-onnx-q` |
| Model file | `model_optimized.onnx`, SHA-256 `51f1bd0addd6e859e42c2c8021a5e5461385bb676a649f4b269aa445449f2431` |
| Query prefix | `Represent this sentence for searching relevant passages: ` |
| Passage text indexed | `{title}. {heading}.\n{body}` |
| Maximum query length | 512 characters (NFKC, lower case) |
| Fusion | **0.6 × dense cosine + 0.4 × BM25** |
| BM25 | k1 1.5 · b 0.75 · score `s / (s + 5)` |
| Candidates before selection | 20 |
| **Relevance threshold** | **0.566273** (safe range 0.513 to 0.586, 17 measured cuts) |
| top-k | **2** |
| Margin to the best passage | **0.05** |
| Lexical fallback (no fastembed) | BM25 + rewrite + router gate · threshold 3.857 · top 2 · margin 2.0 |
| Metadata filter | off (measured worse on the unseen set) |
| Reranker | off (1 s per query, worse on the unseen set) |
| Router gate | only intent `faq` reaches the knowledge base |
| Query rewrite | Roman Urdu and Urdu glossary, phrases matched before words |

### 1.2 Vector index

| Parameter | Frozen value |
|---|---|
| Type | In-memory exact search (NumPy matrix). **No ANN index, so no HNSW or IVF parameters** and no approximation error |
| Dimensions · normalisation · similarity | 384 · L2 · cosine (dot product of unit vectors) |
| Records indexed | 363 (364 before the promotional "Start Managing Your Finances" block was removed from the cleaner on 17 Nov) |
| Vector checksum | `e5e0cb7482e12318` (SHA-256 of vectors rounded to 5 decimals); identical before and after the purge |
| Index file | none persisted: rebuilt at start-up and by `reload_kb()` from the approved KB (about 45 s on CPU) |
| Chunking | FAQ: one question and answer per chunk, never split · sections up to 1500 characters, split at sub-headings then paragraphs · no overlap · intros under 150 characters merged into the next section |

### 1.3 Grounding and response rules

| Rule set | Frozen |
|---|---|
| Answer rules R1–R13 (clarify, no source, conflicts, citations, sources, legal quoting, language, neighbouring topic, one source, expense ambiguity, deterministic conflict resolution, citation audit, app evidence) | `grounding/answer.py` |
| Conversation rules U4–U7 (human-support escalation, no repeats, clarification follow-up, honest limits) | `conversation.py` |
| Constants | support 0.5 · switch margin 0.2 · max 3 sentences per passage · excerpt ≤ 450 characters · related-topic answers ≤ 2 sentences · rare word = in ≤ 10 passages · source authority FAQ 1 > feature page 2 > legal 3 > guide 4 |
| System prompt | SHA-256 `354369810097aca19245891d7ec6fbf0e339bab00817c3df9312f373a3eb9232` |
| Grounding prompt (`GROUNDING_RULES`) | SHA-256 `beb020d21033ed714d4c75685d45a102488fd3132e7a22de8bd6ce8388676c7b` |
| Reply templates (English, Roman Urdu, Urdu) | SHA-256 `2bb3ec0c24871e9fa71e40c8f32b5d8a24f756f2cdbf4c9c06d4c73866e9c9b9` |

### 1.4 Safety guardrail rules

Frozen as hashed source files (line endings normalised):

| File | Rules |
|---|---|
| `guardrails.py` | Injection and instruction override (EN, Roman Urdu, Urdu), prompt extraction, secrets, jailbreak personas, unsafe requests, toxic text, domain boundary, output validation (secrets, prompt text, e-mail, phone, CNIC) |
| `service.py` | Third-party guard (relationships, ids, bare-name possessives), account-figure routing, fallbacks |
| `conversation.py` | Escalation triggers, honest limits, narrow product-capability exemption |
| `dialogue/recognizer.py` | Intent router |

Attack suite v1.1 (87 cases) and the 18 adversarial cases in `scripts/conversation_ux_eval.py` are the regression gate.

### 1.5 Knowledge base

| Item | Frozen |
|---|---|
| Approved chunks | `data/kb/approved/kb_chunks.jsonl`: **363 chunks, 23 sources**, snapshot 2026-10-27, SHA-256 in the freeze file |
| Standardized set | `data/kb/dept3/knowledge_set.jsonl`: 363 records, schema 1.0 |
| Source register | `data/knowledge_source_audit.csv` (hashed) |
| Not frozen | The live site. It has changed since 27 Oct (E2E-07); the approved KB stays until the update procedure in the runbook (section 3) is completed |

### 1.6 Required production settings

| Setting | Value |
|---|---|
| `GROUNDED_ANSWERS_ENABLED` | `true` (the code default is `false`, so this must be set) |
| `GUARDRAILS_ENABLED` | `true` |
| `DIALOGUE_ENABLED` | `true` |
| `KB_RETRIEVER_MODE` | `hybrid` (never `auto` in production: it silently falls back to lexical) |
| `LLM_PROVIDER` | `mock` until a real provider passes sections 2 and 3 of the runbook |
| `INTERNAL_SERVICE_TOKEN` | 32+ characters from the secret store |
| `FASTEMBED_CACHE_PATH` | a fixed folder, so the verified model file is reused |

## 2. Release gates the freeze was cut against (17 Nov)

| Gate | Required | Result |
|---|---|---|
| Release acceptance, grounded off and on | critical 25/25, major 6/6 | 25/25 and 6/6 |
| Safety suite v1.1, 4 configurations | CLEARED | CLEARED ×4 (43/43 · 36/36 · 8/8) |
| Multi-turn journeys | 8/8 | 8/8 |
| Adversarial cases | 18/18 | 18/18 |
| Grounded transcripts | 19/19 | 19/19 |
| End-to-end judged questions (159) | no regression; citation precision ≥ 0.86 | 0.93 |
| Knowledge latency p95 | < 250 ms | about 28 ms (quiet machine) |
| Account latency p95 | < 150 ms | about 11 ms |
| Tests | all pass | all pass except one stale XICTEK test (see closure report) |

## 3. Verification

```bash
python scripts/freeze_config.py --verify      # FREEZE OK, exit 0
```
```bash
python -m pytest tests/test_config_freeze.py  # the same check in the test suite
```

After a deployment, confirm the running service matches: `GET /api/v1/metrics` → `kb.version`, `kb.mode = hybrid`,
`kb.chunks = 363`; `python scripts/ingest_dept3.py --offline` reproduces vector checksum `e5e0cb7482e12318` on the
approved 27 Oct snapshot (offline rebuilds use the snapshot named in the manifest).

## 4. Reproducibility

Pin the environment recorded in the manifest: Python 3.13, fastembed 0.7.3, onnxruntime 1.31.1, numpy 2.4.4,
tokenizers 0.23.3. If the model file hash differs on a new machine, the vectors differ: re-run the retrieval
evaluation and recalibrate the threshold before release.

## 5. What the freeze does not cover

* The account backend is a mock (D3-01). Figures are labelled "demo data".
* No real LLM provider is enabled; answers are extractive. Wording quality with a real model is unmeasured.
* Hindi and Arabic have no glossary or guard patterns.

## 6. Changing the freeze

1. Make the change and measure it on the judged sets (`e2e_regression.py`, `retrieval_eval.py`), the safety suite and
   the conversation evaluation. No worse than the frozen results without a written reason.
2. Run `python scripts/freeze_config.py` to write `config/production_freeze_v1.json` (or a `_v2` file for a change of
   meaning) and commit it with the change, the evidence and an entry in the closure or change log.
3. `tests/test_config_freeze.py` then passes again. A pull request that changes a prompt, rule file, KB or constant
   without the freeze update fails CI.
4. Tag the release: `git tag -a dept3-freeze-v1.N -m "..."`.
