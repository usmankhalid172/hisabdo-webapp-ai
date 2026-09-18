"""Tests for VectorStore.query()'s MMR diversification.

Reproduces the real pattern found in the live index: several
xicteksystems.com "pillar guide" pages share a templated intro
paragraph (only the topic name differs), so their embeddings are
near-identical and crowd out genuinely distinct content from a plain
top-k-by-score query. See vector_store.py's query() docstring.
"""
import numpy as np
import pytest

from src.xictek_website_assistant.vector_store import Chunk, VectorStore


def _normalize(v):
    v = np.array(v, dtype=np.float32)
    return v / np.linalg.norm(v)


@pytest.fixture()
def near_duplicate_store() -> VectorStore:
    # Four chunks sharing a near-identical vector (the templated intro
    # paragraph, present on 4 different pages) plus one chunk that's a
    # genuinely different direction (distinct, real content) but with a
    # lower raw similarity to the query.
    dup_vec = _normalize([1.0, 0.05, 0.0])
    distinct_vec = _normalize([0.5, 0.0, 0.5])

    chunks = [Chunk(chunk_id=f"dup-{i}", title=f"Templated page {i}", url=f"https://x.com/{i}", text="template intro") for i in range(4)]
    chunks.append(Chunk(chunk_id="distinct", title="Services page", url="https://x.com/services", text="real distinct content"))

    vectors = np.stack([dup_vec] * 4 + [distinct_vec])
    store = VectorStore()
    store.build(chunks, vectors)
    return store


def test_without_diversification_duplicates_crowd_out_distinct_content(near_duplicate_store):
    query = _normalize([1.0, 0.0, 0.0])
    results = near_duplicate_store.query(query, top_k=3, relevance_threshold=0.1, diversify=False)
    ids = [r.chunk.chunk_id for r in results]
    # Plain top-k-by-score: all 3 slots go to the near-identical "dup"
    # chunks since they score higher, even though they're redundant with
    # each other -- this is the bug being fixed.
    assert all(i.startswith("dup") for i in ids)
    assert "distinct" not in ids


def test_diversification_surfaces_the_distinct_chunk(near_duplicate_store):
    query = _normalize([1.0, 0.0, 0.0])
    results = near_duplicate_store.query(query, top_k=3, relevance_threshold=0.1, diversify=True, mmr_lambda=0.5)
    ids = [r.chunk.chunk_id for r in results]
    # With MMR, after the first "dup" chunk is picked, the other dup
    # chunks are penalized for redundancy -- the distinct chunk should
    # now make it into the top 3 instead of being crowded out.
    assert "distinct" in ids
    # Should not return the same duplicate content 3 times.
    assert len(set(ids)) == len(ids)


def test_diversify_is_the_default():
    # query()'s default should be the safer, diversified behavior --
    # this pattern (templated near-duplicate content) is common enough
    # on real sites that opting in defeats the point of a safe default.
    import inspect

    sig = inspect.signature(VectorStore.query)
    assert sig.parameters["diversify"].default is True


def test_diversification_returns_no_more_than_top_k(near_duplicate_store):
    query = _normalize([1.0, 0.0, 0.0])
    results = near_duplicate_store.query(query, top_k=2, relevance_threshold=0.1, diversify=True)
    assert len(results) <= 2


def test_diversification_respects_relevance_threshold():
    # A chunk below the threshold should never appear, diversification
    # or not -- MMR only reorders/selects among qualifying candidates.
    vec_high = _normalize([1.0, 0.0])
    vec_low = _normalize([0.0, 1.0])  # orthogonal to query -> score 0
    chunks = [
        Chunk(chunk_id="high", title="High", url="https://x.com/h", text="t"),
        Chunk(chunk_id="low", title="Low", url="https://x.com/l", text="t"),
    ]
    store = VectorStore()
    store.build(chunks, np.stack([vec_high, vec_low]))

    query = _normalize([1.0, 0.0])
    results = store.query(query, top_k=2, relevance_threshold=0.5, diversify=True)
    ids = [r.chunk.chunk_id for r in results]
    assert ids == ["high"]


def test_diversification_matches_plain_query_when_all_scores_distinct():
    # When there's no redundancy problem (every chunk points a different
    # direction), diversification shouldn't change which chunks come
    # back vs. a plain top-k-by-score query -- it only matters when
    # candidates are actually similar to each other.
    vectors = [
        _normalize([1.0, 0.0, 0.0]),
        _normalize([0.9, 0.1, 0.0]),
        _normalize([0.0, 1.0, 0.0]),
        _normalize([0.0, 0.0, 1.0]),
    ]
    chunks = [Chunk(chunk_id=f"c{i}", title=f"c{i}", url=f"https://x.com/{i}", text="t") for i in range(4)]
    store = VectorStore()
    store.build(chunks, np.stack(vectors))

    query = _normalize([1.0, 0.0, 0.0])
    plain = {r.chunk.chunk_id for r in store.query(query, top_k=2, relevance_threshold=-1.0, diversify=False)}
    diverse = {r.chunk.chunk_id for r in store.query(query, top_k=2, relevance_threshold=-1.0, diversify=True)}
    assert plain == diverse == {"c0", "c1"}


def test_diversification_pool_is_wide_enough_to_reach_outnumbered_distinct_content():
    """
    Regression test for a real bug found on Hamza's machine (2026-09-18):
    the first MMR implementation capped its candidate pool at
    max(top_k*8, 30) = 32 for top_k=4. The live site has ~40 pages
    sharing a templated intro paragraph, each contributing at least one
    near-duplicate high-scoring chunk to a generic query -- enough on
    their own to fill a 32-chunk pool, so the genuinely distinct content
    (the real /services page) never even entered the candidate pool for
    MMR to consider, and kept getting crowded out even after "fixing"
    diversification. This test reproduces that at a smaller scale: 40
    near-duplicate chunks outscoring 1 distinct chunk, with top_k=4 --
    the old pool sizing would exclude the distinct chunk entirely; the
    fix (a much wider pool, since scoring is cheap at this index scale)
    must include it.
    """
    dup_vec = _normalize([1.0, 0.05, 0.0])
    distinct_vec = _normalize([0.5, 0.0, 0.5])  # scores lower, but is genuinely different

    chunks = [Chunk(chunk_id=f"dup-{i}", title=f"Templated {i}", url=f"https://x.com/{i}", text="template") for i in range(40)]
    chunks.append(Chunk(chunk_id="distinct", title="Services", url="https://x.com/services", text="real content"))
    vectors = np.stack([dup_vec] * 40 + [distinct_vec])

    store = VectorStore()
    store.build(chunks, vectors)

    query = _normalize([1.0, 0.0, 0.0])
    results = store.query(query, top_k=4, relevance_threshold=0.1, diversify=True)
    ids = [r.chunk.chunk_id for r in results]
    assert "distinct" in ids, (
        "distinct chunk was excluded -- likely the candidate pool is too small "
        "to reach content that's outnumbered by near-duplicates"
    )
