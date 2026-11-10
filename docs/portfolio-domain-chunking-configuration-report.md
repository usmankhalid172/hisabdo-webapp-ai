# Portfolio Domain — Chunking Configuration Report

**Task owner:** Muhammad Mohsin
**Scope:** Portfolio pages, project summaries, and case-study retrieval.

## Recommendation

Use **900 characters per chunk** with **180 characters of overlap** on `/portfolio` and nested `/portfolio/...` URLs. Other site pages retain the existing **1,200/200** settings. The portfolio override is wired into `build_index()` and does not change public APIs or the non-portfolio indexing configuration.

The smaller portfolio window limits blending adjacent project summaries; the overlap carries a nearby complete paragraph when it fits. Project titles, summaries, technology stacks, and outcome/metric text should be authored in adjacent paragraphs. Do not treat overlap as a guarantee for paragraphs larger than the chunk budget.

## Evaluation evidence

The selected-interpreter benchmark ran the current `chunk_text()` implementation against:

1. The checked-in `data/portfolio/hisabdo.md` public-scope source (1,465 characters, 10 paragraphs).
2. A synthetic four-project fixture (2,426 characters). Each project was represented with a title, a three-sentence summary, a technology-stack paragraph, and a metrics paragraph. Synthetic values are test markers only, not client results.

| Chunk size / overlap | Synthetic chunks | Max observed chars | Each project's title, stack, and metrics co-occurred in a chunk |
|---|---:|---:|---|
| 700 / 100 | 4 | 653 | Yes (4/4) |
| 800 / 120 | 4 | 653 | Yes (4/4) |
| **900 / 180** | **4** | **782** | **Yes (4/4)** |
| 1,000 / 200 | 4 | 782 | Yes (4/4) |
| 1,200 / 200 | 3 | 1,083 | Yes (4/4), but some chunks combine projects |

At 900/180, the current public-scope source produced **2 chunks**, with a maximum observed size of **758 characters**. It contains no client-result claim to validate. These are character-based measurements on representative local text, not token counts or a live-site retrieval-quality study.

## Content approval and scope

`data/portfolio/hisabdo.md` states that the portfolio currently displays three anonymized client-style case studies with quantified results, but their substantiation and public-display authorization are not recorded in this repository. Therefore those case studies are excluded from the indexed portfolio source pending approval. This report does not reproduce or validate their claims. Record source-owner approval and evidence before adding them to the ingestion corpus.

## Validation

Automated tests assert that portfolio URLs use 900/180, non-portfolio URLs retain 1,200/200, nested portfolio URLs are recognized, and all four synthetic project title/stack/metric groups remain co-located in at least one chunk within the configured maximum.

Run from the repository root:

```powershell
python -m pytest tests\xictek_website_assistant\test_portfolio_chunking.py -q
```

No live crawl or embedding/index rebuild was performed for this report.
