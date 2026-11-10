# Department 3 Ingestion Master Checklist

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-10 · **Branch:** `FahadZubairi_AI`
**Pipeline:** `scripts/ingest_dept3.py` · **Tests:** `tests/test_ingest_dept3.py` (8)
**Reports:** `data/kb/dept3/ingestion/ingest_<date>_<time>_<mode>.json` and `.md`
**Configuration:** `docs/dept3-chunking-embedding-config.md`

## 1. How to run

```bash
python scripts/ingest_dept3.py --fetch --dry-run     # fetch live pages, full report, publish nothing
```
```bash
python scripts/ingest_dept3.py --fetch               # same, and publish if every gate passes
```
```bash
python scripts/ingest_dept3.py --offline             # rebuild from the latest saved snapshots
```

The exit code is 0 when the gates pass and 2 when publishing was blocked. Schedule it every 30 days, and within 7 days
of an app release (P-FAQ), always as `--dry-run` first.

## 2. Master checklist

| # | Stage | Check | Automated | Pass condition | On failure |
|---|---|---|---|---|---|
| 1 | Sources | Only `Approved` rows of `data/knowledge_source_audit.csv` are read | Yes | Count matches the register | Fix the register |
| 2 | Sources | **New** sources (in the register, not in the last set) are listed | Yes | Reviewed by the content owner | Approve or remove the row |
| 3 | Sources | **Removed** sources: their records are deleted and listed | Yes | Removal intended | Restore the row |
| 4 | Fetch | Each page fetched with 2 retries | Yes | No failed pages | **Failed page captured** (error, URL); its last good snapshot is used and marked stale, so records are not lost |
| 5 | Clean | Page parsed into chunks | Yes | No parse errors | **Parse error captured**; the source's previous records are carried forward; fix the cleaner for the new layout |
| 6 | Clean | Every cleaned sentence is found on the source page | Yes | 0 `NOT FOUND ON PAGE` | Stop: the cleaner changed wording |
| 7 | Dedupe | Exact and contained duplicates removed (higher-priority source kept) | Yes | Each listed with `duplicate_of` | Check the duplicate is a true copy |
| 8 | Dedupe | Conflicting facts across sources flagged (`needs_confirmation`) | Yes | Known conflicts only (currency, C-06) | Content owner decides |
| 9 | Records | Promotional filler purged | Yes | Listed | |
| 10 | Records | Every record validates against schema v1.0 | Yes | 0 schema errors | Record excluded and listed |
| 11 | Diff | Records **added / modified / deleted / unchanged** against the last set (by content hash) | Yes | Changes match what changed on the site | Review each modified record |
| 12 | Vectors | Each vector: 384 dimensions, finite, non-zero | Yes | 0 vector errors | **Vector error captured**; record excluded and listed |
| 13 | Vectors | Manifest: model file SHA-256, versions, parameters, vector checksum | Yes | `onnx_sha256` unchanged | Rerun evaluations, recalibrate |
| 14 | Gate | Record count ≥ 80% of the last set | Yes | | Not published |
| 15 | Gate | No phone numbers, CNICs or emails (except the official support email) | Yes | | Not published |
| 16 | Publish | `knowledge_set.jsonl` and `index_manifest.json` replaced only when all gates pass | Yes | | Old set keeps serving |
| 17 | After | Tests: `pytest tests/test_ingest_dept3.py tests/test_dept3_knowledge_set.py tests/test_kb_privacy.py` | Manual | All pass | |
| 18 | After | Retrieval and grounded-answer evaluations if more than 10% of records changed | Manual | Hit rate not lower | Recalibrate (runbook §5.3) |
| 19 | After | `service.reload_kb()` to load without restart (validates first) | Manual | | Bad file rejected, current index keeps serving |

## 3. Tested failure handling

| Scenario (test) | Result |
|---|---|
| Unchanged pages | Diff 0/0/0, 363 unchanged, published, manifest written |
| Page fetch times out | Failed page listed with the error; stale snapshot used; 0 records deleted |
| Page wording changed | Exactly the changed record reported as modified |
| Source removed from the register | Source listed as removed; only its records deleted |
| Page layout cannot be parsed | Parse error listed; previous records carried forward; 0 deleted |
| Duplicates | Both listed with `duplicate_of`; removed copy not published, kept copy published |
| Large drop (only 5 sources) | Gate fails, nothing published, old 363 records kept |
| NaN, zero and wrong-size vectors | All three captured as vector errors and excluded |

## 4. Execution report, 2026-11-10

| | Offline rebuild (published) | Live fetch (dry run) |
|---|---|---|
| Sources | 23 approved · none added or removed | 23 · none added or removed |
| Fetch | Snapshots 2026-10-27 | 23 fetched · **0 failed pages** |
| Clean | 366 chunks · 0 parse errors · 0 wording changes | 336 chunks · **1 parse error: OFF-01 (Help Center FAQ)** · 0 wording changes |
| Duplicates removed | 2 | 3 |
| Conflicts | supported currencies (known, C-06) | none (the conflicting text is no longer on the new pages) |
| Records | 363 · 1 promotional purged · 0 schema errors | 365 · 33 carried forward from OFF-01 |
| Diff | 0 added · 0 modified · 0 deleted · 363 unchanged | **21 added · 2 modified · 19 deleted** · 342 unchanged |
| Vectors | 363 · 0 errors · checksum `e5e0cb7482e12318` | 365 · 0 errors |
| Gates | Pass | Pass (dry run, not published) |
| Time | 44.7 s | 71.4 s |

**What the live run found:** the hisabdo.app home page (OFF-02) and the about page (OFF-03) were redesigned after
27 Oct. Their old sections were replaced by new ones, which is where the 21 added and 19 deleted records come from. The Help Center FAQ
page (OFF-01) now loads its content in a way the cleaner cannot read, so its 33 records were carried forward
unchanged rather than lost.

**Action before publishing the live set:**

1. Update the OFF-01 cleaner for the new FAQ page layout.
2. The content owner reviews the 21 new home and about sections. Some are marketing copy ("Loved by merchants",
   "Test the parsing engine live") that must be purged.
3. Then rerun with `--fetch` and run the evaluations.

The published set stays the verified 27 Oct set until then.
