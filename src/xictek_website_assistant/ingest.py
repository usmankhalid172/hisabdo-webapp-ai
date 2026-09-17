"""
Ingestion pipeline: crawl -> extract -> chunk -> embed -> persist.

Run from the repo root:
    python -m src.xictek_website_assistant.ingest

What it does:
    1. Starting from `XictekSettings.crawl_seed_urls`, does a same-domain
       breadth-first crawl restricted to `allowed_crawl_domains` (never
       follows a link off those domains), up to `crawl_max_pages`.
    2. For each page, strips nav/header/footer/script/style and extracts
       the main readable text via BeautifulSoup.
    3. Chunks each page's text (chunking.py) and embeds every chunk
       locally (embeddings.py).
    4. Persists the result via `VectorStore.save()` — see vector_store.py
       for the on-disk layout.

Re-run this any time xicteksystems.com or hisabdo.app content changes;
it fully rebuilds the index (no incremental/delta indexing), which is
fine at this content scale (a few hundred pages).

Network note: this needs real internet access to xicteksystems.com /
hisabdo.app, which this container's sandboxed egress does not have —
run it from a normal dev machine or CI with outbound HTTPS access.
"""
from __future__ import annotations

import sys
import time
from collections import deque
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .chunking import chunk_text
from .config import get_xictek_settings
from .embeddings import embed_texts
from .vector_store import Chunk, VectorStore

USER_AGENT = "XictekWebsiteAssistantIngestBot/1.0 (+internal knowledge-base indexer)"

# Tags stripped before extracting "readable" page text — nav/chrome, not
# content, and otherwise pollutes every single chunk with the same
# boilerplate (menu items, footer links) diluting retrieval quality.
_STRIP_TAGS = ["script", "style", "nav", "header", "footer", "noscript", "svg", "form"]


@dataclass
class CrawledPage:
    url: str
    title: str
    text: str


def _is_allowed_domain(url: str, allowed_domains: list[str]) -> bool:
    host = urlparse(url).netloc.lower()
    return host in allowed_domains


def _extract_page(url: str, html: str) -> CrawledPage:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(_STRIP_TAGS):
        tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else url
    main = soup.find("main") or soup.body or soup
    text = main.get_text(separator="\n", strip=True)
    # Collapse runs of blank lines left behind by stripped tags, while
    # keeping paragraph breaks chunking.py relies on.
    lines = [line for line in text.splitlines() if line.strip()]
    text = "\n\n".join(lines)
    return CrawledPage(url=url, title=title, text=text)


def _discover_links(base_url: str, html: str, allowed_domains: list[str]) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        absolute = urljoin(base_url, a["href"]).split("#")[0]
        if absolute.startswith("http") and _is_allowed_domain(absolute, allowed_domains):
            links.append(absolute)
    return links


def crawl(seed_urls: list[str], allowed_domains: list[str], max_pages: int, delay_seconds: float) -> list[CrawledPage]:
    visited: set[str] = set()
    queue: deque[str] = deque(seed_urls)
    pages: list[CrawledPage] = []

    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20, follow_redirects=True) as client:
        while queue and len(visited) < max_pages:
            url = queue.popleft()
            if url in visited:
                continue
            visited.add(url)

            try:
                resp = client.get(url)
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                print(f"  [skip] {url} -> {exc}", file=sys.stderr)
                continue

            content_type = resp.headers.get("content-type", "")
            if "text/html" not in content_type:
                continue

            page = _extract_page(url, resp.text)
            if page.text.strip():
                pages.append(page)
                print(f"  [ok]   {url} ({len(page.text)} chars)")

            for link in _discover_links(url, resp.text, allowed_domains):
                if link not in visited:
                    queue.append(link)

            time.sleep(delay_seconds)  # polite crawling — don't hammer the site

    return pages


def build_index(pages: list[CrawledPage]) -> VectorStore:
    settings = get_xictek_settings()
    chunks: list[Chunk] = []
    texts: list[str] = []

    for page in pages:
        for i, chunk_body in enumerate(
            chunk_text(page.text, settings.chunk_size_chars, settings.chunk_overlap_chars)
        ):
            chunks.append(
                Chunk(
                    chunk_id=f"{page.url}#chunk-{i}",
                    title=page.title,
                    url=page.url,
                    text=chunk_body,
                )
            )
            texts.append(chunk_body)

    vectors = embed_texts(texts)
    store = VectorStore()
    store.build(chunks, vectors)
    return store


def main() -> None:
    settings = get_xictek_settings()
    print(f"Crawling {settings.crawl_seed_urls} (allowed domains: {settings.allowed_crawl_domains})...")
    pages = crawl(
        seed_urls=settings.crawl_seed_urls,
        allowed_domains=settings.allowed_crawl_domains,
        max_pages=settings.crawl_max_pages,
        delay_seconds=settings.crawl_request_delay_seconds,
    )
    print(f"Crawled {len(pages)} pages. Chunking + embedding...")
    store = build_index(pages)
    store.save()
    print(f"Indexed {len(store)} chunks -> {settings.index_dir}")


if __name__ == "__main__":
    main()
