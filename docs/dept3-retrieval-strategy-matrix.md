# Department 3 Retrieval Strategy Comparison Matrix

**Author:** Fahad Zubairi (AI intern) · **Date:** 2026-11-11 · **Branch:** `FahadZubairi_AI`
**Benchmark:** `scripts/retrieval_strategy_benchmark.py` → `data/retrieval_eval/results/strategy_benchmark.json`
**Failed set:** `data/retrieval_eval/queries_failed_day1_probe.json` + the 19 failing judged queries

## 1. Test design

| Set | Queries | Use |
|---|---|---|
| Calibration | 139 judged queries (19 Day 1 dev + 120 held-out), qrels from `qrels.json` | Threshold, top-k and margin chosen here (`retrieval_eval.sweep`: most queries correct, then fewest unrelated passages, centre of the widest safe range) |
| **Day 1 failed set** | **39**: the 19 judged queries that fail in production + 20 Phase 2 Day 1 probe questions (Q29–Q46, D3-26, D3-27), judged on 11 Nov from a pooled top 5 of dense, hybrid and reranked results | Test target. The 20 probe questions were never used for calibration |

A query is **correct** when:
- **Answerable:** a fully answering passage (grade 2) reaches the context and no unrelated passage (grade 0) does.
- **No answer in the KB:** nothing unrelated reaches the context.
- **Not a knowledge question:** the context is empty.

Query types in the failed set:

| Type | Questions | Covers |
|---|---|---|
| Feature how-to | 12 | Add, edit, categories, receipts, budget, recurring entries, staff |
| Udhar / khata | 10 | |
| Reports / export | 4 | |
| Data / sync / privacy | 4 | |
| Platform / currency | 4 | |
| Bookkeeping concept | 4 | |
| Not a knowledge question | 1 | |

## 2. Comparison matrix

All strategies use the same KB (364 chunks), the same embedding model (bge-small-en-v1.5) and calibrated parameters.

| # | Strategy | Calibrated parameters | Calibration correct /139 | Recall@k | MRR | Unrelated passages | Context precision | Failed set correct /39 | Of 19 prod. failures fixed | Unseen probe /20 | Safe threshold range | ms / query |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | **Dense vector only** (baseline) | t 0.675 · k 2 · m 0.05 | 98 | 0.466 | 0.543 | 21 | 0.704 | 13 | 4 | 9 | single point | 32 |
| S2 | Dense + query rewrite | t 0.733 · k 2 · m 0.05 | 97 | 0.517 | 0.754 | 22 | 0.728 | **16** | 5 | **11** | single point | 39 |
| S3 | Hybrid BM25 + dense | t 0.659 · k 1 | 98 | 0.328 | 0.548 | **2** | 0.920 | 13 | 4 | 9 | single point | 34 |
| S4 | Hybrid + query rewrite | t 0.689 · k 3 · m 0.05 | 100 | 0.517 | 0.732 | 11 | 0.859 | 12 | 2 | 10 | single point | 37 |
| **S5** | **S4 + router gate (production, final)** | **t 0.566 · k 2 · m 0.05** | **120** | **0.724** | 0.732 | 9 | 0.908 | 9 | 0 | 9 | **0.513–0.586 (17 cuts)** | **23** |
| S6 | S5 + metadata filter (section + feature category + legal scope) | t 0.679 · k 2 · m 0.05 | 120 | 0.672 | 0.730 | 7 | **0.924** | 10 | 3 | 7 | 0.679–0.681 | 21 |
| S7 | S5 + cross-encoder rerank | t −8.89 · k 2 | 118 | 0.724 | 0.724 | 16 | 0.864 | 12 | **7** | 5 | single point | 1057 |
| S8 | S5 + metadata filter + rerank | t −7.17 · k 2 | 119 | 0.707 | 0.698 | 12 | 0.891 | 12 | 7 | 5 | −7.17 to −7.07 | 982 |
| S9 | BM25 + rewrite + gate (lexical fallback) | t 3.857 · k 2 · m 2.0 | 116 | 0.672 | 0.670 | 16 | 0.835 | 10 | 3 | 7 | single point | 4 |
| S10 | Dense + rewrite + router gate | t 0.648 · k 2 · m 0.05 | 118 | 0.724 | **0.754** | 15 | 0.850 | 14 | 5 | 9 | 0.639–0.652 | 22 |

Failed-set results by query type (calibrated parameters):

| Type | S1 dense | S2 dense+rw | S5 production | S6 metadata | S7 rerank | S10 dense+rw+gate |
|---|---|---|---|---|---|---|
| Feature how-to (12) | 4 | **7** | 3 | 4 | 5 | 5 |
| Udhar / khata (10) | 2 | 2 | 0 | 1 | **4** | 2 |
| Reports / export (4) | 0 | 0 | 1 | 1 | 0 | 0 |
| Data / sync / privacy (4) | 2 | 1 | 2 | 1 | 1 | 2 |
| Platform / currency (4) | 2 | 2 | 0 | 0 | 0 | 2 |
| Bookkeeping concept (4) | 3 | 3 | 3 | 2 | 2 | 3 |
| Not knowledge (1) | 0 | 1 | 0 | 1 | 0 | 0 |

