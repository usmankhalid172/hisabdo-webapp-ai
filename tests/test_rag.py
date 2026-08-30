"""Tests for the RAG retriever layer (rag.py)."""

from __future__ import annotations

import unittest

from src.financial_assistant.knowledge_base import Chunk
from src.financial_assistant.rag import (
    BaseRetriever,
    KeywordRetriever,
    RetrievedChunk,
    VectorRetriever,
    build_default_retriever,
)


def _chunks():
    return [
        Chunk(index=0, title="Saving Tip 1", text="Automate your savings each month.", tags=["savings"]),
        Chunk(index=1, title="Budgeting", text="Track your expenses to control spending.", tags=["budget"]),
        Chunk(index=2, title="Investments", text="Diversify your portfolio over time.", tags=["invest"]),
    ]


class RetrieverTests(unittest.TestCase):

    def test_keyword_retriever_returns_relevant_chunks(self):
        retriever = KeywordRetriever(_chunks())
        results = retriever.retrieve("how to save money", top_k=3)
        self.assertEqual(len(results), 3)
        self.assertIsInstance(results[0], RetrievedChunk)
        self.assertGreater(results[0].score, 0)
        # Results must be ranked descending by score.
        scores = [r.score for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))
        # The "Investments" chunk shares no query terms and ranks last.
        self.assertEqual(results[-1].chunk.index, 2)

    def test_keyword_retriever_empty_corpus(self):
        retriever = KeywordRetriever([])
        self.assertEqual(retriever.retrieve("anything", top_k=3), [])

    def test_build_default_retriever_returns_keyword(self):
        retriever = build_default_retriever(_chunks())
        self.assertIsInstance(retriever, KeywordRetriever)
        self.assertIsInstance(retriever, BaseRetriever)

    def test_vector_retriever_ranks_by_cosine(self):
        # Embeddings: chunk 0 matches the query better than chunk 2.
        embed = lambda texts: [[1.0, 0.0] if "save" in t.lower() else [0.0, 1.0] for t in texts]
        retriever = VectorRetriever(_chunks(), embed)
        results = retriever.retrieve("save money", top_k=3)
        self.assertEqual(results[0].chunk.index, 0)
        self.assertEqual(results[-1].chunk.index, 2)

    def test_vector_retriever_empty_corpus(self):
        embed = lambda texts: []
        retriever = VectorRetriever([], embed)
        self.assertEqual(retriever.retrieve("x", top_k=3), [])


if __name__ == "__main__":
    unittest.main()
