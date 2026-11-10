"""Vector storage for the knowledge base and for notes, in the app's SQLite database.

KB chunks are stored per kb_version, and exactly one version is "active".
Building a new version never touches the active one, so:
  * a half-built index is never served, and
  * rolling back is one command (activate the previous version).

For a few thousand chunks a full scan with a dot product is fast enough. When
the KB outgrows that, swap this class for pgvector in Supabase; nothing else changes.
"""

from __future__ import annotations

import hashlib
from array import array

from .embeddings import cosine
from .kb import KBChunk
from .repository import Repository

SCHEMA = """
CREATE TABLE IF NOT EXISTS kb_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kb_version TEXT NOT NULL, entry_id TEXT NOT NULL, chunk_no INTEGER NOT NULL,
    title TEXT NOT NULL, section TEXT NOT NULL DEFAULT '', text TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT '', model TEXT NOT NULL, embedding BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_kb_chunks_version ON kb_chunks(kb_version);
CREATE TABLE IF NOT EXISTS kb_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS note_vectors (
    note_id TEXT PRIMARY KEY, business_id TEXT NOT NULL, content_hash TEXT NOT NULL,
    model TEXT NOT NULL, embedding BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_note_vectors_biz ON note_vectors(business_id);
"""


def _pack(vector: list[float]) -> bytes:
    return array("f", vector).tobytes()


def _unpack(blob: bytes) -> list[float]:
    values = array("f")
    values.frombytes(blob)
    return values.tolist()


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class VectorStore:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        with repo.connect() as conn:
            conn.executescript(SCHEMA)

    # --- knowledge base ---------------------------------------------------------------

    def save_version(self, kb_version: str, chunks: list[KBChunk], vectors: list[list[float]], model: str) -> None:
        """Store (or rebuild) one KB version. Does NOT make it active."""
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")
        with self.repo.connect() as conn:
            conn.execute("DELETE FROM kb_chunks WHERE kb_version = ?", (kb_version,))
            conn.executemany(
                "INSERT INTO kb_chunks (kb_version, entry_id, chunk_no, title, section, text, source, model, embedding)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [(kb_version, c.entry_id, c.chunk_no, c.title, c.section, c.text, c.source, model, _pack(v))
                 for c, v in zip(chunks, vectors)],
            )

    def versions(self) -> dict[str, int]:
        with self.repo.connect() as conn:
            rows = conn.execute("SELECT kb_version, COUNT(*) AS n FROM kb_chunks GROUP BY kb_version").fetchall()
        return {r["kb_version"]: r["n"] for r in rows}

    def activate(self, kb_version: str) -> None:
        if kb_version not in self.versions():
            raise ValueError(f"KB version {kb_version!r} has not been indexed")
        with self.repo.connect() as conn:
            conn.execute(
                "INSERT INTO kb_meta (key, value) VALUES ('active_version', ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value", (kb_version,),
            )

    def active_version(self) -> str | None:
        with self.repo.connect() as conn:
            row = conn.execute("SELECT value FROM kb_meta WHERE key = 'active_version'").fetchone()
        return row["value"] if row else None

    def active_model(self) -> str | None:
        version = self.active_version()
        if version is None:
            return None
        with self.repo.connect() as conn:
            row = conn.execute("SELECT model FROM kb_chunks WHERE kb_version = ? LIMIT 1", (version,)).fetchone()
        return row["model"] if row else None

    def search(self, query_vector: list[float], top_k: int) -> list[tuple[KBChunk, float]]:
        """The top_k chunks of the ACTIVE version, most similar first, with their scores."""
        version = self.active_version()
        if version is None:
            return []
        with self.repo.connect() as conn:
            rows = conn.execute("SELECT * FROM kb_chunks WHERE kb_version = ?", (version,)).fetchall()
        scored = [
            (KBChunk(r["entry_id"], r["chunk_no"], r["title"], r["section"], r["text"], r["source"], r["kb_version"]),
             cosine(query_vector, _unpack(r["embedding"])))
            for r in rows
        ]
        scored.sort(key=lambda cs: cs[1], reverse=True)
        return scored[:top_k]

    # --- note vectors (always scoped to one business) -----------------------------------

    def note_hashes(self, business_id: str, model: str) -> dict[str, str]:
        with self.repo.connect() as conn:
            rows = conn.execute(
                "SELECT note_id, content_hash FROM note_vectors WHERE business_id = ? AND model = ?", (business_id, model)
            ).fetchall()
        return {r["note_id"]: r["content_hash"] for r in rows}

    def save_note_vectors(self, business_id: str, model: str, items: list[tuple[str, str, list[float]]]) -> None:
        """items = [(note_id, content_hash, vector)]"""
        with self.repo.connect() as conn:
            conn.executemany(
                "INSERT INTO note_vectors (note_id, business_id, content_hash, model, embedding) VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT(note_id) DO UPDATE SET business_id = excluded.business_id,"
                " content_hash = excluded.content_hash, model = excluded.model, embedding = excluded.embedding",
                [(note_id, business_id, h, model, _pack(v)) for note_id, h, v in items],
            )

    def delete_note_vectors(self, business_id: str, note_ids: list[str]) -> None:
        with self.repo.connect() as conn:
            conn.executemany(
                "DELETE FROM note_vectors WHERE business_id = ? AND note_id = ?", [(business_id, n) for n in note_ids]
            )

    def note_vectors(self, business_id: str, model: str) -> dict[str, list[float]]:
        with self.repo.connect() as conn:
            rows = conn.execute(
                "SELECT note_id, embedding FROM note_vectors WHERE business_id = ? AND model = ?", (business_id, model)
            ).fetchall()
        return {r["note_id"]: _unpack(r["embedding"]) for r in rows}
