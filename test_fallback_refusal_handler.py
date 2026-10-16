"""Regression tests for the HisabDo fallback/refusal handler.

Run with: python -m unittest -v test_fallback_refusal_handler.py
These tests use synthetic, explicitly verified sample evidence; they do not
represent a live website chatbot test or independently verify the Product Page.
"""
import unittest
from fallback_refusal_handler import (
    HandlerAction,
    HisabDoFallbackRefusalHandler,
    KBEvidence,
)


class TestHisabDoFallbackRefusalHandler(unittest.TestCase):
    def setUp(self):
        self.handler = HisabDoFallbackRefusalHandler()
        self.verified_evidence = [KBEvidence(
            text=("HisabDo is a business assistant that helps users manage "
                  "business records and view reports."),
            source_url="https://www.xicteksystems.com/portfolio",
            confidence=0.91,
            verified=True,
        )]

    def check_action(self, query, evidence, confidence, expected, **kwargs):
        result = self.handler.handle(
            query, evidence, confidence, **kwargs
        )
        self.assertEqual(result.action, expected, msg=f"Query: {query}; reason={result.reason}")
        return result

    def test_01_greeting_with_verified_context(self):
        self.check_action("Hi! Can you introduce yourself and explain how you can help me?", self.verified_evidence, .91, HandlerAction.ANSWER_FROM_KB)

    def test_02_product_purpose_with_verified_context(self):
        self.check_action("What is HisabDo?", self.verified_evidence, .91, HandlerAction.ANSWER_FROM_KB)

    def test_03_business_records_with_verified_context(self):
        self.check_action("Can HisabDo help manage business records?", self.verified_evidence, .90, HandlerAction.ANSWER_FROM_KB)

    def test_04_reports_with_verified_context(self):
        self.check_action("Can I view reports in HisabDo?", self.verified_evidence, .90, HandlerAction.ANSWER_FROM_KB)

    def test_05_unknown_monthly_pricing_refused(self):
        self.check_action("How much does HisabDo cost per month?", [], .20, HandlerAction.REFUSE_UNVERIFIED_CLAIM)

    def test_06_free_forever_claim_refused(self):
        self.check_action("Is HisabDo completely free forever?", [], .18, HandlerAction.REFUSE_UNVERIFIED_CLAIM)

    def test_07_all_bank_integrations_claim_refused(self):
        self.check_action("Does HisabDo integrate with every bank?", [], .12, HandlerAction.REFUSE_UNVERIFIED_CLAIM)

    def test_08_whatsapp_integration_unverified_refused(self):
        self.check_action("Can I connect HisabDo to WhatsApp?", [], .25, HandlerAction.REFUSE_UNVERIFIED_CLAIM)

    def test_09_security_guarantee_refused(self):
        self.check_action("Can you guarantee my data is 100% secure?", [], .10, HandlerAction.REFUSE_UNVERIFIED_CLAIM)

    def test_10_certification_claim_refused(self):
        self.check_action("Is HisabDo ISO 27001 certified?", [], .10, HandlerAction.REFUSE_UNVERIFIED_CLAIM)

    def test_11_tax_claim_refused(self):
        self.check_action("Will HisabDo calculate my taxes legally and accurately?", [], .15, HandlerAction.REFUSE_UNVERIFIED_CLAIM)

    def test_12_payroll_unknown_falls_back(self):
        self.check_action("Does HisabDo include payroll and HR automation?", [], .25, HandlerAction.FALLBACK_TO_SUPPORT)

    def test_13_inventory_unknown_falls_back(self):
        self.check_action("Does it support barcode scanning and inventory tracking?", [], .22, HandlerAction.FALLBACK_TO_SUPPORT)

    def test_14_mobile_app_unknown_falls_back(self):
        self.check_action("Is there an Android and iOS app?", [], .20, HandlerAction.FALLBACK_TO_SUPPORT)

    def test_15_medical_question_out_of_scope(self):
        self.check_action("Can you diagnose my headache?", [], .05, HandlerAction.FALLBACK_TO_SUPPORT)

    def test_16_unrelated_trivia_out_of_scope(self):
        self.check_action("Who won the last FIFA World Cup?", [], .05, HandlerAction.FALLBACK_TO_SUPPORT)

    def test_17_political_question_out_of_scope(self):
        self.check_action("Which political party should I vote for?", [], .03, HandlerAction.FALLBACK_TO_SUPPORT)

    def test_18_empty_query_asks_for_clarification(self):
        self.check_action("   ", [], 0.0, HandlerAction.ASK_FOR_CLARIFICATION)

    def test_19_contradictory_sources_fall_back(self):
        self.check_action("Does HisabDo support this feature?", self.verified_evidence, .91, HandlerAction.FALLBACK_TO_SUPPORT, contradictory_evidence=True)

    def test_20_forced_human_review_falls_back(self):
        result = self.check_action("Please review this account issue.", self.verified_evidence, .91, HandlerAction.FALLBACK_TO_SUPPORT, force_human_review=True)
        self.assertTrue(result.needs_human_review)

    def test_21_unsupported_guarantee_not_accepted_from_generic_evidence(self):
        self.check_action("Can you guarantee HisabDo never fails?", self.verified_evidence, .91, HandlerAction.REFUSE_UNVERIFIED_CLAIM)

    def test_22_unverified_evidence_is_not_enough(self):
        unverified = [KBEvidence(text="HisabDo supports every bank.", confidence=.99, verified=False)]
        self.check_action("Does HisabDo integrate with every bank?", unverified, .99, HandlerAction.REFUSE_UNVERIFIED_CLAIM)


if __name__ == "__main__":
    unittest.main(verbosity=2)
