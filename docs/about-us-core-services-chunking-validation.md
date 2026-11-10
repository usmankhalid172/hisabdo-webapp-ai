# About Us & Core Services — Chunking Rules and Parsing Validation

**Task owner:** Muhammad Mujtaba Chohan
**Scope:** Website-assistant ingestion of corporate descriptions, service tables, and policy lists.

## Objective

Keep related company descriptions and service listings retrievable as coherent context. A service row or policy bullet must not be cut in half by chunk boundaries. When a structured block exceeds the target chunk size, split only between complete rows/items and retain nearby rows/items as overlap context.

## Recommended rules

| Content | Parsing/chunking rule |
|---|---|
| About Us descriptions | Keep headings and each paragraph as separate blocks; pack adjacent blocks into the same chunk while they fit. |
| Core Services table | Emit one `Service | Description` row per line. Keep the table in a single block; if it exceeds the budget, repeat its header and split only between rows. |
| Policy/feature bullets | Emit one complete bullet per line. Keep the list together when it fits; otherwise split between bullets and include complete nearby bullets as overlap. |
| Long unstructured prose | Retain the existing hard-split fallback with character overlap when there are no identifiable row/item boundaries. |
| Navigation and page chrome | Continue removing navigation, headers, footers, scripts, styles, and forms before extraction. |

### Parameters

Use the existing production defaults: **1,200 characters per chunk** and **200 characters of overlap**. The overlap is a character budget for prose and a best-effort budget for whole rows/items in structured blocks; atomic structured content may exceed the overlap budget rather than being truncated. Table headers are repeated in every table continuation chunk. The defaults are retained because this task adds structure-aware boundaries without requiring a broader embedding/index migration.

## Parsing and validation

The HTML extractor now recognizes headings, paragraphs, blockquotes, tables, and ordered/unordered lists as content blocks. Table cells are joined with ` | ` and list entries receive a bullet prefix; blocks are separated by blank lines so the chunker can distinguish narrative blocks from multiline structured blocks.

Offline regression coverage checks:

- Page title extraction and exclusion of navigation text.
- Preservation of About Us heading/paragraph context.
- Table headers, cell contents, and row boundaries.
- Full policy bullet preservation.
- Single-chunk preservation for a service listing that fits.
- Row/item-boundary splitting for oversized tables and lists, including repeated table headers and configured size limits.

The validation uses representative HTML fixtures and synthetic oversized tables/lists. It does **not** claim a live-site crawl or production corpus measurement; network crawling and re-indexing remain separate operational validation steps.

Run `python -m pytest tests\xictek_website_assistant -q` from the repository root to execute the validation and related assistant regression tests. Latest result: **132 passed**; two existing Starlette deprecation warnings are emitted by unrelated test/client compatibility paths.

## Acceptance criteria

1. A fitting service table or policy list remains within one chunk.
2. Oversized structured content is split only at complete rows/items, without dropping any item.
3. Each continued service-table chunk includes its header.
4. Chunks stay within the configured maximum when each individual structured item fits.
5. The existing paragraph-aware behavior remains covered by the original chunking tests.
