# HisabDo Reference Chunking Evaluation Log

**Date:** 10 November 2026
**Scope:** Cleaned HisabDo product references and Markdown/HTML feature tables
**Chunk configuration:** Existing defaults: 1,200 characters per chunk; 200-character overlap for ordinary paragraph hard-splits.

## Change under evaluation

The original chunker split only on blank lines and hard-split an oversized block by character offset. That could divide a Markdown table in the middle of a row and leave later chunks without their column labels.

The updated flow:

1. Recognizes a Markdown table by its header row and separator row.
2. Keeps a table together when it fits in the target chunk size.
3. Splits an oversized table only between data rows and repeats the header and separator in each table chunk.
4. Keeps an individual overlong data row intact rather than cutting through its Markdown syntax.
5. Converts HTML tables into Markdown rows before page text is passed to the chunker.

## Evaluation results

| Check | Result | Evidence |
|---|---|---|
| Chunker unit suite | **Pass — 9 passed** | `python -m pytest --confcutdir=tests/xictek_website_assistant tests/xictek_website_assistant/test_chunking.py -q` |
| Curated `data_handling.md` at defaults | **Pass — 4 chunks; largest 1,064 characters** | Local chunk generation from cleaned reference file, including its metadata header. |
| Curated `feature_reference.md` at defaults | **Pass — 3 chunks; largest 1,140 characters** | Local chunk generation from cleaned reference file, including its metadata header. |
| Curated `product_overview.md` at defaults | **Pass — 2 chunks; largest 1,185 characters** | Local chunk generation from cleaned reference file, including its metadata header. |
| Synthetic 10-row feature table, 180-character target | **Pass — 10 chunks; largest 169 characters** | Every chunk retained the header and separator; each source data row appeared exactly once; all lines remained complete table rows. |
| Single oversized table row | **Pass** | Unit case verifies a row larger than the chunk target stays whole. |
| Markdown table that fits in one chunk | **Pass** | Unit case verifies header, separator, and rows remain unchanged and contiguous. |
| HTML-table extraction integration test | **Added; execution blocked** | The current interpreter does not have `beautifulsoup4` (`bs4`) installed. The focused ingestion test module cannot import. |
| Full shared test setup | **Blocked before tests run** | Root `tests/conftest.py` imports the main app, which requires missing `slowapi`. The isolated chunker test suite bypassed that shared setup and passed. |
| Syntax check | **Pass** | `python -m py_compile src/xictek_website_assistant/chunking.py src/xictek_website_assistant/ingest.py` |

## Interpretation and limits

- The cleaned HisabDo references contain Q&A and prose, not a product-specification table. Their measured chunk counts therefore verify the current curated files; the synthetic table fixture verifies table row integrity and header repetition.
- The HTML extraction implementation has a focused regression test, but it needs the repository ingestion dependencies installed before that test can execute.
- This evaluation did not run a live crawl, rebuild the production vector index, regenerate embeddings, or assess retrieval relevance. It validates local chunk construction only.

## Files changed

- `src/xictek_website_assistant/chunking.py`
- `src/xictek_website_assistant/ingest.py`
- `tests/xictek_website_assistant/test_chunking.py`
- `tests/xictek_website_assistant/test_ingest_dedup.py`
