"""
Source URL Matcher Fix — XICTEK Blog Section
=============================================

Standalone utility for resolving and injecting safe source URLs from retrieved
Blog documents. It supports incomplete metadata, validates URL structure,
optionally checks that a URL is reachable, deduplicates sources, and never
fabricates a URL for an unknown article.

Usage:
    from source_url_matcher_fix import inject_source_urls

    answer = inject_source_urls(
        generated_answer,
        retrieved_documents,
        source_catalog={
            # Optional verified fallback catalogue:
            "How to Choose a Software Development Company in Pakistan":
                "https://xicteksystems.com/blog/software-development-company-pakistan"
        },
    )

Important:
- The fallback catalogue must contain URLs verified by the project/team.
- URL syntax/domain checks do not prove that an article exists.
- Live checking is enabled by default. Set verify_live=False for offline use.
- Only official XICTEK HTTPS blog URLs are accepted.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterable, Mapping
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit, urlunsplit
from urllib.request import Request, urlopen

ALLOWED_HOSTS = {"xicteksystems.com", "www.xicteksystems.com"}
BLOG_PATH = "/blog"
DEFAULT_MAX_SOURCES = 3
DEFAULT_TIMEOUT = 5

URL_FIELDS = (
    "source_url", "canonical_url", "url", "page_url",
    "source", "link", "href", "website_url", "original_url",
    # Some vector stores preserve the original page URL in a chunk identifier.
    "chunk_id", "source_id", "id",
)
TITLE_FIELDS = ("title", "page_title", "name", "heading", "article_title")


def validate_blog_url(value: Any) -> str | None:
    """Return a canonical HTTPS XICTEK Blog URL or None if unsafe/invalid."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or any(ord(c) < 32 for c in value):
        return None
    # Do not silently turn relative URLs into absolute URLs: their origin is unknown.
    try:
        parsed = urlsplit(value)
        if parsed.scheme.lower() != "https":
            return None
        if parsed.username or parsed.password:
            return None
        if parsed.port not in (None, 443):
            return None
        host = (parsed.hostname or "").lower()
        if host not in ALLOWED_HOSTS:
            return None
        path = parsed.path or BLOG_PATH
        decoded_path = unquote(path)
        if "\\" in decoded_path or any(p in {".", ".."} for p in decoded_path.split("/")):
            return None
        if not (decoded_path == BLOG_PATH or decoded_path.startswith(BLOG_PATH + "/")):
            return None
        # Reject encoded traversal and encoded separators that can be interpreted differently.
        if re.search(r"%2f|%5c", path, re.IGNORECASE):
            return None
        normalized_path = path.rstrip("/") or BLOG_PATH
        return urlunsplit(("https", host, normalized_path, "", ""))
    except (ValueError, TypeError):
        return None


def _as_mapping(document: Any) -> Mapping:
    """Get metadata without assuming every retriever uses the same object shape."""
    if isinstance(document, Mapping):
        meta = document.get("metadata")
        if isinstance(meta, Mapping):
            # Keep direct document fields as a fallback when nested metadata is partial.
            return {**document, **meta}
        return document
    meta = getattr(document, "metadata", None)
    if isinstance(meta, Mapping):
        merged = dict(meta)
        for field in URL_FIELDS + TITLE_FIELDS:
            direct = getattr(document, field, None)
            if direct is not None and field not in merged:
                merged[field] = direct
        content = getattr(document, "page_content", None)
        if isinstance(content, str):
            merged.setdefault("page_content", content)
        return merged
    result = {}
    for field in URL_FIELDS + TITLE_FIELDS + ("page_content", "text", "content"):
        val = getattr(document, field, None)
        if val is not None:
            result[field] = val
    return result


