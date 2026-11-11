
"""Department 3 repeatable HisabDo knowledge ingestion.

Default mode builds deterministic staging chunks and metadata.
Real embeddings require an approved 40-character Hugging Face commit SHA.

This script never changes the live chatbot index.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "faq_docs.json"
OUT = ROOT / "data" / "department3_ingestion"
STATE = OUT / "state.json"
CHUNKS = OUT / "chunks.json"
FAILURES = OUT / "failures.json"
EMBEDDINGS = OUT / "embeddings.npy"
REPORT = ROOT / "docs" / "department3_automated_ingestion_execution_report.md"

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSION = 384

CONFIG = {
    "faq": (250, 30),
    "accounting_feature_table": (350, 40),
    "workflow_guideline": (450, 60),
    "long_form_documentation": (600, 80),
}

TOKEN_RE = re.compile(r"\S+")
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_approved(doc: dict[str, Any]) -> bool:
    return (
        doc.get("verified") is True
        and doc.get("content_status") == "approved"
    )


def classify(doc: dict[str, Any]) -> str:
    explicit = str(doc.get("content_type", "")).strip().lower()

    aliases = {
        "structured_faq": "faq",
        "product_faq": "faq",
        "finance_faq": "faq",
        "faq": "faq",
        "table": "accounting_feature_table",
        "feature_table": "accounting_feature_table",
        "workflow": "workflow_guideline",
        "guideline": "workflow_guideline",
        "documentation": "long_form_documentation",
        "long_form": "long_form_documentation",
    }

    if explicit in CONFIG:
        return explicit

    if explicit in aliases:
        return aliases[explicit]

    kind = str(doc.get("type", "")).lower()
    category = str(doc.get("category", "")).lower()

    if "table" in kind or "table" in category:
        return "accounting_feature_table"

    if (
        "workflow" in kind
        or "workflow" in category
        or "guideline" in kind
    ):
        return "workflow_guideline"

    if "documentation" in kind or "long" in kind:
        return "long_form_documentation"

    return "faq"


def content_text(doc: dict[str, Any]) -> str:
    title = str(doc.get("title", "")).strip()
    body = doc.get("text", "")

    if isinstance(body, list):
        body = "\n".join(
            " | ".join(map(str, row))
            if isinstance(row, (list, tuple))
            else json.dumps(
                row,
                ensure_ascii=False,
                sort_keys=True,
            )
            for row in body
        )
    elif isinstance(body, dict):
        body = json.dumps(
            body,
            ensure_ascii=False,
            sort_keys=True,
        )

    if not isinstance(body, str):
        raise ValueError(
            "document text must be a string, list, or object"
        )

    body = body.strip()

    if not title or not body:
        raise ValueError(
            "document requires non-empty title and text"
        )

    return f"{title}\n{body}"


def split_chunks(
    text: str,
    size: int,
    overlap: int,
) -> list[str]:
    words = TOKEN_RE.findall(text)

    if not words:
        return []

    step = size - overlap

    if step <= 0:
        raise ValueError(
            "chunk overlap must be smaller than chunk size"
        )

    return [
        " ".join(words[i:i + size])
        for i in range(0, len(words), step)
    ]


def load_json(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(
        path.read_text(encoding="utf-8-sig")
    )

    if not isinstance(raw, list):
        raise ValueError(
            "knowledge source root must be a JSON array"
        )

    return raw


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")

    try:
        temp.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


def check_approved_pages(
    urls: set[str],
) -> list[dict[str, str]]:
    """Check approved source URLs against an HTTPS domain allowlist."""

    allowed = {
        "hisabdo.app",
        "www.hisabdo.app",
        "openstax.org",
        "www.openstax.org",
    }

    errors = []

    for url in sorted(urls):
        try:
            parsed = urlparse(url)

            if (
                parsed.scheme != "https"
                or parsed.hostname not in allowed
                or parsed.username is not None
                or parsed.password is not None
            ):
                errors.append({
                    "source": url,
                    "category": "page_rejected",
                    "error": (
                        "URL is not HTTPS on the approved "
                        "source-domain allowlist"
                    ),
                })
                continue

            request = Request(
                url,
                headers={
                    "User-Agent": (
                        "HisabDo-Dept3-Knowledge-Ingest/1.0"
                    )
                },
            )

            with urlopen(request, timeout=15) as response:
                if response.status < 200 or response.status >= 300:
                    raise ValueError(
                        f"unexpected HTTP status {response.status}"
                    )

                response.read(1)

        except (
            HTTPError,
            URLError,
            TimeoutError,
            ValueError,
            OSError,
        ) as exc:
            errors.append({
                "source": url,
                "category": "page_fetch",
                "error": f"{type(exc).__name__}: {exc}",
            })

    return errors


def build_embeddings(
    chunks: list[dict[str, Any]],
    revision: str,
) -> str:
    """Build and validate embeddings before replacing the saved matrix."""

    import numpy as np
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(
        MODEL_ID,
        revision=revision,
        device="cpu",
    )

    if chunks:
        vectors = model.encode(
            [chunk["text"] for chunk in chunks],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        vectors = np.asarray(vectors, dtype=np.float32)
    else:
        vectors = np.empty(
            (0, DIMENSION),
            dtype=np.float32,
        )

    expected_shape = (len(chunks), DIMENSION)

    if vectors.shape != expected_shape:
        raise ValueError(
            f"unexpected embedding shape: {vectors.shape}; "
            f"expected {expected_shape}"
        )

    if not np.isfinite(vectors).all():
        raise ValueError(
            "embeddings contain NaN or infinite values"
        )

    if len(vectors):
        norms = np.linalg.norm(vectors, axis=1)

        if np.any(norms <= 1e-12):
            raise ValueError(
                "one or more embeddings have zero norm"
            )

        if not np.allclose(norms, 1.0, atol=1e-4):
            raise ValueError(
                "embeddings are not L2-normalized"
            )

    temp = EMBEDDINGS.with_suffix(".npy.tmp")

    try:
        with temp.open("wb") as file:
            np.save(
                file,
                vectors,
                allow_pickle=False,
            )

        temp.replace(EMBEDDINGS)

    finally:
        if temp.exists():
            temp.unlink()

    return "built"


def run(
    build_embeddings_requested: bool = False,
    model_revision: str | None = None,
    check_pages: bool = False,
) -> dict[str, Any]:

    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / "docs").mkdir(exist_ok=True)

    old_state = (
        json.loads(STATE.read_text(encoding="utf-8"))
        if STATE.exists()
        else {"documents": {}}
    )

    if not isinstance(old_state, dict):
        raise ValueError("invalid previous ingestion state")

    old_docs = old_state.get("documents", {})

    if not isinstance(old_docs, dict):
        raise ValueError("invalid previous ingestion documents")

    failures: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []

    try:
        source_docs = load_json(SOURCE)

    except Exception as exc:
        atomic_json(FAILURES, [{
            "source": str(SOURCE.relative_to(ROOT)),
            "category": "source_parse",
            "error": str(exc),
        }])
        raise

    previous_chunks = (
        json.loads(CHUNKS.read_text(encoding="utf-8"))
        if CHUNKS.exists()
        else []
    )

    if not isinstance(previous_chunks, list):
        raise ValueError("invalid previous chunks artifact")

    cached_chunks: dict[str, list[dict[str, Any]]] = {}

    for chunk in previous_chunks:
        if not isinstance(chunk, dict):
            continue

        document_id = chunk.get("document_id")

        if document_id:
            cached_chunks.setdefault(
                document_id,
                [],
            ).append(chunk)

    active: dict[str, dict[str, Any]] = {}
    chunks: list[dict[str, Any]] = []

    duplicate_hashes: dict[str, str] = {}
    source_ids: set[str] = set()
    seen_ids: set[str] = set()
    excluded_ids: list[str] = []

    duplicate_count = 0
    unverified_count = 0
    unchanged_count = 0
    modified_count = 0
    new_count = 0

    approved_urls: set[str] = set()

    def count_document(prior: dict[str, Any], digest: str) -> None:
        nonlocal new_count, modified_count, unchanged_count

        if not prior:
            new_count += 1
        elif prior.get("source_hash") == digest:
            unchanged_count += 1
        else:
            modified_count += 1

    for position, doc in enumerate(source_docs):

        if not isinstance(doc, dict):
            failures.append({
                "source": f"record[{position}]",
                "category": "record_parse",
                "error": "record must be an object",
            })
            continue

        doc_id = str(doc.get("id", "")).strip()

        if not doc_id:
            failures.append({
                "source": f"record[{position}]",
                "category": "record_parse",
                "error": "missing stable id",
            })
            continue

        source_ids.add(doc_id)

        if doc_id in seen_ids:
            failures.append({
                "source": doc_id,
                "category": "duplicate_id",
                "error": "duplicate document ID in source",
            })
            continue

        seen_ids.add(doc_id)

        if not is_approved(doc):
            unverified_count += 1
            excluded_ids.append(doc_id)
            continue

        prior = old_docs.get(doc_id, {})

        try:
            text = content_text(doc)

            digest = sha256(
                json.dumps(
                    doc,
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )

            content_digest = sha256(
                re.sub(
                    r"\s+",
                    " ",
                    text,
                ).strip().casefold()
            )

            kind = classify(doc)
            size, overlap = CONFIG[kind]

            config_hash = sha256(
                json.dumps(
                    {
                        "type": kind,
                        "size": size,
                        "overlap": overlap,
                    },
                    sort_keys=True,
                )
            )

            metadata = {
                "source_hash": digest,
                "content_hash": content_digest,
                "chunk_config_hash": config_hash,
                "title": doc["title"],
                "source_url": (
                    doc.get("source_url") or doc.get("url")
                ),
                "section": doc.get("section"),
                "category": doc.get("category"),
                "language": doc.get("language", "en"),
                "last_updated": doc.get("last_updated"),
                "product_area": doc.get("product_area"),
                "content_type": kind,
                "chunk_count": 0,
                "verified": True,
                "duplicate_of": None,
            }

            source_url = metadata["source_url"]

            if source_url:
                approved_urls.add(str(source_url))

            duplicate_of = duplicate_hashes.get(content_digest)

            # Exact duplicate: retain metadata, omit duplicate chunks.
            if duplicate_of:
                metadata["duplicate_of"] = duplicate_of
                active[doc_id] = metadata
                duplicate_count += 1

                count_document(prior, digest)

                warnings.append({
                    "source": doc_id,
                    "category": "duplicate_content",
                    "message": (
                        f"Exact normalized content duplicates "
                        f"{duplicate_of}; source retained and "
                        "duplicate chunks omitted."
                    ),
                })
                continue

            can_reuse = (
                prior.get("source_hash") == digest
                and prior.get("chunk_config_hash") == config_hash
                and doc_id in cached_chunks
            )

            if can_reuse:
                doc_chunks = cached_chunks[doc_id]

                if not doc_chunks:
                    raise ValueError(
                        "cached document has no chunks"
                    )

            else:
                bodies = split_chunks(
                    text,
                    size,
                    overlap,
                )

                if not bodies:
                    raise ValueError("no chunks produced")

                doc_chunks = []

                for index, body in enumerate(bodies):
                    doc_chunks.append({
                        "chunk_id": (
                            f"{doc_id}::chunk-{index:04d}"
                        ),
                        "document_id": doc_id,
                        "title": doc["title"],
                        "text": body,
                        "content_type": kind,
                        "chunk_index": index,
                        "chunk_size_tokens": size,
                        "overlap_tokens": overlap,
                        "source_url": source_url,
                        "section": metadata["section"],
                        "category": metadata["category"],
                        "language": metadata["language"],
                        "verified": True,
                        "source_hash": digest,
                    })

            metadata["chunk_count"] = len(doc_chunks)

            # Add only successfully processed documents to active state.
            active[doc_id] = metadata
            chunks.extend(doc_chunks)

            # Register content only after successful processing.
            duplicate_hashes[content_digest] = doc_id

            count_document(prior, digest)

        except Exception as exc:
            failures.append({
                "source": doc_id,
                "category": "chunk_parse",
                "error": f"{type(exc).__name__}: {exc}",
            })

            # Preserve the last known-good staged version when available.
            if prior and cached_chunks.get(doc_id):
                active[doc_id] = prior
                chunks.extend(cached_chunks[doc_id])

                old_content_hash = prior.get("content_hash")

                if old_content_hash:
                    duplicate_hashes.setdefault(
                        old_content_hash,
                        doc_id,
                    )

    deleted_ids = sorted(
        set(old_docs) - source_ids
    )

    removed_from_staging = sorted(
        set(old_docs) & set(excluded_ids)
    )

    if check_pages:
        failures.extend(
            check_approved_pages(approved_urls)
        )

    embedding_status = "not_requested"

    if build_embeddings_requested:

        if not model_revision or not SHA_RE.fullmatch(model_revision):
            embedding_status = "failed_missing_pinned_revision"

            failures.append({
                "source": "embedding_model",
                "category": "embedding_configuration",
                "error": (
                    "--model-revision must be an approved "
                    "40-character Hugging Face commit SHA"
                ),
            })

        elif failures:
            embedding_status = "skipped_due_to_ingestion_errors"

        else:
            try:
                embedding_status = build_embeddings(
                    chunks,
                    model_revision,
                )

            except Exception as exc:
                embedding_status = "failed"

                failures.append({
                    "source": "embedding_model",
                    "category": "vector_parsing_or_embedding",
                    "error": f"{type(exc).__name__}: {exc}",
                })

    if embedding_status != "built" and EMBEDDINGS.exists():
        EMBEDDINGS.unlink()

    metadata_failure_categories = {
        "source_parse",
        "record_parse",
        "duplicate_id",
        "chunk_parse",
    }

    metadata_ingestion_ok = not any(
        item["category"] in metadata_failure_categories
        for item in failures
    )

    previous_timestamp = old_state.get(
        "last_successful_metadata_ingestion_utc"
    )

    successful_timestamp = (
        datetime.now(timezone.utc).isoformat()
        if metadata_ingestion_ok
        else previous_timestamp
    )

    state = {
        "schema_version": 2,
        "source_file": str(SOURCE.relative_to(ROOT)),
        "source_file_hash": sha256(
            SOURCE.read_text(encoding="utf-8-sig")
        ),
        "documents": active,
        "embedding": {
            "model_id": MODEL_ID,
            "model_revision": (
                model_revision
                if embedding_status == "built"
                else "UNPINNED_NOT_BUILT"
            ),
            "dimension": DIMENSION,
            "normalization": "L2",
            "similarity": "cosine",
            "index_type": "flat_exact_staging",
            "dtype": "float32",
            "status": embedding_status,
            "vector_count": (
                len(chunks)
                if embedding_status == "built"
                else 0
            ),
        },
        "last_successful_metadata_ingestion_utc": (
            successful_timestamp
        ),
    }

    atomic_json(CHUNKS, chunks)
    atomic_json(STATE, state)
    atomic_json(FAILURES, failures)

    indexed_documents = sum(
        1
        for metadata in active.values()
        if metadata.get("chunk_count", 0) > 0
    )

    report = {
        "source_records": len(source_docs),
        "approved_indexed_documents": indexed_documents,
        "approved_staged_documents": len(active),
        "unverified_or_unapproved_excluded": unverified_count,
        "chunks": len(chunks),
        "new_documents": new_count,
        "modified_documents": modified_count,
        "unchanged_documents": unchanged_count,
        "deleted_documents": deleted_ids,
        "removed_from_staging": removed_from_staging,
        "duplicate_content_records": duplicate_count,
        "failures": len(failures),
        "warnings": len(warnings),
        "embedding_status": embedding_status,
        "embedding_model": MODEL_ID,
        "model_revision": model_revision or "UNPINNED_NOT_BUILT",
    }

    report_text = f"""# Department 3 Automated Ingestion Execution Report