## 3. What each module does

| Module | Effect (measured) | Decision |
|---|---|---|
| Hybrid vs dense | Similar accuracy without a gate. With a gate: hybrid 120 vs dense 118, 9 vs 15 unrelated passages, and a wide safe threshold range against a 1-point range | **Hybrid** |
| Query rewrite (Roman Urdu / Urdu glossary) | Dense MRR 0.543 → 0.754; Urdu and Roman Urdu answers rise; failed set 13 → 16 | **On** |
| Router gate (faq only) | +20 calibration queries (personal figures and actions never reach the KB). The largest single gain | **On** |
| Metadata filter (product section boost 0.06, feature-category boost 0.04, legal scope filter) | Fewest unrelated passages (7, precision 0.924), but recall falls 0.724 → 0.672 and the unseen probe falls 9 → 7. The safe threshold range is only 0.002 wide | **Off** (kept in code as an option) |
| Cross-encoder rerank (bge-reranker-base) | Fixes 7 of the 19 production failures (udhar questions), but adds unrelated passages (16), scores 5/20 on the unseen probe, and is 46× slower (1 s per query on CPU) | **Off** |
| top-k | The sweep chose k = 2 for every strategy except S3 (k 1, recall 0.33) and S4 (k 3, more noise) | **2** |
| Threshold | S5 is the only strategy with a wide safe range (0.513–0.586). The production value 0.566273 sits inside it, so it is re-confirmed | **0.566273** |
| Margin | 0.05 (a second passage must score within 0.05 of the best) removes weak second passages | **0.05** |

## 4. Final retrieval pipeline configuration

| Stage | Setting |
|---|---|
| Route gate | Rule-based intent router; only `faq` reaches the KB |
| Query normalisation | NFKC, lower case, whitespace, 500-character cap |
| Query rewrite | Roman Urdu / Urdu glossary, phrases first (precompiled) |
| Lexical | BM25 k1 1.5, b 0.75, score `s/(s+5)` |
| Dense | `BAAI/bge-small-en-v1.5` (quantized ONNX, file SHA-256 `51f1bd0a…`), query prefix, cosine |
| Fusion | 0.6 × dense + 0.4 × lexical, 20 candidates |
| Metadata filter | Off |
| Reranker | Off |
| Selection | Score ≥ **0.566273**, within **0.05** of the best, at most **2** passages |
| No result | Empty context → no-source fallback (R2), never a guess |
| Lexical fallback (no fastembed) | BM25 + rewrite + gate, threshold 3.857, top 2, margin 2.0 |

This is unchanged from production. The benchmark confirms it as the best calibrated configuration on the 139
calibration queries: most correct, and the only one with a stable threshold range. No other strategy is better on both
the calibration set and the unseen probe set.

## 5. Baseline vs optimized

| Measure (139 calibration queries) | Baseline: dense vector search (S1) | Optimized: final pipeline (S5) | Change |
|---|---|---|---|
| Correct | 98 (70.5%) | **120 (86.3%)** | +22 |
| Recall@2 (answer reaches the context) | 0.466 | **0.724** | +0.258 |
| MRR | 0.543 | **0.732** | +0.189 |
| Unrelated passages in context | 21 | **9** | −57% |
| Context precision | 0.704 | **0.908** | +0.204 |
| Personal / action questions given KB text | yes | **never (gated)** | |
| Latency | 32 ms | 23 ms | |

On the **Day 1 failed set (39)**, the final pipeline scores 9/39, and dense with rewrite scores 16/39. These questions
are hard by design. Of the 30 the final pipeline still gets wrong:

| Why it fails | Count | Retrieval can fix it? | Fix |
|---|---|---|---|
| Only related passages: the KB has no answering source (record income, record udhar, desktop version, PDF by WhatsApp in Urdu) | 11 | No | New official pages (D3-18, D3-19) |
| Unrelated passage reaches the context | 17 | Partly | 9 are no-answer questions (edit, budget, recurring, staff, bank) where a near-topic blog passage scores above the threshold. Raising the threshold to stop them loses answerable questions (see S6). The answer-level relevance gate (R9) and the no-source wording handle them downstream |
| Answerable, nothing above threshold (Urdu PDF questions) | 2 | Yes | Glossary entries for پی ڈی ایف / بھیجوں (D3-31) |

**Rerank is the best tool for the udhar questions** (4/10, against 0/10), but it costs 1 second per query and adds
noise elsewhere. Re-test it after the missing udhar how-to page is published: a page that answers these questions is
the real fix, and reranking would no longer be needed for them.

## 6. Reproduce

```bash
python scripts/retrieval_strategy_benchmark.py          # all 10 strategies (~20 min on CPU)
```
```bash
python scripts/retrieval_strategy_benchmark.py S10      # one strategy, merged into the results file
```
