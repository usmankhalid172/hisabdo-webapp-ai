"""
categorization_service — orchestrates normalization → rule-based fallback
→ ML model → confidence-based confirmation flag, per Day 15 §6.2.
"""
from ..config import get_settings
from ..schemas import CategorizeRequest, CategorizeResponse
from .ml_classifier import get_ml_categorizer
from .rules import rule_based_predict


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


def categorize(request: CategorizeRequest) -> CategorizeResponse:
    settings = get_settings()
    description = _normalize(request.description)

    rule_hit = rule_based_predict(description, request.merchant)
    if rule_hit is not None:
        category, confidence = rule_hit
        return CategorizeResponse(
            category=category,
            confidence=confidence,
            alternative_categories=[],
            needs_confirmation=False,
            method="rule_based",
        )

    category, confidence, alternatives = get_ml_categorizer().predict(
        description, request.merchant
    )
    needs_confirmation = confidence < settings.categorization_confidence_threshold

    return CategorizeResponse(
        category=category,
        confidence=round(confidence, 4),
        alternative_categories=alternatives,
        needs_confirmation=needs_confirmation,
        method="ml_model",
    )
