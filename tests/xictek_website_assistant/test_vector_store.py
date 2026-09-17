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
