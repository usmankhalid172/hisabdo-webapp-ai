"""Regression tests for ingestion diagnostics and source-change tracking."""
import numpy as np

from src.xictek_website_assistant.ingest import (
    CrawledPage,
    _duplicate_diagnostics,
    _normalise_url,
    classify_source_changes,
)
from src.xictek_website_assistant.vector_store import Chunk


def test_url_normalisation_removes_fragment_and_default_port():
    assert _normalise_url("HTTPS://Example.COM:443/a#section") == "https://example.com/a"


def test_source_change_detection_classifies_new_updated_unchanged_and_removed():
    old = {
        "sources": {
            "https://example.com/same": {"sha256": "same"},
            "https://example.com/change": {"sha256": "old"},
            "https://example.com/gone": {"sha256": "gone"},
        }
    }
    pages = [
        CrawledPage("https://example.com/same", "Same", "same content"),
        CrawledPage("https://example.com/change", "Change", "new content"),
        CrawledPage("https://example.com/new", "New", "brand new"),
    ]
    # Use hashes generated from page text for stable test expectations.
    from src.xictek_website_assistant.ingest import _source_hash
    old["sources"]["https://example.com/same"]["sha256"] = _source_hash(pages[0])
    old["sources"]["https://example.com/change"]["sha256"] = _source_hash(CrawledPage("", "", "old content"))
    changes = classify_source_changes(pages, old)
    assert changes["new"] == ["https://example.com/new"]
    assert changes["updated"] == ["https://example.com/change"]
    assert changes["unchanged"] == ["https://example.com/same"]
    assert changes["removed"] == ["https://example.com/gone"]


def test_duplicate_and_zero_vector_diagnostics():
    chunks = [
        Chunk("1", "A", "same text", "https://example.com/a"),
        Chunk("2", "B", "same text", "https://example.com/b"),
        Chunk("3", "C", "different", "https://example.com/c"),
    ]
    vectors = np.array([[1, 0], [1, 0], [0, 0]], dtype=np.float32)
    report = _duplicate_diagnostics(chunks, vectors)
    assert report["duplicate_text_groups"] == 1
    assert report["chunks_in_duplicate_text_groups"] == 2
    assert report["duplicate_vector_excess_rows"] == 1
    assert report["zero_vector_rows"] == 1
