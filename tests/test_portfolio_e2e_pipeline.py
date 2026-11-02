import json
from portfolio_e2e_pipeline import (
    ABOUT_URL, PORTFOLIO_URL, calculate_stats, classify_source_for_claim,
    contains_expected_outcome, contains_expected_stack, empty_retrieval_fallback,
    is_outlier_iqr, resolve_contextual_query, safe_generation, unsupported_metric_fallback,
    validate_https_url,
)

TOTAL = [487.11, 618.49, 962.40, 29430.00, 739.37, 624.83, 420.02, 431.79, 760.07, 585.78]
WAIT = [483.81, 613.38, 958.48, 421.19, 734.77, 622.17, 417.20, 429.13, 757.54, 582.60]

def test_hisabdo_stack_is_exact():
    assert contains_expected_stack("HisabDo is built with Flutter, Supabase, and PostgreSQL.")

def test_stack_rejects_generic_web_stack():
    assert not contains_expected_stack("React, Next.js, and TypeScript")

def test_portfolio_stack_source_is_relevant():
    assert classify_source_for_claim(PORTFOLIO_URL, "portfolio_stack")

def test_about_features_require_about_source():
    assert classify_source_for_claim(ABOUT_URL, "about_features")
    assert not classify_source_for_claim("https://hisabdo.app/contact", "about_features")

def test_generic_blog_rejected_for_portfolio_stack():
    assert not classify_source_for_claim("https://xicteksystems.com/blog/react-development-services", "portfolio_stack")

def test_homepage_not_accepted_as_direct_case_study_citation():
    assert not classify_source_for_claim("https://xicteksystems.com/", "portfolio_stack")

def test_https_and_url_structure():
    assert validate_https_url(PORTFOLIO_URL)[0]
    assert not validate_https_url("http://xicteksystems.com/portfolio")[0]
    assert not validate_https_url("https:///portfolio")[0]

def test_multi_turn_pronoun_resolution_retains_hisabdo():
    history = [{"role": "user", "content": "Explain HisabDo."}]
    assert resolve_contextual_query("What technologies does it use?", history).startswith("HisabDo ")

def test_context_resolves_after_longer_sequence():
    history = [
        {"role": "user", "content": "Tell me about HisabDo."},
        {"role": "assistant", "content": "An offline-first ledger."},
        {"role": "user", "content": "What problem does it solve?"},
        {"role": "assistant", "content": "Paper-register workflows."},
        {"role": "user", "content": "Who is it designed for?"},
    ]
    q = resolve_contextual_query("What technologies does it use?", history)
    assert "HisabDo" in q and contains_expected_stack("Flutter Supabase PostgreSQL")

def test_unsupported_revenue_metric_fallback():
    answer = "The provided case study does not specify an exact first-year revenue increase percentage. I cannot verify a figure."
    assert unsupported_metric_fallback(answer)
    assert not unsupported_metric_fallback("Customers increased revenue by 35%.")

def test_client_outcome_is_grounded():
    assert contains_expected_outcome("A focused product foundation for expense tracking, digital khata, and customer balances.")
    assert not contains_expected_outcome("Increased customer revenue by 30%.")

def test_empty_retrieval_returns_abstention():
    fallback = empty_retrieval_fallback([])
    assert "don't have verified information" in fallback
    assert empty_retrieval_fallback(["retrieved chunk"]) == ""

def test_provider_error_is_handled():
    def fail(*args, **kwargs):
        raise TimeoutError("simulated provider timeout")
    reply, status = safe_generation(fail, "question")
    assert status == "provider_error"
    assert "could not complete" in reply

def test_production_total_latency_statistics():
    stats = calculate_stats(TOTAL)
    assert stats.count == 10
    assert round(stats.mean_ms, 2) == 3505.99
    assert round(stats.median_ms, 2) == 621.66
    assert round(stats.p95_linear_ms, 2) == 16619.58
    assert stats.p95_nearest_rank_ms == 29430.00
    assert stats.minimum_ms == 420.02 and stats.maximum_ms == 29430.00

def test_production_server_wait_statistics():
    stats = calculate_stats(WAIT)
    assert stats.count == 10
    assert round(stats.mean_ms, 2) == 602.03
    assert round(stats.median_ms, 2) == 597.99
    assert round(stats.p95_linear_ms, 2) == 868.06
    assert stats.minimum_ms == 417.20 and stats.maximum_ms == 958.48

def test_outlier_is_preserved_and_detected():
    assert 29430.00 in is_outlier_iqr(TOTAL)
    assert len(TOTAL) == 10

def test_request_four_gap_is_not_server_wait():
    assert round(TOTAL[3] - WAIT[3], 2) == 29008.81

def test_source_link_relevance_is_not_reachability():
    # A syntactically valid URL is not automatically relevant to a claim.
    assert validate_https_url("https://xicteksystems.com/blog/progressive-web-apps")[0]
    assert not classify_source_for_claim("https://xicteksystems.com/blog/progressive-web-apps", "portfolio_stack")


def test_repository_portfolio_reference_fixture_contains_exact_stack():
    from pathlib import Path
    fixture = json.loads((Path(__file__).parent / "portfolio_reference_fixtures.json").read_text(encoding="utf-8"))
    record = next(item for item in fixture["records"] if item["id"] == "faq-34")
    assert "Flutter, Supabase, and PostgreSQL" in record["text"]
    assert record["url"] == PORTFOLIO_URL
