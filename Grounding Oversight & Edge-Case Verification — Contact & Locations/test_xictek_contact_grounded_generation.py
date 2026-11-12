import json
import unittest

from xictek_contact_grounded_generation import (
    OFFICIAL_CONTACT_URL,
    audit_response,
    build_grounded_response,
    run_grounded_generation_suite,
)

class GroundedGenerationAndCitationsTests(unittest.TestCase):
    def test_all_15_queries_meet_100_percent_grounding_compliance(self) -> None:
        summary = run_grounded_generation_suite()                  
        self.assertEqual(summary["total_queries"], 15)
        self.assertEqual(summary["citation_accuracy"], 1.0)
        self.assertEqual(summary["fallback_safety_rate"], 1.0)
        self.assertEqual(summary["overall_grounding_compliance"], 1.0)

    def test_citation_url_matches_official_contact_page(self) -> None:
        summary = run_grounded_generation_suite()
        for item in summary["results"]:
            self.assertTrue(item["has_valid_citation"])
            self.assertEqual(item["citation_url"], OFFICIAL_CONTACT_URL)

    def test_office_location_triggers_explicit_fallback(self) -> None:
        doc = {
            "id": "office_location",
            "title": "Office address and location",
            "text": "The reviewed official Contact page text does not publish a verifiable office address, city, country, map, or visitor access details.",
        }
        text, requires_fallback = build_grounded_response("Q06", doc)
        self.assertTrue(requires_fallback)
        self.assertIn("does not publish", text.casefold())
        self.assertNotIn("street", text.casefold().replace("does not publish a physical street address", ""))

        has_cite, cite_url, passes_audit = audit_response("Q06", text, requires_fallback)
        self.assertTrue(has_cite)
        self.assertEqual(cite_url, OFFICIAL_CONTACT_URL)
        self.assertTrue(passes_audit)

    def test_office_hours_and_phone_triggers_fallback(self) -> None:
        doc = {
            "id": "office_hours_phone",
            "title": "Office hours and telephone",
            "text": "The reviewed official Contact page text does not state office hours or a telephone number.",
        }
        text, requires_fallback = build_grounded_response("Q08", doc)
        self.assertTrue(requires_fallback)
        self.assertIn("does not state office opening hours", text)

        has_cite, cite_url, passes_audit = audit_response("Q08", text, requires_fallback)
        self.assertTrue(has_cite)
        self.assertTrue(passes_audit)

    def test_support_sla_unverified_triggers_fallback(self) -> None:
        doc = {
            "id": "post_launch_support",
            "title": "Post-launch maintenance and support",
            "text": "Ongoing maintenance is offered, but SLA is not published.",
        }
        text, requires_fallback = build_grounded_response("Q12", doc)
        self.assertTrue(requires_fallback)
        self.assertIn("does not publish specific support hours", text)

        has_cite, cite_url, passes_audit = audit_response("Q12", text, requires_fallback)
        self.assertTrue(has_cite)
        self.assertTrue(passes_audit)

    def test_verified_project_inquiries_grounded_without_fallback(self) -> None:
        doc = {
            "id": "contact_general",
            "title": "General project and business inquiries",
            "text": "XICTEK Systems invites visitors to contact the company about a project.",
        }
        text, requires_fallback = build_grounded_response("Q01", doc)
        self.assertFalse(requires_fallback)
        self.assertIn(OFFICIAL_CONTACT_URL, text)

if __name__ == "__main__":
    unittest.main()