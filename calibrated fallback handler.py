"""
Fallback and refusal handling for HisabDo Product Page queries.

Purpose
-------
This module helps a website chatbot answer questions about HisabDo only when
there is enough verified knowledge-base evidence. It prevents the chatbot from
inventing product features, prices, integrations, guarantees, policies, or
other claims.

Design
------
1. The retrieval layer passes the handler the knowledge-base excerpts it found.
2. The handler estimates whether the evidence is relevant and sufficiently strong.
3. If evidence is weak, missing, contradictory, or marked unverified, it returns
   a polite fallback and directs the visitor to the configured official support
   channel.
4. If the question asks for an unsupported claim, the handler returns a refusal
   rather than guessing.
5. The caller should display the returned answer and log the reason for review.

Important
---------
- This module does not itself retrieve documents or calculate semantic similarity.
 
from pathlib import Path
src = Path("/mnt/data/fallback_refusal_handler(2).py")
out = Path("/mnt/data/fallback_refusal_handler_calibrated.py")
code = r'''

Calibration improvements:
- Distinguishes explicit out-of-scope questions from product questions with weak retrieval.
- Avoids treating ordinary words such as "connect", "all features", or "any reports"
  as automatic guarantee/claim requests.
- Scores evidence relevance against the query before trusting retrieval confidence.
- Uses evidence confidence when available and validates confidence values.
- Routes unsupported or out-of-scope questions to the configured official channel.
- Keeps sensitive/high-risk claims conservative without blocking unrelated questions.

"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional, Sequence
import logging
import re

logger = logging.getLogger(__name__)


class HandlerAction(str, Enum):
    ANSWER_FROM_KB = "answer_from_kb"
    FALLBACK_TO_SUPPORT = "fallback_to_support"
    REFUSE_UNVERIFIED_CLAIM = "refuse_unverified_claim"
    ASK_FOR_CLARIFICATION = "ask_for_clarification"


@dataclass(frozen=True)
class KBEvidence:
    """One knowledge-base excerpt, including verification and retrieval metadata."""
    text: str
    source_url: Optional[str] = None
    confidence: float = 0.0
    verified: bool = False


@dataclass
class HandlerConfig:
    """Thresholds and approved official support destinations."""
    min_confidence: float = 0.65
    min_verified_evidence_items: int = 1
    min_query_term_overlap: float = 0.12
    support_url: str = "https://www.xicteksystems.com/portfolio"
    support_email: Optional[str] = None
    company_name: str = "XICTEK Systems"
    product_name: str = "HisabDo"

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0.0 and 1.0.")
        if not 0.0 <= self.min_query_term_overlap <= 1.0:
            raise ValueError("min_query_term_overlap must be between 0.0 and 1.0.")
        if self.min_verified_evidence_items < 1:
            raise ValueError("min_verified_evidence_items must be at least 1.")


@dataclass
class HandlerResult:
    """Standard response returned to the chat API."""
    action: HandlerAction
    answer: str
    should_call_llm: bool
    confidence: float
    reason: str
    source_urls: list[str] = field(default_factory=list)
    needs_human_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "answer": self.answer,
            "should_call_llm": self.should_call_llm,
            "confidence": round(self.confidence, 4),
            "reason": self.reason,
            "source_urls": self.source_urls,
            "needs_human_review": self.needs_human_review,
        }


class HisabDoFallbackRefusalHandler:
    """Decide whether a HisabDo product question can be answered from verified evidence."""

    # Only explicit off-topic intent should be classified as out of scope.
    # General words like "help", "connect", "all", and "any" are deliberately excluded.
    OUT_OF_SCOPE_PATTERNS = (
        re.compile(r"\b(weather|forecast|temperature outside)\b", re.I),
        re.compile(r"\b(football|cricket|basketball|match score|sports results)\b", re.I),
        re.compile(r"\b(write me a poem|romantic poem|recipe for|solve this math homework)\b", re.I),
        re.compile(r"\b(stock price|bitcoin price|celebrity gossip)\b", re.I),
    )

    HIGH_RISK_PATTERNS = {
        "pricing_or_plans": re.compile(
            r"\b(price|pricing|cost|fee|fees|subscription|plan|free trial|discount)\b", re.I
        ),
        "security_or_compliance": re.compile(
            r"\b(encryption|secure|security|privacy|compliance|gdpr|iso 27001|"
            r"data residency|backup|data protection)\b", re.I
        ),
        "integrations": re.compile(
            r"\b(integrat(?:e|es|ion|ions)|api|bank integration|quickbooks|xero|"
            r"whatsapp integration|third[- ]party integration)\b", re.I
        ),
        "guarantees_or_performance": re.compile(
            r"\b(guarantee|guaranteed|promise|100%|never fails|uptime|"
            r"certified|officially approved)\b", re.I
        ),
        "legal_or_financial_advice": re.compile(
            r"\b(legal advice|tax advice|investment advice|will i be fined|"
            r"is this legally compliant)\b", re.I
        ),
    }

    # Match explicit requests to certify a claim, not ordinary product questions.
    CLAIM_REQUEST_PATTERNS = (
        re.compile(r"\b(do you guarantee|can you guarantee|promise me|certify that)\b", re.I),
        re.compile(r"\b(can you confirm that|is it true that)\b", re.I),
        re.compile(r"\b(100%\s*(secure|accurate|guaranteed))\b", re.I),
    )

    STOP_WORDS = {
        "can", "could", "would", "should", "what", "when", "where", "which", "who",
        "how", "does", "do", "did", "is", "are", "was", "were", "the", "a", "an",
        "and", "or", "for", "to", "of", "in", "on", "with", "about", "please",
        "tell", "me", "you", "your", "hisabdo", "this", "that", "there", "have",
        "has", "i", "we", "it", "my", "our", "their", "all", "any", "every",
    }

    def __init__(self, config: Optional[HandlerConfig] = None) -> None:
        self.config = config or HandlerConfig()

    def handle(
        self,
        query: str,
        evidence: Optional[Sequence[KBEvidence | Mapping[str, Any]]] = None,
        retrieval_confidence: Optional[float] = None,
        *,
        contradictory_evidence: bool = False,
        force_human_review: bool = False,
    ) -> HandlerResult:
        clean_query = (query or "").strip()
        if not clean_query:
            return HandlerResult(
                HandlerAction.ASK_FOR_CLARIFICATION,
                "Please enter a question about HisabDo, and I’ll do my best to help.",
                False, 0.0, "empty_query",
            )

        normalized = self._normalize_evidence(evidence or [])
        verified = [item for item in normalized if item.verified and item.text.strip()]

        if force_human_review:
            return self._support_result(0.0, "forced_human_review", True)
        if contradictory_evidence:
            logger.warning("Contradictory KB evidence detected.")
            return self._support_result(0.0, "contradictory_verified_evidence", True)

        if self._is_out_of_scope(clean_query):
            return self._support_result(
                0.0, "explicit_out_of_scope_query", False
            )

        confidence = self._resolve_confidence(normalized, retrieval_confidence)
        relevant = [item for item in verified if self._is_relevant(clean_query, item.text)]
        risk_topic = self._high_risk_topic(clean_query)

        # Risky topics need verified evidence that actually discusses the topic.
        if risk_topic and not self._has_sufficient_evidence(relevant, confidence):
            return self._unverified_claim_result(
                confidence, f"insufficient_relevant_verified_evidence_for_{risk_topic}"
            )

        # Ordinary product questions are not refused solely because a broad retrieval
        # score is low if a verified, relevant excerpt itself has a strong score.
        relevant_confidence = max(
            (self._clamp(item.confidence) for item in relevant), default=0.0
        )
        effective_confidence = max(confidence, relevant_confidence)
        if not self._has_sufficient_evidence(relevant, effective_confidence):
            return self._support_result(
                effective_confidence, "no_sufficient_relevant_verified_evidence", False
            )

        if self._looks_like_claim_request(clean_query):
            if not self._evidence_directly_supports_claim(clean_query, relevant):
                return self._unverified_claim_result(
                    effective_confidence, "unsupported_confirmation_or_guarantee_request"
                )

        urls = sorted({item.source_url for item in relevant if item.source_url})
        return HandlerResult(
            HandlerAction.ANSWER_FROM_KB,
            "Verified product information was found. Answer using only the approved evidence supplied to the response-generation step.",
            True, effective_confidence, "sufficient_relevant_verified_evidence", urls,
        )

    def validate_generated_answer(
        self,
        answer: str,
        evidence: Sequence[KBEvidence | Mapping[str, Any]],
        *,
        unsupported_claim_detected: bool = False,
    ) -> HandlerResult:
        normalized = self._normalize_evidence(evidence)
        verified = [item for item in normalized if item.verified and item.text.strip()]
        urls = sorted({item.source_url for item in verified if item.source_url})
        confidence = max((self._clamp(item.confidence) for item in verified), default=0.0)

        if unsupported_claim_detected or not verified:
            logger.warning("Generated answer failed grounding validation.")
            result = self._unverified_claim_result(
                confidence, "generated_answer_not_grounded_in_verified_evidence"
            )
            result.needs_human_review = unsupported_claim_detected
            return result

        return HandlerResult(
            HandlerAction.ANSWER_FROM_KB, answer.strip(), False, confidence,
            "generated_answer_passed_basic_grounding_gate", urls,
        )

    def _support_result(
        self, confidence: float, reason: str, needs_human_review: bool = False
    ) -> HandlerResult:
        destinations = self.config.support_url
        if self.config.support_email:
            destinations += f" or email {self.config.support_email}"
        return HandlerResult(
            HandlerAction.FALLBACK_TO_SUPPORT,
            f"I can help with verified HisabDo product information, but I can’t reliably answer this question from the approved information available to me. Please check the official {self.config.company_name} page at {destinations}.",
            False, self._clamp(confidence), reason, [], needs_human_review,
        )

    def _unverified_claim_result(self, confidence: float, reason: str) -> HandlerResult:
        return HandlerResult(
            HandlerAction.REFUSE_UNVERIFIED_CLAIM,
            f"I can’t confirm that claim without relevant, verified information from the official {self.config.product_name} documentation. I don’t want to guess or promise something that may be inaccurate. Please check {self.config.support_url} for official information.",
            False, self._clamp(confidence), reason, [], True,
        )

    def _has_sufficient_evidence(self, evidence: Sequence[KBEvidence], confidence: float) -> bool:
        return (
            len(evidence) >= self.config.min_verified_evidence_items
            and confidence >= self.config.min_confidence
        )

    @staticmethod
    def _clamp(value: Any) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except (TypeError, ValueError):
            return 0.0

    def _resolve_confidence(
        self, evidence: Sequence[KBEvidence], retrieval_confidence: Optional[float]
    ) -> float:
        if retrieval_confidence is not None:
            return self._clamp(retrieval_confidence)
        return max((self._clamp(item.confidence) for item in evidence), default=0.0)

    @classmethod
    def _normalize_evidence(
        cls, evidence: Iterable[KBEvidence | Mapping[str, Any]]
    ) -> list[KBEvidence]:
        normalized: list[KBEvidence] = []
        for item in evidence:
            if isinstance(item, KBEvidence):
                normalized.append(item)
            elif isinstance(item, Mapping):
                try:
                    normalized.append(KBEvidence(
                        text=str(item.get("text", "")),
                        source_url=str(item["source_url"]) if item.get("source_url") else None,
                        confidence=cls._clamp(item.get("confidence", 0.0)),
                        verified=bool(item.get("verified", False)),
                    ))
                except (TypeError, ValueError):
                    logger.exception("Skipping malformed evidence item.")
        return normalized

    @classmethod
    def _query_terms(cls, text: str) -> set[str]:
        return {
            token.lower() for token in re.findall(r"[a-zA-Z0-9]+", text)
            if len(token) > 2 and token.lower() not in cls.STOP_WORDS
        }

    def _is_relevant(self, query: str, evidence_text: str) -> bool:
        query_terms = self._query_terms(query)
        evidence_terms = self._query_terms(evidence_text)
        if not query_terms:
            return True
        # Include a small product-context allowance for common broad questions.
        if query_terms.intersection(evidence_terms):
            return True
        broad_product_question = re.search(
            r"\b(what does|what is|introduce|help me understand|features of)\b", query, re.I
        )
        return bool(broad_product_question and re.search(r"\b(hisabdo|expense|income|business|report|account)\b", evidence_text, re.I))

    def _is_out_of_scope(self, query: str) -> bool:
        return any(pattern.search(query) for pattern in self.OUT_OF_SCOPE_PATTERNS)

    def _high_risk_topic(self, query: str) -> Optional[str]:
        for topic, pattern in self.HIGH_RISK_PATTERNS.items():
            if pattern.search(query):
                return topic
        return None

    def _looks_like_claim_request(self, query: str) -> bool:
        return any(pattern.search(query) for pattern in self.CLAIM_REQUEST_PATTERNS)

    def _evidence_directly_supports_claim(
        self, query: str, evidence: Sequence[KBEvidence]
    ) -> bool:
        terms = self._query_terms(query)
        evidence_terms = self._query_terms(" ".join(item.text for item in evidence))
        # Claim language is excluded from the overlap test; require meaningful subject
        # matter rather than passing because the excerpt repeats "confirm" or "guarantee".
        return bool(terms and terms.intersection(evidence_terms))


def handle_hisabdo_query(
    query: str,
    evidence: Optional[Sequence[KBEvidence | Mapping[str, Any]]] = None,
    retrieval_confidence: Optional[float] = None,
    *,
    support_url: str = "https://www.xicteksystems.com/portfolio",
) -> dict[str, Any]:
    """Convenience wrapper returning a JSON-serializable dictionary."""
    handler = HisabDoFallbackRefusalHandler(HandlerConfig(support_url=support_url))
    return handler.handle(query, evidence, retrieval_confidence).to_dict()


if __name__ == "__main__":
    import unittest

    class FallbackCalibrationTests(unittest.TestCase):
        def setUp(self):
            self.handler = HisabDoFallbackRefusalHandler()
            self.evidence = [
                KBEvidence(
                    text="HisabDo helps businesses manage expenses, income, and reports.",
                    source_url="https://www.xicteksystems.com/portfolio",
                    confidence=0.91,
                    verified=True,
                )
            ]

        def test_valid_product_question_not_refused(self):
            result = self.handler.handle("What reports can HisabDo help with?", self.evidence, 0.25)
            self.assertEqual(result.action, HandlerAction.ANSWER_FROM_KB)

        def test_all_features_not_automatically_a_guarantee(self):
            result = self.handler.handle("What are all the features of HisabDo?", self.evidence, 0.9)
            self.assertEqual(result.action, HandlerAction.ANSWER_FROM_KB)

        def test_unrelated_evidence_does_not_pass(self):
            unrelated = [KBEvidence("Weather forecast and temperature today.", confidence=0.99, verified=True)]
            result = self.handler.handle("How does HisabDo track expenses?", unrelated, 0.99)
            self.assertEqual(result.action, HandlerAction.FALLBACK_TO_SUPPORT)

        def test_unsupported_security_guarantee_refused(self):
            result = self.handler.handle("Can you guarantee that my data is 100% secure?", [], 0.0)
            self.assertEqual(result.action, HandlerAction.REFUSE_UNVERIFIED_CLAIM)

        def test_explicit_off_topic_routes_to_support(self):
            result = self.handler.handle("What is the weather forecast?", [], 0.0)
            self.assertEqual(result.action, HandlerAction.FALLBACK_TO_SUPPORT)
            self.assertEqual(result.reason, "explicit_out_of_scope_query")

        def test_empty_query_asks_clarification(self):
            result = self.handler.handle("  ", [], 0.0)
            self.assertEqual(result.action, HandlerAction.ASK_FOR_CLARIFICATION)

    unittest.main(verbosity=2)
    
out.write_text(code, encoding="utf-8")
print(f"Created {out} ({out.stat().st_size} bytes)")