Generated (UTC): {datetime.now(timezone.utc).isoformat()}

## Run result

| Metric | Result |
|---|---:|
| Source records read | {len(source_docs)} |
| Approved documents staged | {len(active)} |
| Approved documents indexed | {indexed_documents} |
| Unapproved documents excluded | {unverified_count} |
| Chunks generated | {len(chunks)} |
| New documents | {new_count} |
| Modified documents | {modified_count} |
| Unchanged documents | {unchanged_count} |
| Deleted source IDs | {len(deleted_ids)} |
| Removed from staging due to approval change | {len(removed_from_staging)} |
| Duplicate content records | {duplicate_count} |
| Failures | {len(failures)} |
| Warnings | {len(warnings)} |
| Embedding build | {embedding_status} |

## Embedding configuration

- Model: `{MODEL_ID}`
- Revision: `{model_revision or 'NOT PINNED'}`
- Dimension: {DIMENSION}
- Normalization: L2
- Similarity: cosine
- Vector dtype: float32
- Index: flat exact staging matrix
- Embedding status: {embedding_status}

## Incremental ingestion

Unchanged documents reuse cached chunks when their source hash
and chunk configuration match. Modified documents are rechunked.
Failed documents do not replace their previous successful staged
version when cached data is available.

Deleted source IDs are distinguished from documents excluded
because their approval status changed.

