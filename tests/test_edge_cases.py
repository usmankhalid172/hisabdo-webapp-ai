import unittest
from edge_cases import run_all


class EdgeCases(unittest.TestCase):
    def test_all_cases(self):
        for r in run_all():
            with self.subTest(case=r["id"], desc=r["description"]):
                self.assertTrue(r["passed"], f"{r['id']}: expected {r['expected']} got {r['actual']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