def _normalize_title(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    value = unquote(value).lower().strip()
    value = re.sub(r"\.(html?|php)$", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _title_and_content(metadata: Mapping) -> tuple[str, str]:
    title = next((metadata.get(k) for k in TITLE_FIELDS
                  if isinstance(metadata.get(k), str) and metadata.get(k).strip()), "")
    content = next((metadata.get(k) for k in ("page_content", "text", "content", "body")
                    if isinstance(metadata.get(k), str)), "")
    return title, content


def _catalog_fallback(title: str, content: str, source_catalog: Mapping[str, str]) -> str | None:
    """
    Resolve missing URL metadata only against a caller-supplied verified catalogue.
    Matching is conservative: normalized exact title or exact URL slug only.
    """
    title_key = _normalize_title(title)
    slug_candidates = set()
    # A URL-like slug in title/content is useful only as a key into the trusted catalogue.
    for candidate in (title,):
        normalized = _normalize_title(candidate)
        if normalized:
            slug_candidates.add(normalized)
    for key, raw_url in source_catalog.items():
        key_norm = _normalize_title(key)
        if not key_norm:
            continue
        if key_norm == title_key or key_norm in slug_candidates:
            return validate_blog_url(raw_url)
    return None


def _candidate_urls(metadata: Mapping) -> Iterable[str]:
    for field in URL_FIELDS:
        value = metadata.get(field)
        if isinstance(value, str) and value.strip():
            # Chunk IDs commonly look like https://site/blog/article#chunk-12.
            # Only strip the known chunk suffix; ordinary URL fragments are
            # harmless because validate_blog_url removes fragments anyway.
            if field in {"chunk_id", "source_id", "id"}:
                match = re.match(r"^(https://[^\\s]+?)(?:#chunk-\\d+)$", value.strip(), re.I)
                if match:
                    yield match.group(1)
            yield value
        elif isinstance(value, Mapping):
            # Some retrievers nest source information under e.g. metadata.source.url.
            for nested_key in ("url", "href", "link", "source_url"):
                nested = value.get(nested_key)
                if isinstance(nested, str) and nested.strip():
                    yield nested


def is_url_active(url: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Check reachability with HEAD and GET fallback; redirects must remain approved."""
    for method in ("HEAD", "GET"):
        request = Request(url, headers={"User-Agent": "XICTEK-Blog-Source-Matcher/1.0"}, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                status = getattr(response, "status", 200)
                final_url = validate_blog_url(response.geturl())
                return 200 <= status < 400 and final_url is not None
        except HTTPError as exc:
            if method == "HEAD" and exc.code in (403, 405, 501):
                continue
            return False
        except (URLError, TimeoutError, OSError, ValueError):
            if method == "HEAD":
                continue
            return False
    return False


def resolve_source_url(
    document: Any,
    source_catalog: Mapping[str, str] | None = None,
    verify_live: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
    url_checker: Callable[[str, int], bool] | None = None,
) -> tuple[str | None, str]:
    """
    Return (URL, reason). Invalid candidates are skipped so a later valid
    metadata field can still win. If metadata has no usable URL, consult the
    verified catalogue. No LLM-generated or guessed URL is accepted.
    """
    metadata = _as_mapping(document)
    candidates = list(_candidate_urls(metadata))
    for candidate in candidates:
        url = validate_blog_url(candidate)
        if not url:
            continue
        if verify_live:
            checker = url_checker or is_url_active
            try:
                if not checker(url, timeout):
                    continue
            except Exception:
                continue
        return url, "metadata"

    title, content = _title_and_content(metadata)
    if source_catalog:
        fallback = _catalog_fallback(title, content, source_catalog)
        if fallback:
            if not verify_live:
                return fallback, "verified_catalog_fallback"
            checker = url_checker or is_url_active
            try:
                if checker(fallback, timeout):
                    return fallback, "verified_catalog_fallback"
            except Exception:
                pass

    return None, "no_verified_url"


def _safe_title(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "XICTEK Blog Article"
    value = re.sub(r"\s+", " ", value).strip()[:180]
    return re.sub(r"([\\`*_{}\[\]()<>!|])", r"\\\1", value)


def inject_source_urls(
    response: str,
    retrieved_documents: Iterable[Any] | None,
    *,
    source_catalog: Mapping[str, str] | None = None,
    max_sources: int = DEFAULT_MAX_SOURCES,
    verify_live: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
    url_checker: Callable[[str, int], bool] | None = None,
) -> str:
    """
    Append a Sources footer using validated, deduplicated article URLs.
    Existing answer text is preserved. If no trustworthy URL can be resolved,
    the answer is returned unchanged rather than inventing a source.
    """
    if not isinstance(response, str):
        raise TypeError("response must be a string")
    if isinstance(max_sources, bool) or not isinstance(max_sources, int) or max_sources < 1:
        raise ValueError("max_sources must be a positive integer")
    if retrieved_documents is None:
        return response
    if isinstance(retrieved_documents, Mapping):
        documents = [retrieved_documents]
    else:
        try:
            documents = list(retrieved_documents)
        except TypeError:
            return response

    existing_urls = set(re.findall(r"https?://[^\s<>\])}\"']+", response, flags=re.I))
    sources: list[tuple[str, str]] = []
    seen: set[str] = set()
    for document in documents:
        url, _reason = resolve_source_url(
            document, source_catalog, verify_live, timeout, url_checker
        )
        if not url or url in seen or any(url.rstrip(".,;:!?") == u.rstrip(".,;:!?") for u in existing_urls):
            continue
        seen.add(url)
        metadata = _as_mapping(document)
        title, _content = _title_and_content(metadata)
        sources.append((url, _safe_title(title)))
        if len(sources) >= max_sources:
            break

    if not sources:
        return response
    footer = "Sources:\n" + "\n".join(f"- [{title}]({url})" for url, title in sources)
    base = response.rstrip()
    # If a Sources heading already exists, replace that footer rather than stacking duplicates.
    heading = re.compile(r"(?im)^\s*(?:#{1,6}\s*)?sources\s*:?\s*$")
    matches = list(heading.finditer(base))
    if matches:
        base = base[:matches[-1].start()].rstrip()
    return f"{base}\n\n{footer}" if base else footer


if __name__ == "__main__":
    demo_docs = [
        {"metadata": {"title": "Example article", "url": "https://xicteksystems.com/blog/example-article"}},
        {"metadata": {"title": "Example article", "source_url": "https://example.com/broken"}},
        {"title": "Catalog article"},
    ]
    demo_catalog = {"Catalog article": "https://xicteksystems.com/blog/catalog-article"}
    print(inject_source_urls(
        "Here is the answer based on the retrieved blog context.",
        demo_docs,
        source_catalog=demo_catalog,
        verify_live=False,
    ))
