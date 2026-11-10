"""Reliable website ingestion with structured logs, change detection and integrity checks.

Run from the repository root: python -m src.xictek_website_assistant.ingest

The vector index is rebuilt on each successful crawl. A source manifest records
content hashes so the run can classify new, updated, unchanged and removed URLs.
Removed-source decisions are committed only after a complete crawl with no fetch
or parse failures; partial scans never erase previously known sources.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import Counter, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin, urlparse, urlunparse

import httpx
import numpy as np
from bs4 import BeautifulSoup

from .chunking import chunk_text
from .config import get_xictek_settings
from .embeddings import embed_texts
from .vector_store import Chunk, VectorStore

USER_AGENT = "XictekWebsiteAssistantIngestBot/1.0 (+internal knowledge-base indexer)"
_STRIP_TAGS = ["script", "style", "nav", "header", "footer", "noscript", "svg", "form"]


@dataclass
class CrawledPage:
    url: str
    title: str
    text: str


@dataclass
class CrawlResult:
    pages: list[CrawledPage]
    failures: list[dict[str, Any]]
    attempted_urls: int
    non_html_urls: int
    max_pages_reached: bool


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalise_url(url: str) -> str:
    """Remove fragments and default ports while preserving meaningful paths/query."""
    url, _fragment = urldefrag(url.strip())
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").lower()
    if not scheme or not host:
        return url
    port = parsed.port
    netloc = host if port is None or (scheme == "https" and port == 443) or (scheme == "http" and port == 80) else f"{host}:{port}"
    path = parsed.path or "/"
    return urlunparse((scheme, netloc, path, "", parsed.query, ""))


def _is_allowed_domain(url: str, allowed_domains: list[str]) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in {d.lower() for d in allowed_domains}


def _extract_page(url: str, html: str) -> CrawledPage:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    main = soup.find("main") or soup.body or soup
    text = main.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n\n".join(lines)
    return CrawledPage(url=url, title=title, text=text)


def _discover_links(base_url: str, html: str, allowed_domains: list[str]) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    for anchor in soup.find_all("a", href=True):
        absolute = _normalise_url(urljoin(base_url, anchor["href"]))
        if urlparse(absolute).scheme in {"http", "https"} and _is_allowed_domain(absolute, allowed_domains):
            links.append(absolute)
    return links


def _make_run_logger(log_path: Path) -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    name = f"xictek.ingestion.{log_path.stem}"
    run_logger = logging.getLogger(name)
    run_logger.setLevel(logging.INFO)
    run_logger.propagate = False
    run_logger.handlers.clear()

    class JsonLineFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            payload = {
                "timestamp": _utc_now(),
                "level": record.levelname,
                "event": record.getMessage(),
            }
            for key, value in record.__dict__.items():
                if key not in logging.LogRecord("", 0, "", 0, "", (), None).__dict__ and key not in {"message", "asctime"} and not key.startswith("_"):
                    try:
                        json.dumps(value)
                        payload[key] = value
                    except (TypeError, ValueError):
                        payload[key] = str(value)
            if record.exc_info:
                payload["exception"] = self.formatException(record.exc_info)
            return json.dumps(payload, ensure_ascii=False)

    formatter = JsonLineFormatter()
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    run_logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    run_logger.addHandler(console_handler)
    return run_logger


def crawl_detailed(
    seed_urls: list[str], allowed_domains: list[str], max_pages: int, delay_seconds: float,
    run_logger: logging.Logger | None = None,
) -> CrawlResult:
    visited: set[str] = set()
    queued: set[str] = set()
    queue: deque[str] = deque()
    for seed in seed_urls:
        normal = _normalise_url(seed)
        if normal not in queued:
            queue.append(normal)
            queued.add(normal)
    pages: list[CrawledPage] = []
    failures: list[dict[str, Any]] = []
    non_html = 0

    def log(level: int, event: str, **fields: Any) -> None:
        if run_logger:
            run_logger.log(level, event, extra=fields)

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20, follow_redirects=True) as client:
        while queue and len(visited) < max_pages:
            requested_url = queue.popleft()
            if requested_url in visited:
                continue
            visited.add(requested_url)
            try:
                response = client.get(requested_url)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                item = {"url": requested_url, "error_type": type(exc).__name__, "error": str(exc)}
                failures.append(item)
                log(logging.ERROR, "page_fetch_failed", **item)
                continue

            final_url = _normalise_url(str(response.url))
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                non_html += 1
                log(logging.WARNING, "page_skipped_non_html", url=final_url, content_type=content_type)
                continue
            try:
                page = _extract_page(final_url, response.text)
                if not page.text.strip():
                    raise ValueError("HTML page produced no readable text")
                pages.append(page)
                log(logging.INFO, "page_ingested", url=final_url, status_code=response.status_code, text_chars=len(page.text))
            except Exception as exc:  # parser/extraction failures are isolated per page
                item = {"url": final_url, "error_type": type(exc).__name__, "error": str(exc)}
                failures.append(item)
                log(logging.ERROR, "page_parse_failed", **item)
                continue

            for link in _discover_links(final_url, response.text, allowed_domains):
                if link not in visited and link not in queued:
                    queue.append(link)
                    queued.add(link)
            if delay_seconds > 0:
                time.sleep(delay_seconds)

    cap_reached = bool(queue) and len(visited) >= max_pages
    return CrawlResult(pages, failures, len(visited), non_html, cap_reached)


def crawl(seed_urls: list[str], allowed_domains: list[str], max_pages: int, delay_seconds: float) -> list[CrawledPage]:
    """Backward-compatible crawl API used by any existing callers/tests."""
    return crawl_detailed(seed_urls, allowed_domains, max_pages, delay_seconds).pages


def _source_hash(page: CrawledPage) -> str:
    normalized = "\n".join(line.strip() for line in page.text.splitlines() if line.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def classify_source_changes(pages: list[CrawledPage], previous: dict[str, Any]) -> dict[str, Any]:
    current = {page.url: {"sha256": _source_hash(page), "title": page.title} for page in pages}
    old_sources = previous.get("sources", {}) if isinstance(previous, dict) else {}
    new_urls = sorted(set(current) - set(old_sources))
    removed_urls = sorted(set(old_sources) - set(current))
    updated_urls = sorted(url for url in set(current) & set(old_sources) if current[url]["sha256"] != old_sources[url].get("sha256"))
    unchanged_urls = sorted(url for url in set(current) & set(old_sources) if current[url]["sha256"] == old_sources[url].get("sha256"))
    return {"current": current, "new": new_urls, "updated": updated_urls, "unchanged": unchanged_urls, "removed": removed_urls}


def _duplicate_diagnostics(chunks: list[Chunk], vectors: np.ndarray) -> dict[str, Any]:
    text_counts = Counter(chunk.text for chunk in chunks)
    duplicate_text_groups = [{"occurrences": count, "text_preview": text[:180], "urls": sorted({c.url for c in chunks if c.text == text and c.url})[:10]}
                             for text, count in text_counts.items() if count > 1]
    vector_counts = Counter(hashlib.sha256(np.ascontiguousarray(row).tobytes()).hexdigest() for row in vectors)
    duplicate_vector_groups = sum(1 for count in vector_counts.values() if count > 1)
    duplicate_vector_excess = sum(count - 1 for count in vector_counts.values() if count > 1)
    zero_vectors = int(np.count_nonzero(np.linalg.norm(vectors, axis=1) == 0)) if vectors.size else 0
    return {
        "duplicate_text_groups": len(duplicate_text_groups),
        "chunks_in_duplicate_text_groups": sum(item["occurrences"] for item in duplicate_text_groups),
        "duplicate_vector_groups": duplicate_vector_groups,
        "duplicate_vector_excess_rows": duplicate_vector_excess,
        "zero_vector_rows": zero_vectors,
        "duplicate_text_examples": sorted(duplicate_text_groups, key=lambda item: item["occurrences"], reverse=True)[:10],
    }


def build_index(pages: list[CrawledPage]) -> VectorStore:
    settings = get_xictek_settings()
    chunks: list[Chunk] = []
    texts: list[str] = []
    for page in pages:
        seen_on_page: set[str] = set()
        for index, body in enumerate(chunk_text(page.text, settings.chunk_size_chars, settings.chunk_overlap_chars)):
            if body in seen_on_page:
                continue
            seen_on_page.add(body)
            chunks.append(Chunk(chunk_id=f"{page.url}#chunk-{index}", title=page.title, url=page.url, text=body))
            texts.append(body)
    if not texts:
        raise ValueError("No non-empty chunks were produced; existing index was not changed")
    vectors = embed_texts(texts)
    if vectors.ndim != 2 or vectors.shape[0] != len(chunks):
        raise ValueError(f"Invalid embedding matrix shape {vectors.shape} for {len(chunks)} chunks")
    if not np.isfinite(vectors).all():
        raise ValueError("Embedding matrix contains NaN or infinite values")
    store = VectorStore()
    store.build(chunks, vectors)
    return store


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    settings = get_xictek_settings()
    data_dir = settings.index_dir.parent
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = data_dir / "ingestion_logs" / f"ingestion_{run_id}.jsonl"
    run_logger = _make_run_logger(log_path)
    manifest_path = data_dir / "source_manifest.json"
    report_path = data_dir / "ingestion_report.json"
    started = time.monotonic()
    previous_manifest = _read_json(manifest_path, {"sources": {}})
    run_logger.info("ingestion_started", extra={"seed_urls": settings.crawl_seed_urls, "max_pages": settings.crawl_max_pages})

    result = crawl_detailed(settings.crawl_seed_urls, settings.allowed_crawl_domains, settings.crawl_max_pages,
                            settings.crawl_request_delay_seconds, run_logger)
    if not result.pages:
        report = {"run_id": run_id, "status": "failed", "reason": "No pages were successfully extracted",
                  "attempted_urls": result.attempted_urls, "failures": result.failures, "log_file": str(log_path)}
        _write_json_atomic(report_path, report)
        raise RuntimeError("Ingestion aborted: no readable pages were extracted; existing index preserved")

    changes = classify_source_changes(result.pages, previous_manifest)
    store = build_index(result.pages)
    diagnostics = _duplicate_diagnostics(store.chunks, store._vectors)
    # Persist index only after crawl, extraction and embedding validation succeed.
    store.save()

    complete = not result.failures and not result.max_pages_reached
    if complete:
        manifest = {"generated_at": _utc_now(), "sources": changes["current"]}
        _write_json_atomic(manifest_path, manifest)
        removed = changes["removed"]
    else:
        # Do not infer removals from a partial crawl (e.g. transient 404/5xx/network errors).
        removed = []
        run_logger.warning("manifest_not_updated_partial_scan", extra={"failure_count": len(result.failures), "max_pages_reached": result.max_pages_reached})

    elapsed_ms = round((time.monotonic() - started) * 1000, 2)
    report = {
        "run_id": run_id,
        "started_at_utc": run_id,
        "completed_at_utc": _utc_now(),
        "status": "completed_with_warnings" if result.failures or result.max_pages_reached or diagnostics["duplicate_vector_excess_rows"] or diagnostics["zero_vector_rows"] else "completed",
        "crawl": {"attempted_urls": result.attempted_urls, "successful_pages": len(result.pages),
                  "failed_pages": len(result.failures), "non_html_skipped": result.non_html_urls,
                  "max_pages_reached": result.max_pages_reached, "failures": result.failures},
        "source_changes": {"new": changes["new"], "updated": changes["updated"],
                           "unchanged": changes["unchanged"], "removed": removed,
                           "removed_detection_committed": complete},
        "index": {"chunk_count": len(store), "vector_shape": list(store._vectors.shape),
                  "chunk_vector_count_match": len(store.chunks) == store._vectors.shape[0], **diagnostics},
        "duration_ms": elapsed_ms,
        "log_file": str(log_path),
        "manifest_file": str(manifest_path),
    }
    _write_json_atomic(report_path, report)
    run_logger.info("ingestion_finished", extra={"status": report["status"], "pages": len(result.pages),
                                                  "chunks": len(store), "duration_ms": elapsed_ms,
                                                  "failed_pages": len(result.failures), **diagnostics})
    print(f"Ingestion {report['status']}: {len(result.pages)} pages, {len(store)} chunks; report: {report_path}")


if __name__ == "__main__":
    main()
