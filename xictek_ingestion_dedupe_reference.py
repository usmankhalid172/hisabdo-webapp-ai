"""Reference helpers for idempotent public-website knowledge ingestion.

This module does not fetch pages, create embeddings, or write to a database.
It creates deterministic source/chunk identifiers and a dry-run source diff.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ALLOWED_HOSTS = {"xicteksystems.com", "www.xicteksystems.com"}
TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMETERS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    """Normalize text for identity hashing without altering stored display text."""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def canonicalize_url(url: str, *, allowed_hosts: set[str] | None = None) -> str:
    """Return a stable URL or raise ValueError if it is outside the approved scope."""
    hosts = allowed_hosts or ALLOWED_HOSTS
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"}:
        raise ValueError("Only HTTP(S) source URLs are allowed")
    if parts.username is not None or parts.password is not None:
        raise ValueError("URLs containing credentials are not allowed")

    host = (parts.hostname or "").lower().rstrip(".")
    if host not in hosts:
        raise ValueError(f"Host is outside the approved allowlist: {host or '<missing>'}")
    if not host.startswith("www.") and f"www.{host}" in hosts:
        host = f"www.{host}"

    port = parts.port
    netloc = host if port in (None, 80, 443) else f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")

    kept_query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key in TRACKING_PARAMETERS or any(
            lower_key.startswith(prefix) for prefix in TRACKING_PREFIXES
        ):
            continue
        kept_query.append((key, value))

    return urlunsplit(
        (
            parts.scheme.lower(),
            netloc,
            path,
            urlencode(sorted(kept_query)),
            "",
        )
    )


def source_id(namespace: str, canonical_url: str) -> str:
    """Stable page/source identity. Call with an already canonicalized URL."""
    if not namespace.strip():
        raise ValueError("Namespace must not be empty")
    return _sha256(f"{namespace.strip()}|{canonical_url}")


@dataclass(frozen=True)
class Chunk:
    heading_path: str
    text: str


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    source_id: str
    namespace: str
    canonical_url: str
    heading_path: str
    text: str
    content_hash: str


def build_chunk_records(
    *,
    namespace: str,
    canonical_url: str,
    chunks: list[Chunk],
) -> list[ChunkRecord]:
    """Create deterministic records and suppress exact duplicates per section."""
    normalized_url = canonicalize_url(canonical_url)
    page_id = source_id(namespace, normalized_url)
    records: list[ChunkRecord] = []
    seen: set[str] = set()

    for chunk in chunks:
        clean_text = re.sub(r"\s+", " ", chunk.text).strip()
        normalized = normalize_text(clean_text)
        heading = re.sub(r"\s+", " ", chunk.heading_path).strip()
        if not normalized:
            continue

        # Heading path differentiates intentional repeated wording in separate sections.
        identity = f"{namespace}|{normalized_url}|{normalize_text(heading)}|{normalized}"
        chunk_id = _sha256(identity)
        if chunk_id in seen:
            continue
        seen.add(chunk_id)

        records.append(
            ChunkRecord(
                chunk_id=chunk_id,
                source_id=page_id,
                namespace=namespace,
                canonical_url=normalized_url,
                heading_path=heading,
                text=clean_text,
                content_hash=_sha256(normalized),
            )
        )
    return records


def plan_source_sync(
    *,
    namespace: str,
    canonical_url: str,
    chunks: list[Chunk],
    existing_active_chunk_ids: set[str],
) -> dict[str, object]:
    """Return a dry-run upsert/retirement plan for one source only.

    The caller must stage and verify all `upsert` records before retiring the
    listed IDs. Do not call this with IDs from other sources or namespaces.
    """
    records = build_chunk_records(
        namespace=namespace,
        canonical_url=canonical_url,
        chunks=chunks,
    )
    current_ids = {record.chunk_id for record in records}
    upsert = [record for record in records]
    retire_after_commit = sorted(existing_active_chunk_ids - current_ids)
    return {
        "namespace": namespace,
        "canonical_url": canonicalize_url(canonical_url),
        "source_id": source_id(namespace, canonicalize_url(canonical_url)),
        "upsert": upsert,
        "retire_after_commit": retire_after_commit,
        "active_chunk_count_after_commit": len(current_ids),
    }
