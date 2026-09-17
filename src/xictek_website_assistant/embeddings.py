"""
Local embeddings via sentence-transformers.

Deliberate choice (per the plan locked in with the team lead): local
embeddings, not an embeddings API, so this costs nothing to run and has
no external dependency on the network at *query* time — the model is
downloaded once (first run, or during `ingest.py`) and cached locally by
the `sentence-transformers` / `huggingface_hub` libraries, same idea as
`site_size ~50+ blog posts` justifying real embeddings over TF-IDF: with
this much content, semantic similarity meaningfully beats keyword overlap.

Loaded lazily and cached (`@lru_cache`) so importing this module doesn't
pay the model-load cost, and so the same in-process model instance is
reused across both ingestion and query-time retrieval.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from .config import get_xictek_settings


@lru_cache
def _model():
    # Imported inside the function, not at module top-level: importing
    # sentence-transformers eagerly (and the torch it pulls in) slows down
    # every process that imports this module, including ones (like the
    # router at app-startup) that may not need to embed anything yet.
    from sentence_transformers import SentenceTransformer

    settings = get_xictek_settings()
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns an (n_texts, embedding_dim) float32 array, L2-normalized so
    a plain dot product is equivalent to cosine similarity in vector_store.py."""
    if not texts:
        return np.zeros((0, get_xictek_settings().embedding_dim), dtype=np.float32)
    vectors = _model().encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vectors.astype(np.float32)


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]
