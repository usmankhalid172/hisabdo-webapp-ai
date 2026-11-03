import time

from ..config import get_settings
from ..logging_config import logger
from ..schemas import CategorizeRequest, CategorizeResponse
from .ml_classifier import get_ml_categorizer
from .rules import rule_based_predict


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


def categorize(request: CategorizeRequest) -> CategorizeResponse:
    started = time.perf_counter()
    settings = get_settings()
    description = _normalize(request.description)

    rule_hit = rule_based_predict(description, request.merchant)
    if rule_hit is not None:
        category, confidence = rule_hit
        logger.info(
            "Expense categorization completed",
            extra={
                "event": "expense_categorization",
                "outcome": "success",
                "source": "rule_based",
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return CategorizeResponse(
            category=category,
            confidence=confidence,
            alternative_categories=[],
            needs_confirmation=False,
            method="rule_based",
        )

    try:
        category, confidence, alternatives = get_ml_categorizer().predict(
            description, request.merchant
        )
        needs_confirmation = confidence < settings.categorization_confidence_threshold

        logger.info(
            "Expense categorization completed",
            extra={
                "event": "expense_categorization",
                "outcome": "success",
                "source": "ml_model",
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return CategorizeResponse(
            category=category,
            confidence=round(confidence, 4),
            alternative_categories=alternatives,
            needs_confirmation=needs_confirmation,
            method="ml_model",
        )

    except Exception:
        logger.warning(
            "Expense categorization model unavailable",
            extra={
                "event": "expense_categorization",
                "outcome": "fallback",
                "source": "ml_model",
                "error_category": "model_unavailable",
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return CategorizeResponse(
            category="Uncategorized",
            confidence=0.0,
            alternative_categories=[],
            needs_confirmation=True,
            method="fallback",
        )
