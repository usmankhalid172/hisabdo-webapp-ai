# HisabDo Website Reference Ingestion Checklist

Use this checklist when cleaning, chunking, and rebuilding the HisabDo reference index.

## Source capture

- [ ] Crawl only approved HisabDo/XICTEK hosts and approved public reference URLs.
- [ ] Record the canonical source URL, page title, crawl date, and content hash/version for each document.
- [ ] Keep product overview, feature guides, FAQ, and privacy/data-handling sources in their proper categories.
- [ ] Mark page claims that conflict with another official source for owner review; do not silently merge the claims.
- [ ] Confirm the source content is current before rebuilding embeddings.

## Page cleaning

- [ ] Remove navigation, header/footer links, cookie banners, newsletter panels, sidebars, forms, repeated calls to action, and decorative labels.
- [ ] Retain meaningful headings, paragraphs, feature names, Q&A pairs, and source links.
- [ ] Convert HTML feature/specification tables to Markdown before text extraction.
- [ ] Escape literal pipe characters inside table cells and normalize cell whitespace.
- [ ] Verify that every table has one header row and a Markdown separator row.
- [ ] Do not convert marketing metrics or testimonial text into approved technical specifications without evidence and owner approval.

## Metadata

- [ ] Each cleaned file has `title`, `section`, `category`, `source_url`, `language`, and `updated_date`.
- [ ] `source_url` points to the official page that supports the content in that file.
- [ ] `updated_date` records the cleanup or review date, not an assumed page publication date.
- [ ] Metadata validation sheet lists each cleaned file and records field/link validation and outstanding source issues.

## Chunking and indexing

- [ ] Use the configured chunk size and overlap consistently; current default is 1,200 characters and 200-character paragraph overlap.
- [ ] Confirm a table that fits remains contiguous in one chunk.
- [ ] For large tables, split only between complete body rows and repeat the header plus separator in each chunk.
- [ ] Keep an oversized individual table row intact and flag it for manual review instead of slicing Markdown syntax.
- [ ] Confirm each chunk retains enough heading/source context to be retrievable and cited correctly.
- [ ] Remove exact duplicate chunks within a page without dropping separate-page source attribution.
- [ ] Rebuild embeddings and the local index only after source cleaning and chunk validation are complete.

## Release checks

- [ ] Run the focused chunking and ingestion tests in an environment with all declared project dependencies installed.
- [ ] Inspect representative serialized chunks, especially the longest feature table and specification list.
- [ ] Verify source URL/title metadata survives into each index record.
- [ ] Run retrieval queries for feature names, table values, and specification combinations; verify returned passages and citations.
- [ ] Record the index build date/version and test evidence in the ingestion log.
- [ ] Do not describe the production index as rebuilt until a fresh crawl, embedding run, and index inspection have actually completed.
