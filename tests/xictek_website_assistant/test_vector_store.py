"""Unit tests for the local numpy-backed vector store."""
import numpy as np
import pytest

from src.xictek_website_assistant.vector_store import Chunk, VectorStore


def _unit_vector(x: float, y: float) -> np.ndarray:
    v = np.array([x, y], dtype=np.float32)
    return v / np.linalg.norm(v)


@pytest.fixture()
def populated_store() -> VectorStore:
    chunks = [
        Chunk(chunk_id="a", title="Services page", url="https://xicteksystems.com/services", text="We build AI backends."),
        Chunk(chunk_id="b", title="Careers page", url="https://xicteksystems.com/careers", text="We're hiring interns."),
        Chunk(chunk_id="c", title="Unrelated page", url="https://xicteksystems.com/misc", text="Completely unrelated content."),
    ]
    vectors = np.stack([_unit_vector(1, 0), _unit_vector(0, 1), _unit_vector(-1, 0)])
    store = VectorStore()
    store.build(chunks, vectors)
    return store


def test_empty_store_query_returns_no_matches():
    store = VectorStore()
    results = store.query(_unit_vector(1, 0), top_k=4, relevance_threshold=0.0)
    assert results == []


def test_build_rejects_mismatched_chunk_and_vector_counts():
    store = VectorStore()
    with pytest.raises(ValueError):
        store.build([Chunk(chunk_id="a", title="t", text="x")], np.zeros((2, 2), dtype=np.float32))


def test_query_returns_best_match_first(populated_store):
    results = populated_store.query(_unit_vector(1, 0), top_k=3, relevance_threshold=0.0)
    assert results[0].chunk.chunk_id == "a"
    assert results[0].score == pytest.approx(1.0, abs=1e-5)


def test_query_respects_relevance_threshold(populated_store):
    # query vector near-orthogonal to everything but "a" — high threshold
    # should drop the weak/negative matches.
    results = populated_store.query(_unit_vector(1, 0), top_k=3, relevance_threshold=0.9)
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "a"


def test_query_respects_top_k(populated_store):
    results = populated_store.query(_unit_vector(1, 0), top_k=1, relevance_threshold=-1.0)
    assert len(results) == 1


def test_save_and_load_roundtrip(populated_store, tmp_path):
    populated_store.save(index_dir=tmp_path)
    loaded = VectorStore.load(index_dir=tmp_path)
    assert len(loaded) == len(populated_store)
    assert loaded.chunks[0].chunk_id == populated_store.chunks[0].chunk_id
    assert loaded.chunks[0].url == populated_store.chunks[0].url
    results = loaded.query(_unit_vector(1, 0), top_k=1, relevance_threshold=0.0)
    assert results[0].chunk.chunk_id == "a"


def test_load_missing_index_returns_empty_store(tmp_path):
    store = VectorStore.load(index_dir=tmp_path / "does-not-exist")
    assert len(store) == 0


def test_save_writes_metadata_recording_the_embedding_model(populated_store, tmp_path, monkeypatch):
    monkeypatch.setenv("XICTEK_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    from src.xictek_website_assistant.config import get_xictek_settings

    get_xictek_settings.cache_clear()
    populated_store.save(index_dir=tmp_path)

    import json

    metadata = json.loads((tmp_path / "metadata.json").read_text())
    assert metadata["embedding_model"] == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    get_xictek_settings.cache_clear()


def test_load_warns_on_embedding_model_mismatch(populated_store, tmp_path, monkeypatch):
    from unittest.mock import patch

    from src.xictek_website_assistant.config import get_xictek_settings

    # Save under one model...
    monkeypatch.setenv("XICTEK_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    get_xictek_settings.cache_clear()
    populated_store.save(index_dir=tmp_path)

    # ...then load under a different one -- should warn, not silently
    # return results as if nothing's wrong. The logger's own handler
    # writes JSON straight to stdout regardless of caplog/propagation
    # config, so assert directly on the call rather than fighting that.
    monkeypatch.setenv("XICTEK_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    get_xictek_settings.cache_clear()
    with patch("src.xictek_website_assistant.vector_store.logger.warning") as mock_warn:
        VectorStore.load(index_dir=tmp_path)
    assert any("mismatch" in str(call.args) for call in mock_warn.call_args_list)
    get_xictek_settings.cache_clear()


def test_load_does_not_warn_when_model_matches(populated_store, tmp_path, monkeypatch):
    from unittest.mock import patch

    from src.xictek_website_assistant.config import get_xictek_settings

    monkeypatch.setenv("XICTEK_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    get_xictek_settings.cache_clear()
    populated_store.save(index_dir=tmp_path)

    with patch("src.xictek_website_assistant.vector_store.logger.warning") as mock_warn:
        VectorStore.load(index_dir=tmp_path)
    assert not any("mismatch" in str(call.args) for call in mock_warn.call_args_list)
    get_xictek_settings.cache_clear()
