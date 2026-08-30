from src.expense_categorization.rules import rule_based_predict
from src.expense_categorization.service import categorize
from src.schemas import CategorizeRequest


def test_rule_based_predict_hits_known_keyword():
    result = rule_based_predict("Electricity bill payment", "LESCO")
    assert result is not None
    category, confidence = result
    assert category == "Utilities"
    assert confidence >= 0.9


def test_rule_based_predict_returns_none_for_unmatched_text():
    assert rule_based_predict("xyz completely unknown zzqq", None) is None


def test_categorize_service_uses_rule_based_when_available():
    req = CategorizeRequest(description="Ride to office", merchant="Careem", amount=350)
    resp = categorize(req)
    assert resp.category == "Transport"
    assert resp.method == "rule_based"
    assert resp.needs_confirmation is False


def test_categorize_service_falls_back_to_ml_model():
    # Deliberately avoids every rules.py keyword so the ML path is exercised.
    req = CategorizeRequest(description="Payment for annual subscription renewal", amount=1500)
    resp = categorize(req)
    assert resp.method == "ml_model"
    assert 0.0 <= resp.confidence <= 1.0
    assert isinstance(resp.needs_confirmation, bool)


def test_categorize_endpoint_returns_valid_shape(client, auth_headers):
    resp = client.post(
        "/api/v1/categorize",
        json={"description": "Grocery shopping at Metro", "merchant": "Metro", "amount": 4500},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    for field in ("category", "confidence", "alternative_categories", "needs_confirmation", "method"):
        assert field in body


def test_categorize_batch_endpoint(client, auth_headers):
    payload = {
        "items": [
            {"description": "Uber to airport", "amount": 1800},
            {"description": "Netflix subscription", "amount": 1100},
        ]
    }
    resp = client.post("/api/v1/categorize/batch", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) == 2
    assert results[0]["category"] == "Transport"
    assert results[1]["category"] == "Entertainment"
