"""Regression test for build_index()'s per-page chunk deduplication.

Guards against a real issue found while indexing the live site: several
xicteksystems.com "pillar guide" pages paste the exact same paragraph
block under 10+ different <h2> headers (a content bug on their end, not
ours — see build_index()'s docstring). Without dedup, that page alone
produced ~12x more chunks than its actual unique content, wasting
embedding time for zero retrieval benefit.
"""
from unittest.mock import patch

import numpy as np

from src.xictek_website_assistant.ingest import CrawledPage, build_index


def _stub_embed(texts):
    return np.zeros((len(texts), 4), dtype="float32")


def test_repeated_paragraph_block_collapses_to_unique_chunks():
    para = "Custom Software Development Guide is most useful when connected to a clear outcome. " * 5
    duplicated_text = "\n\n".join([para] * 12)  # mirrors the real site's 12x repeat

    with patch("src.xictek_website_assistant.ingest.embed_texts", side_effect=_stub_embed):
        duplicated_store = build_index(
            [CrawledPage(url="https://example.com/dup", title="Dup", text=duplicated_text)]
        )
        single_store = build_index(
            [CrawledPage(url="https://example.com/single", title="Single", text=para)]
        )

    assert len(duplicated_store) == len(single_store)


def test_dedup_is_scoped_per_page_not_global():
    # Two different pages sharing a paragraph (e.g. a shared CTA/intro)
    # should NOT be deduped against each other — only exact-duplicate
    # chunks *within the same page* are collapsed. Cross-page dedup would
    # wrongly drop a chunk's ability to be retrieved with its own page's
    # url/title as the source.
    shared_para = "XICTEK Systems builds AI-powered software products for growing teams. " * 5

    with patch("src.xictek_website_assistant.ingest.embed_texts", side_effect=_stub_embed):
        store = build_index(
            [
                CrawledPage(url="https://example.com/a", title="A", text=shared_para),
                CrawledPage(url="https://example.com/b", title="B", text=shared_para),
            ]
        )

    urls = {c.url for c in store.chunks}
    assert urls == {"https://example.com/a", "https://example.com/b"}
    assert len(store) == 2


def test_no_duplicates_means_no_chunks_dropped():
    text = "\n\n".join(
        [
            "First distinct paragraph about services.",
            "Second distinct paragraph about technologies.",
            "Third distinct paragraph about careers.",
        ]
    )
    with patch("src.xictek_website_assistant.ingest.embed_texts", side_effect=_stub_embed):
        store = build_index([CrawledPage(url="https://example.com/x", title="X", text=text)])

    assert len(store) == 1  # short enough to pack into one chunk, per chunking.py's defaults
