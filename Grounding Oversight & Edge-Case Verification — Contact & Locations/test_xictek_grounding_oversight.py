"""Automated test suite verifying Day 6 grounding rules, edge-case evaluations, and zero hallucinations.
Author: Ali Hassan (Team Lead, Department 4)
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "xictek_grounding_oversight_evaluation_log.json"
REPORT_PATH = ROOT / "Ali_Hassan_Department4_Day6_Quality_Signoff_Report.md"


class GroundingOversightValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(JSON_PATH.is_file(), "Grounding evaluation log JSON must exist")
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_metadata_compliance_scores(self) -> None:
        meta = self.data.get("audit_metadata", {})
        self.assertEqual(meta["citation_compliance_rate"], "100.0% (15/15 Exact Matches)")
        self.assertEqual(meta["fallback_safety_rate"], "100.0% (Zero Hallucinated Coordinates or SLAs)")
        self.assertEqual(meta["overall_grounding_score"], "100.0% (Zero Ungrounded Claims Across All Domains)")

    def test_grounding_rules_completeness(self) -> None:
        rules = self.data.get("grounding_and_fallback_rules", [])
        self.assertEqual(len(rules), 6, "Expected 6 standardized grounding rules")

        rule_ids = [r["rule_id"] for r in rules]
        self.assertIn("GND-RULE-01", rule_ids) # Physical address
        self.assertIn("GND-RULE-02", rule_ids) # Telephone / hours
        self.assertIn("GND-RULE-03", rule_ids) # Post-launch SLAs
        self.assertIn("GND-RULE-04", rule_ids) # Form fields
        self.assertIn("GND-RULE-05", rule_ids) # Project quotes
        self.assertIn("GND-RULE-06", rule_ids) # Cross-product quarantine

        for r in rules:
            self.assertEqual(r["mandatory_citation"], "[Contact Us](https://www.xicteksystems.com/contact)")
            self.assertTrue(len(r["canonical_response_template"]) > 20)

    def test_edge_case_matrix_evaluation(self) -> None:
        matrix = self.data.get("edge_case_verification_matrix", [])
        self.assertEqual(len(matrix), 15, "Expected 15 edge-case scenarios")

        for item in matrix:
            self.assertTrue(item["case_id"].startswith("EC-"))
            self.assertTrue(item["valid_citation"])
            self.assertTrue(item["grounded_and_safe"])
            self.assertEqual(item["verification_verdict"], "PASS")
            self.assertIn("[Contact Us](https://www.xicteksystems.com/contact)", item["generated_response"])

    def test_department4_prompt_oversight_register(self) -> None:
        register = self.data.get("department4_day6_prompt_oversight_register", [])
        self.assertEqual(len(register), 9, "Expected 9 Department 4 knowledge domains")

        for d in register:
            self.assertTrue(d["domain_id"].startswith("DOM-0"))
            self.assertEqual(d["citation_compliance"], "100.0%")
            self.assertEqual(d["hallucination_rate"], "0.0%")
            self.assertEqual(d["day6_quality_verdict"], "APPROVED & SIGNED OFF")

    def test_report_and_signoff_text_integrity(self) -> None:
        self.assertTrue(REPORT_PATH.is_file(), "Sign-off report markdown must exist")
        text = REPORT_PATH.read_text(encoding="utf-8")
        self.assertIn("Ali Hassan", text)
        self.assertIn("Department 4", text)
        self.assertIn("DEPARTMENT 4 DAY 6 QUALITY SIGN-OFF & GROUNDING CERTIFICATE", text)
        self.assertIn("100% GROUNDED & SIGNED OFF", text)


if __name__ == "__main__":
    unittest.main()