## Duplicate content

Exact normalized duplicates are retained in metadata but do not
generate duplicate chunks. They are reported as warnings, not failures.

{json.dumps(warnings, ensure_ascii=False, indent=2) if warnings else 'No duplicate-content warnings.'}

## Metadata ingestion timestamp

Last successful metadata ingestion:
`{successful_timestamp or 'No successful ingestion recorded'}`

## Production boundary

This script builds staging artifacts only. It does not update the
live chatbot retriever or production index. A production cutover still
requires an approved model revision, dependency lockfile, labeled
retrieval evaluation, and engineering approval.

## Deleted source IDs

{json.dumps(deleted_ids, ensure_ascii=False, indent=2)}

## Removed from staging

{json.dumps(removed_from_staging, ensure_ascii=False, indent=2)}

## Failure log

{json.dumps(failures, ensure_ascii=False, indent=2) if failures else 'No failures recorded.'}
"""

    REPORT.write_text(
        report_text,
        encoding="utf-8",
    )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--build-embeddings",
        action="store_true",
    )

    parser.add_argument(
        "--model-revision",
        default=None,
    )

    parser.add_argument(
        "--check-pages",
        action="store_true",
        help=(
            "Check approved source URLs using "
            "the HTTPS allowlist"
        ),
    )

    args = parser.parse_args()

    try:
        result = run(
            build_embeddings_requested=args.build_embeddings,
            model_revision=args.model_revision,
            check_pages=args.check_pages,
        )

    except Exception as exc:
        print(
            f"Ingestion failed: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )

    if result["failures"] > 0:
        return 1

    if result["embedding_status"].startswith("failed"):
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
