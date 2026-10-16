"""
fallback_refusal_handler.py

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
  Pass a confidence score from your retrieval/reranking layer.
- Do not set a high confidence score merely because a document was retrieved.
  Confidence should reflect relevance and the quality of the source.
- Replace the support URL/email below with the exact official contact details
  approved by your organization before deployment.
- This is a rule-based safety layer, not a substitute for testing and monitoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping, Optional, Sequence
import logging
import re


logger = logging.getLogger(__name__)


class HandlerAction(str, Enum):
    """Action the chat backend should take for a query."""

    ANSWER_FROM_KB = "answer_from_kb"
    FALLBACK_TO_SUPPORT = "fallback_to_support"
    REFUSE_UNVERIFIED_CLAIM = "refuse_unverified_claim"
    ASK_FOR_CLARIFICATION = "ask_for_clarification"


@dataclass(frozen=True)
class KBEvidence:
    """
    One retrieved knowledge-base result.

    Attributes:
        text: Relevant text excerpt from a verified source.
        source_url: URL or identifier for the source document.
        confidence: Relevance score from the retrieval/reranking layer, 0.0-1.0.
        verified: Whether the source has been approved as an authoritative source.
    """

    text: str
    source_url: Optional[str] = None
    confidence: float = 0.0
    verified: bool = False


@dataclass
class HandlerConfig:
    """Configurable thresholds and approved support destinations."""

    min_confidence: float = 0.72
    min_verified_evidence_items: int = 1
    support_url: str = "https://www.xicteksystems.com/portfolio"
    support_email: Optional[str] = None
    company_name: str = "XICTEK Systems"
    product_name: str = "HisabDo"

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0.0 and 1.0.")
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
        """Convert the result to a JSON-serializable dictionary."""
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
    """
    Rule-based fallback/refusal handler for HisabDo Product Page questions.

    Typical use:
        handler = HisabDoFallbackRefusalHandler()
        result = handler.handle(
            query="Does HisabDo integrate with every bank?",
            evidence=[],
            retrieval_confidence=0.18,
        )
        print(result.to_dict())

    Integration rule:
        - If action == ANSWER_FROM_KB, allow the answer-generation step to use
          only the supplied verified evidence.
        - For all other actions, return result.answer directly and do not ask
          the language model to invent an answer.
    """

    # Questions about these topics need direct, explicit evidence.
    HIGH_RISK_PATTERNS = {
        "pricing_or_plans": re.compile(
            r"\b(price|pricing|cost|fee|fees|subscription|plan|free|discount)\b",
            re.IGNORECASE,
        ),
        "security_or_compliance": re.compile(
            r"\b(encryption|secure|security|privacy|compliance|gdpr|iso 27001|"
            r"data residency|backup|data protection)\b",
            re.IGNORECASE,
        ),
        "integrations": re.compile(
            r"\b(integrat(?:e|es|ion|ions)|connect(?:s|ion)?|api|bank|"
            r"third[- ]party|whatsapp|quickbooks|xero)\b",
            re.IGNORECASE,
        ),
        "guarantees_or_performance": re.compile(
            r"\b(guarantee|guaranteed|100%|always|never fails|uptime|"
            r"accuracy|certified|officially approved)\b",
            re.IGNORECASE,
        ),
        "legal_or_financial_advice": re.compile(
            r"\b(legal advice|tax(?:es)?|investment advice|will i be fined|"
            r"is this legally compliant)\b",
            re.IGNORECASE,
        ),
    }

    # Phrases that often indicate a user is trying to get the bot to assert
    # something not necessarily supported by the official product material.
    CLAIM_REQUEST_PATTERNS = (
        re.compile(r"\b(confirm|guarantee|promise|prove|certify|assure)\b", re.I),
        re.compile(r"\b(is it true that|can you confirm that|do you guarantee)\b", re.I),
        re.compile(r"\b(every|all|any|always|never|100%)\b", re.I),
    )

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
        """
        Decide whether a query can safely proceed to answer generation.

        Args:
            query: Visitor's question.
            evidence: Retrieved KB excerpts. Mapping items may use keys:
                text, source_url, confidence, verified.
            retrieval_confidence: Overall retrieval confidence (0.0-1.0).
                If omitted, the maximum evidence confidence is used.
            contradictory_evidence: Set True when retrieved verified sources
                conflict with each other.
            force_human_review: Set True for issues your backend policy routes
                to a person.

        Returns:
            HandlerResult with a safe response and action decision.
        """
        clean_query = (query or "").strip()
        if not clean_query:
            return HandlerResult(
                action=HandlerAction.ASK_FOR_CLARIFICATION,
                answer="Please enter a question about HisabDo, and I’ll do my best to help.",
                should_call_llm=False,
                confidence=0.0,
                reason="empty_query",
            )

        normalized_evidence = self._normalize_evidence(evidence or [])
        verified_evidence = [
            item for item in normalized_evidence
            if item.verified and item.text.strip()
        ]

        if force_human_review:
            return self._support_result(
                confidence=0.0,
                reason="forced_human_review",
                needs_human_review=True,
            )

        if contradictory_evidence:
            logger.warning("Contradictory KB evidence detected for query: %s", clean_query)
            return self._support_result(
                confidence=0.0,
                reason="contradictory_verified_evidence",
                needs_human_review=True,
            )

        confidence = self._resolve_confidence(
            normalized_evidence, retrieval_confidence
        )

        # High-risk questions require verified, directly relevant evidence.
        risk_topic = self._high_risk_topic(clean_query)
        if risk_topic and not self._has_sufficient_verified_evidence(
            verified_evidence, confidence
        ):
            return self._unverified_claim_result(
                confidence=confidence,
                reason=f"insufficient_verified_evidence_for_{risk_topic}",
            )

        # Any question without sufficient verified evidence should not be guessed.
        if not self._has_sufficient_verified_evidence(verified_evidence, confidence):
            return self._support_result(
                confidence=confidence,
                reason="low_confidence_or_no_verified_evidence",
            )

        # If the question explicitly requests a guarantee/confirmation, require
        # a verified excerpt that directly supports the claim. A generic excerpt
        # is not enough. The retrieval layer should provide relevant excerpts.
        if self._looks_like_claim_request(clean_query):
            if not self._evidence_directly_supports_claim(clean_query, verified_evidence):
                return self._unverified_claim_result(
                    confidence=confidence,
                    reason="unsupported_confirmation_or_guarantee_request",
                )

        source_urls = sorted({
            item.source_url for item in verified_evidence if item.source_url
        })
        return HandlerResult(
            action=HandlerAction.ANSWER_FROM_KB,
            answer=(
                "Verified product information was found. Answer using only the "
                "approved evidence supplied to the response-generation step."
            ),
            should_call_llm=True,
            confidence=confidence,
            reason="sufficient_verified_evidence",
            source_urls=source_urls,
        )

    def validate_generated_answer(
        self,
        answer: str,
        evidence: Sequence[KBEvidence | Mapping[str, Any]],
        *,
        unsupported_claim_detected: bool = False,
    ) -> HandlerResult:
        """
        Optional post-generation guard.

        Call this after the LLM drafts an answer. Your grounding/evaluation
        layer should set unsupported_claim_detected=True if the answer contains
        claims not supported by the retrieved evidence. This method cannot
        independently prove semantic entailment.
        """
        normalized_evidence = self._normalize_evidence(evidence)
        verified = [item for item in normalized_evidence if item.verified and item.text.strip()]
        source_urls = sorted({item.source_url for item in verified if item.source_url})

        if unsupported_claim_detected or not verified:
            logger.warning("Generated answer failed grounding validation.")
            result = self._unverified_claim_result(
                confidence=max((e.confidence for e in verified), default=0.0),
                reason="generated_answer_not_grounded_in_verified_evidence",
            )
            result.needs_human_review = unsupported_claim_detected
            return result

        return HandlerResult(
            action=HandlerAction.ANSWER_FROM_KB,
            answer=answer.strip(),
            should_call_llm=False,
            confidence=max((e.confidence for e in verified), default=0.0),
            reason="generated_answer_passed_basic_grounding_gate",
            source_urls=source_urls,
        )

    def _support_result(
        self,
        *,
        confidence: float,
        reason: str,
        needs_human_review: bool = False,
    ) -> HandlerResult:
        support = self.config.support_url
        if self.config.support_email:
            support += f" or email {self.config.support_email}"

        return HandlerResult(
            action=HandlerAction.FALLBACK_TO_SUPPORT,
            answer=(
                f"I’m sorry, but I can’t verify that detail from the approved "
                f"{self.config.product_name} information available to me. "
                f"To avoid giving you incorrect information, please check the "
                f"official {self.config.company_name} page at {self.config.support_url}"
                + (
                    f" or contact {self.config.support_email}"
                    if self.config.support_email else ""
                )
                + "."
            ),
            should_call_llm=False,
            confidence=confidence,
            reason=reason,
            needs_human_review=needs_human_review,
        )

    def _unverified_claim_result(self, *, confidence: float, reason: str) -> HandlerResult:
        return HandlerResult(
            action=HandlerAction.REFUSE_UNVERIFIED_CLAIM,
            answer=(
                f"I can’t confirm that claim without verified information from "
                f"the official {self.config.product_name} documentation. I don’t "
                f"want to guess or promise something that may be inaccurate. "
                f"Please check {self.config.support_url} for official information."
            ).replace("f want", "want"),
            should_call_llm=False,
            confidence=confidence,
            reason=reason,
            needs_human_review=True,
        )

    def _has_sufficient_verified_evidence(
        self,
        evidence: Sequence[KBEvidence],
        confidence: float,
    ) -> bool:
        return (
            len(evidence) >= self.config.min_verified_evidence_items
            and confidence >= self.config.min_confidence
        )

    @staticmethod
    def _resolve_confidence(
        evidence: Sequence[KBEvidence],
        retrieval_confidence: Optional[float],
    ) -> float:
        if retrieval_confidence is not None:
            return max(0.0, min(1.0, float(retrieval_confidence)))
        return max((max(0.0, min(1.0, item.confidence)) for item in evidence), default=0.0)

    @staticmethod
    def _normalize_evidence(
        evidence: Iterable[KBEvidence | Mapping[str, Any]],
    ) -> list[KBEvidence]:
        normalized: list[KBEvidence] = []
        for item in evidence:
            if isinstance(item, KBEvidence):
                normalized.append(item)
                continue
            if isinstance(item, Mapping):
                try:
                    normalized.append(
                        KBEvidence(
                            text=str(item.get("text", "")),
                            source_url=(
                                str(item["source_url"])
                                if item.get("source_url") else None
                            ),
                            confidence=float(item.get("confidence", 0.0)),
                            verified=bool(item.get("verified", False)),
                        )
                    )
                except (TypeError, ValueError):
                    logger.exception("Skipping malformed evidence item.")
        return normalized

    def _high_risk_topic(self, query: str) -> Optional[str]:
        for topic, pattern in self.HIGH_RISK_PATTERNS.items():
            if pattern.search(query):
                return topic
        return None

    def _looks_like_claim_request(self, query: str) -> bool:
        return any(pattern.search(query) for pattern in self.CLAIM_REQUEST_PATTERNS)

    @staticmethod
    def _evidence_directly_supports_claim(
        query: str,
        evidence: Sequence[KBEvidence],
    ) -> bool:
        """
        Conservative lexical check only.

        Production systems should use a dedicated grounding/entailment checker
        or human review for important claims. This simple check requires at
        least one meaningful query term to appear in verified evidence.
        """
        stop_words = {
            "can", "you", "confirm", "that", "is", "it", "true", "do", "does",
            "hisabdo", "the", "a", "an", "and", "or", "for", "to", "of", "in",
            "with", "all", "every", "any", "always", "never", "100", "guarantee",
            "guaranteed", "promise", "prove", "certify", "assure",
        }
        terms = {
            term.lower()
            for term in re.findall(r"[A-Za-z0-9]+", query)
            if len(term) > 2 and term.lower() not in stop_words
        }
        if not terms:
            return False
        evidence_text = " ".join(item.text.lower() for item in evidence)
        return any(term in evidence_text for term in terms)


def handle_hisabdo_query(
    query: str,
    evidence: Optional[Sequence[KBEvidence | Mapping[str, Any]]] = None,
    retrieval_confidence: Optional[float] = None,
    *,
    support_url: str = "https://www.xicteksystems.com/portfolio",
) -> dict[str, Any]:
    """
    Convenience function for a backend endpoint.

    Returns a plain dictionary that can be returned as JSON by Flask/FastAPI.
    Configure the support URL with the official approved support/contact page.
    """
    handler = HisabDoFallbackRefusalHandler(
        HandlerConfig(support_url=support_url)
    )
    return handler.handle(
        query=query,
        evidence=evidence,
        retrieval_confidence=retrieval_confidence,
    ).to_dict()


if __name__ == "__main__":
    # Demonstration only. Replace these sample values with actual retriever output.
    logging.basicConfig(level=logging.INFO)

    handler = HisabDoFallbackRefusalHandler()

    sample_queries = [
        "What does HisabDo do?",
        "Does HisabDo integrate with every bank?",
        "Can you guarantee that my data is 100% secure?",
    ]

    for sample in sample_queries:
        result = handler.handle(
            query=sample,
            evidence=[],
            retrieval_confidence=0.0,
        )
        print(f"\nQuestion: {sample}")
        print(result.to_dict())
