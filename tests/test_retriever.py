"""Test RAG retrieval and financial computations."""

from __future__ import annotations

import unittest

from src.financial_assistant import knowledge_base as kb
from src.financial_assistant import retriever
from src.financial_assistant import transactions as tr


class KnowledgeBaseTests(unittest.TestCase):

    def setUp(self):
        self.chunks = kb.load_knowledge_base()

    def test_chunks_loaded(self):
        self.assertGreater(len(self.chunks), 3)

    def test_each_chunk_has_title_and_text(self):
        for chunk in self.chunks:
            self.assertTrue(chunk.title)
            self.assertTrue(chunk.text)

    def test_tags_present(self):
        titles = {chunk.title for chunk in self.chunks}
        self.assertIn("Budgeting to save money", titles)


class RetrieverTests(unittest.TestCase):

    def setUp(self):
        self.chunks = kb.load_knowledge_base()

    def test_cooking_query_top_result(self):
        results = retriever.retrieve("how can I save money", self.chunks, top_k=3)
        self.assertGreater(len(results), 0)
        self.assertTrue(results[0].score > 0)

    def test_empty_result_for_unrelated(self):
        results = retriever.retrieve("which movie won the oscar", self.chunks)
        # Irrelevant queries should return few/no chunks (min_score threshold).
        self.assertLessEqual(len(results), 1)


class ComputationTests(unittest.TestCase):

    def setUp(self):
        self.txns = tr.load_transactions()

    def test_total_july(self):
        total = tr.total_for_period(self.txns, "2026-07")
        self.assertGreater(total, 0)
        self.assertEqual(round(total, 2), total)

    def test_highest_category_july_is_groceries(self):
        top = tr.highest_category_for_period(self.txns, "2026-07")
        self.assertEqual(top["category"], "Groceries")

    def test_summary_structure(self):
        s = tr.summary_for_period(self.txns, "2026-07")
        self.assertIn("total", s)
        self.assertIn("categories", s)
        self.assertEqual(s["total"], sum(s["categories"].values()))

    def test_monthly_series(self):
        series = tr.monthly_series(self.txns)
        self.assertIn("2026-07", series)
        self.assertIn("2026-08", series)


if __name__ == "__main__":
    unittest.main()