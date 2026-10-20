
import pytest
from types import SimpleNamespace
from unittest.mock import patch

import embeddings


def fake_response(texts):
    data = [
        SimpleNamespace(
            index=i,
            embedding=[0.1] * embeddings.VECTOR_DIMENSION,
        )
        for i, _ in enumerate(texts)
    ]
    return SimpleNamespace(data=data)


def test_empty_list_returns_empty():
    assert embeddings.generate_embeddings([]) == []


def test_one_vector_per_chunk():
    chunks = ["Invoice due date", "Customer balance", "Sales report"]

    with patch.object(
        embeddings.client.embeddings,
        "create",
        side_effect=lambda **kwargs: fake_response(kwargs["input"]),
    ) as mock_create:
        vectors = embeddings.generate_embeddings(chunks)

    assert len(vectors) == len(chunks)
    assert all(
        len(vector) == embeddings.VECTOR_DIMENSION
        for vector in vectors
    )
    assert mock_create.call_count == 1


def test_chunks_are_sent_in_batches():
    chunks = [f"Business question {i}" for i in range(70)]

    with patch.object(
        embeddings.client.embeddings,
        "create",
        side_effect=lambda **kwargs: fake_response(kwargs["input"]),
    ) as mock_create:
        vectors = embeddings.generate_embeddings(chunks)

    assert len(vectors) == 70
    assert mock_create.call_count == 3


def test_empty_chunk_is_rejected():
    with pytest.raises(ValueError, match="Chunk 1"):
        embeddings.generate_embeddings(["Valid text", "   "])


def test_very_long_chunk_is_rejected():
    long_text = "x" * (embeddings.MAX_CHARS + 1)

    with pytest.raises(ValueError, match="exceeds"):
        embeddings.generate_embeddings([long_text])


def test_provider_failure_does_not_escape_as_raw_error():
    with patch.object(
        embeddings,
        "_request_embeddings",
        side_effect=RuntimeError("provider unavailable"),
    ):
        with pytest.raises(embeddings.EmbeddingProviderError):
            embeddings.generate_embeddings(["Test chunk"])
