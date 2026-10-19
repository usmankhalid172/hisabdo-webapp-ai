"""Regression tests for source_url_matcher_fix.py; no external network required."""
from types import SimpleNamespace

import pytest

from source_url_matcher_fix import (
    inject_source_urls,
    resolve_source_url,
    validate_blog_url,
)


def always_active(url, timeout):
    return True


def always_inactive(url, timeout):
    return False


def test_accepts_official_blog_url_and_strips_tracking():
    assert validate_blog_url(
        "https://www.xicteksystems.com/blog/article/?utm_source=test#top"
    ) == "https://www.xicteksystems.com/blog/article"


@pytest.mark.parametrize("url", [
    "http://xicteksystems.com/blog/article",
    "https://example.com/blog/article",
    "https://xicteksystems.com/services",
    "https://xicteksystems.com.evil.test/blog/article",
    "https://user@xicteksystems.com/blog/article",
    "https://xicteksystems.com:444/blog/article",
    "https://xicteksystems.com/blog/%2e%2e/private",
    "javascript:alert(1)",
    "/blog/article",
])
def test_rejects_unsafe_or_non_blog_urls(url):
    assert validate_blog_url(url) is None


def test_missing_nested_metadata_uses_direct_url_field():
    doc = {
        "metadata": {"title": "Blog article"},
        "source_url": "https://xicteksystems.com/blog/right-article",
    }
    url, reason = resolve_source_url(doc, verify_live=False)
    assert url == "https://xicteksystems.com/blog/right-article"
    assert reason == "metadata"


def test_invalid_first_candidate_does_not_hide_later_valid_candidate():
    doc = {
        "metadata": {
            "source_url": "https://example.com/fake",
            "canonical_url": "https://xicteksystems.com/blog/correct-article",
        }
    }
    url, _ = resolve_source_url(doc, verify_live=False)
    assert url == "https://xicteksystems.com/blog/correct-article"


def test_document_object_shape_supported():
    doc = SimpleNamespace(
        metadata={"title": "Article title"},
        page_content="Blog body",
        source_url="https://xicteksystems.com/blog/object-article",
    )
    url, _ = resolve_source_url(doc, verify_live=False)
    assert url == "https://xicteksystems.com/blog/object-article"


def test_verified_catalog_fallback_when_url_metadata_missing():
    doc = {"metadata": {"title": "Trusted Article"}}
    catalog = {"Trusted Article": "https://xicteksystems.com/blog/trusted-article"}
    url, reason = resolve_source_url(doc, catalog, verify_live=False)
    assert url == "https://xicteksystems.com/blog/trusted-article"
    assert reason == "verified_catalog_fallback"


def test_no_catalog_fallback_means_no_guessed_url():
    doc = {"metadata": {"title": "Unknown Article"}}
    url, reason = resolve_source_url(doc, verify_live=False)
    assert url is None
    assert reason == "no_verified_url"


def test_broken_url_not_injected_when_live_check_fails():
    doc = {"metadata": {
        "title": "Broken article",
        "url": "https://xicteksystems.com/blog/broken",
    }}
    answer = inject_source_urls(
        "Answer.", [doc], verify_live=True, url_checker=always_inactive
    )
    assert answer == "Answer."
    assert "Sources:" not in answer


def test_active_url_is_injected_and_deduplicated():
    doc = {"metadata": {
        "title": "Article",
        "url": "https://xicteksystems.com/blog/article",
    }}
    answer = inject_source_urls(
        "Answer.", [doc, doc], verify_live=True, url_checker=always_active
    )
    assert answer.count("https://xicteksystems.com/blog/article") == 1
    assert answer.endswith("- [Article](https://xicteksystems.com/blog/article)")


def test_existing_source_footer_is_replaced_not_duplicated():
    doc = {"metadata": {
        "title": "Correct Article",
        "url": "https://xicteksystems.com/blog/correct",
    }}
    answer = inject_source_urls(
        "Answer.\n\nSources:\n- [Wrong](https://xicteksystems.com/blog/wrong)",
        [doc], verify_live=False
    )
    assert answer.count("Sources:") == 1
    assert "blog/wrong" not in answer
    assert "blog/correct" in answer


def test_existing_url_in_body_is_not_duplicated_in_footer():
    doc = {"metadata": {
        "title": "Article",
        "url": "https://xicteksystems.com/blog/article",
    }}
    answer = inject_source_urls(
        "Read https://xicteksystems.com/blog/article for details.",
        [doc], verify_live=False
    )
    assert answer.count("https://xicteksystems.com/blog/article") == 1


def test_title_missing_gets_safe_fallback_title():
    doc = {"metadata": {"url": "https://xicteksystems.com/blog/article"}}
    answer = inject_source_urls("Answer.", [doc], verify_live=False)
    assert "[XICTEK Blog Article](https://xicteksystems.com/blog/article)" in answer


def test_invalid_response_and_max_sources_validation():
    with pytest.raises(TypeError):
        inject_source_urls(None, [])
    with pytest.raises(ValueError):
        inject_source_urls("Answer", [], max_sources=0)


def test_chunk_id_can_recover_original_page_url_when_url_metadata_missing():
    doc = {
        "metadata": {"title": "Article title"},
        "id": "https://xicteksystems.com/blog/original-article#chunk-12",
    }
    url, _ = resolve_source_url(doc, verify_live=False)
    assert url == "https://xicteksystems.com/blog/original-article"
