"""Semantic retrieval with a relevance threshold and a safe fallback.

Every retrieval ends in exactly one status, and the chatbot behaves differently for each:

    ok           at least one KB entry scored >= threshold  -> answer from it and cite it
    no_match     nothing reached the threshold               -> say there is no verified information
    empty        no KB version is active                     -> same as no_match
    unavailable  the embedding service failed                -> say product info is temporarily unavailable

The threshold is the difference between "retrieval" and "always return the
nearest thing": without it, a biryani question still gets the 4 least-unrelated
passages, and the model is tempted to answer from them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .embeddings import Embedder, EmbeddingUnavailable, cosine
from .models import Note
from .vector_store import VectorStore, text_hash

MAX_SECTIONS_PER_SOURCE = 2


@dataclass(frozen=True)
class KBSource:
    """One KB entry that passed the threshold, with the passages that matched."""

    id: str
    title: str
    source: str
    kb_version: str
    score: float  # best passage score, 0..1
    passages: tuple[tuple[str, str], ...]  # (section heading, text)


@dataclass(frozen=True)
class RetrievalResult:
    status: str  # ok | no_match | empty | unavailable
    sources: tuple[KBSource, ...] = ()
    kb_version: str | None = None
    best_score: float | None = None  # highest score seen, even if below the threshold (for tuning)
    threshold: float = 0.0
    query_vector: list[float] | None = field(default=None, repr=False, compare=False)


class KBRetriever:
    def __init__(self, store: VectorStore, embedder: Embedder, threshold: float = 0.60, top_k: int = 4) -> None:
        self.store = store
        self.embedder = embedder
        self.threshold = threshold
        self.top_k = top_k

    def retrieve(self, question: str) -> RetrievalResult:
        version = self.store.active_version()
        try:
            query_vector = self.embedder.embed_query(question)
        except EmbeddingUnavailable:
            return RetrievalResult("unavailable", kb_version=version, threshold=self.threshold)
        if version is None:
            return RetrievalResult("empty", threshold=self.threshold, query_vector=query_vector)
        if self.store.active_model() != self.embedder.model:
            # Vectors from different models are not comparable; refusing is safer than wrong matches.
            return RetrievalResult("unavailable", kb_version=version, threshold=self.threshold, query_vector=query_vector)

        hits = self.store.search(query_vector, self.top_k * 3)
        best = hits[0][1] if hits else None
        grouped: dict[str, list] = {}
        for chunk, score in hits:
            if score >= self.threshold:
                grouped.setdefault(chunk.entry_id, []).append((chunk, score))

        sources = []
        for entry_id, items in grouped.items():
            items = items[:MAX_SECTIONS_PER_SOURCE]
            first = items[0][0]
            sources.append(KBSource(
                id=entry_id, title=first.title, source=first.source, kb_version=first.kb_version,
                score=round(items[0][1], 4), passages=tuple((c.section, c.text) for c, _ in items),
            ))
        sources = sorted(sources, key=lambda s: s.score, reverse=True)[: self.top_k]
        return RetrievalResult(
            "ok" if sources else "no_match", tuple(sources), version,
            round(best, 4) if best is not None else None, self.threshold, query_vector,
        )


class NoteIndex:
    """Semantic search over ONE business's notes, replacing keyword overlap.

    Vectors are created lazily: each search first embeds any note that is new or
    whose text changed, and drops vectors of deleted notes. Returns None when the
    embedding service is unavailable, so the caller can fall back to keyword matching.
    """

    def __init__(self, store: VectorStore, embedder: Embedder, threshold: float = 0.55, top_k: int = 5) -> None:
        self.store = store
        self.embedder = embedder
        self.threshold = threshold
        self.top_k = top_k

    def rank(self, business_id: str, notes: list[Note], query_vector: list[float] | None) -> list[Note] | None:
        if query_vector is None:
            return None
        wrong_tenant = [n.id for n in notes if n.business_id != business_id]
        if wrong_tenant:  # defence in depth: never index or return another business's notes
            raise ValueError(f"notes from another business passed to NoteIndex: {wrong_tenant}")
        try:
            self._sync(business_id, notes)
        except EmbeddingUnavailable:
            return None
        vectors = self.store.note_vectors(business_id, self.embedder.model)
        scored = [(cosine(query_vector, vectors[n.id]), n) for n in notes if n.id in vectors]
        scored = [(s, n) for s, n in scored if s >= self.threshold]
        scored.sort(key=lambda sn: (-sn[0], -sn[1].created_at.timestamp()))
        return [n for _, n in scored[: self.top_k]]

    def _sync(self, business_id: str, notes: list[Note]) -> None:
        stored = self.store.note_hashes(business_id, self.embedder.model)
        current = {n.id: text_hash(n.content) for n in notes}
        stale = [n for n in notes if stored.get(n.id) != current[n.id]]
        if stale:
            vectors = self.embedder.embed_documents([n.content for n in stale])
            self.store.save_note_vectors(
                business_id, self.embedder.model, [(n.id, current[n.id], v) for n, v in zip(stale, vectors)]
            )
        deleted = [note_id for note_id in stored if note_id not in current]
        if deleted:
            self.store.delete_note_vectors(business_id, deleted)


def build_index(store: VectorStore, embedder: Embedder, kb_dir) -> tuple[str, int, int]:
    """Embed and store one KB version folder. Returns (kb_version, chunks indexed, drafts skipped).

    Does not activate the version; call store.activate(version) when it should go live.
    """
    from .kb import chunk_entries, load_kb

    version, entries = load_kb(kb_dir)
    chunks = chunk_entries(version, entries)
    if chunks:
        # Title and section are embedded with the text, so a short passage keeps its topic.
        vectors = embedder.embed_documents([f"{c.title}\n{c.section}\n{c.text}".strip() for c in chunks])
        store.save_version(version, chunks, vectors, embedder.model)
    return version, len(chunks), sum(1 for e in entries if not e.is_verified)
