"""
HisabDo AI Financial Assistant — vector store retrieval over transaction history.

Owner: Muhammad Hamza Nawaz
Day: 25 — RAG Context Pipeline Setup (wire up vector database retrieval)

Scope of this module:
    - Provide an actual, working retrieval mechanism (Day 23-24's
      `rag_pipeline.py` deliberately accepted context from *any* retriever
      via the `ContextChunk` contract, but didn't implement one — this
      module is that implementation).
    - Store and query transaction-shaped records by semantic-ish similarity
      (bag-of-words term-frequency cosine similarity — no external vector
      DB or embeddings API available in this environment, so this is a
      dependency-free stand-in with the same query/retrieve interface a
      real vector DB would have).
    - Produce results already shaped as `rag_pipeline.ContextChunk`, so it
      plugs into the Day 23-24 pipeline with zero changes there.

This module does NOT:
    - Replace or compete with Ahmed's / Faiza's retriever implementations
      — this is a working demo/reference retriever built specifically to
      exercise the Day 23-24 pipeline end-to-end with real (if synthetic)
      transaction data, not a claim that this is "the" canonical retriever.
      Swapping in a real vector DB (pgvector, FAISS, Pinecone, etc.) later
      means replacing `InMemoryTransactionVectorStore.query()`'s internals
      only — every other consumer of it stays the same, since it returns
      the same `ContextChunk` shape either way.
    - Persist data — in-memory only, rebuilt from whatever transactions are
      indexed at process start. Persistence is a backend/integration
      concern (Ahmed Ali / Niha Batool / Zainab Raza's Day 23-24 lane).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, List, Optional

from .rag_pipeline import ContextChunk

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return _TOKEN_RE.findall(text.lower())


def _term_frequencies(tokens: Iterable[str]) -> Counter:
    return Counter(tokens)


def _cosine_similarity(a: Counter, b: Counter) -> float:
    if not a or not b:
        return 0.0
    shared_terms = set(a) & set(b)
    dot_product = sum(a[t] * b[t] for t in shared_terms)
    magnitude_a = math.sqrt(sum(v * v for v in a.values()))
    magnitude_b = math.sqrt(sum(v * v for v in b.values()))
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)


@dataclass
class Transaction:
    """
    A single transaction record. Field names/shape are a reasonable
    guess at what the actual app's transaction schema looks like — this
    is the piece to reconcile with the real schema once backend
    integration (Niha's service layer) defines one.
    """

    transaction_id: str
    date: str  # ISO date string, e.g. "2026-08-15"
    amount: float
    category: str
    merchant: str
    note: str = ""

    def to_retrievable_text(self) -> str:
        """
        Renders this transaction as text for indexing/matching. Kept as a
        single method so the "how a transaction becomes searchable text"
        decision lives in one place.
        """
        parts = [self.category, self.merchant]
        if self.note:
            parts.append(self.note)
        return " ".join(parts)

    def to_display_text(self) -> str:
        """
        Renders this transaction as a compact, consistently formatted
        line for use inside a retrieved context chunk — this is the
        "correctly formats transaction histories" requirement from the
        Day 25/26 task description.
        """
        return f"{self.date}: {self.merchant} — Rs. {self.amount:,.2f} ({self.category})"


@dataclass
class TransactionVectorStore:
    """
    A dependency-free, in-memory "vector store" over transactions, using
    bag-of-words term-frequency cosine similarity in place of real
    embeddings. Interface (`add`, `query`) mirrors what a real vector DB
    client call would look like, so this class is a drop-in placeholder,
    not a permanent architecture decision.
    """

    _records: List[Transaction] = field(default_factory=list)
    _vectors: List[Counter] = field(default_factory=list)

    def add(self, transaction: Transaction) -> None:
        self._records.append(transaction)
        self._vectors.append(_term_frequencies(_tokenize(transaction.to_retrievable_text())))

    def add_many(self, transactions: Iterable[Transaction]) -> None:
        for txn in transactions:
            self.add(txn)

    def query(self, query_text: str, top_k: int = 5) -> List[ContextChunk]:
        """
        Returns the top_k most similar transactions to `query_text`,
        already shaped as ContextChunk objects (source="transaction_history",
        score=cosine similarity) ready to hand to
        `rag_pipeline.prepare_context()` / `get_grounded_financial_assistant_response()`.
        """
        if not self._records:
            return []

        query_vector = _term_frequencies(_tokenize(query_text))
        scored: List[tuple] = []
        for record, vector in zip(self._records, self._vectors):
            score = _cosine_similarity(query_vector, vector)
            if score > 0:
                scored.append((score, record))

        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [
            ContextChunk(
                text=record.to_display_text(),
                source="transaction_history",
                score=score,
            )
            for score, record in scored[:top_k]
        ]

    def __len__(self) -> int:
        return len(self._records)


def build_sample_transaction_store() -> TransactionVectorStore:
    """
    Builds a store populated with sample/demo transaction data — clearly
    synthetic, used only to verify the retrieval pipeline works
    end-to-end. Not real user data; no real transaction source is wired
    in yet (that's backend/integration scope).
    """
    store = TransactionVectorStore()
    store.add_many([
        Transaction("t1", "2026-08-01", 4500.00, "groceries", "Al-Fatah", "monthly grocery run"),
        Transaction("t2", "2026-08-03", 1200.00, "transport", "Careem", "ride to office"),
        Transaction("t3", "2026-08-05", 8000.00, "rent", "Landlord", "August rent"),
        Transaction("t4", "2026-08-07", 650.00, "groceries", "Imtiaz", "snacks and milk"),
        Transaction("t5", "2026-08-10", 2200.00, "utilities", "K-Electric", "electricity bill"),
        Transaction("t6", "2026-08-12", 900.00, "transport", "Careem", "airport pickup"),
        Transaction("t7", "2026-08-15", 3000.00, "dining", "KFC", "family dinner"),
        Transaction("t8", "2026-08-18", 1500.00, "groceries", "Al-Fatah", "weekly grocery run"),
        Transaction("t9", "2026-08-20", 500.00, "entertainment", "Cinepax", "movie tickets"),
        Transaction("t10", "2026-08-22", 1800.00, "utilities", "PTCL", "internet bill"),
    ])
    return store