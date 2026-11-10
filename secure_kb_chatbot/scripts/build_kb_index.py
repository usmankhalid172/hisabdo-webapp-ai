"""Build the search index for one knowledge-base version.

    python scripts/build_kb_index.py kb/v1               # validate + index, do not switch
    python scripts/build_kb_index.py kb/v1 --activate    # ...and make it the live version
    python scripts/build_kb_index.py --activate-version 1.0.0   # roll back/forward without re-indexing
    python scripts/build_kb_index.py --list

Needs GEMINI_API_KEY (to create embeddings). Only entries with status "verified",
a verifier and a date are indexed; drafts are counted and skipped.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatbot.config import Settings  # noqa: E402
from chatbot.embeddings import EmbeddingUnavailable, GeminiEmbedder  # noqa: E402
from chatbot.kb import KBError  # noqa: E402
from chatbot.repository import Repository  # noqa: E402
from chatbot.retrieval import build_index  # noqa: E402
from chatbot.vector_store import VectorStore  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kb_dir", nargs="?", help="KB version folder, e.g. kb/v1")
    ap.add_argument("--activate", action="store_true", help="make this version live after indexing")
    ap.add_argument("--activate-version", help="switch the live version to one already indexed")
    ap.add_argument("--list", action="store_true", help="show indexed versions")
    args = ap.parse_args()

    settings = Settings.from_env()
    store = VectorStore(Repository(os.environ.get("CHATBOT_DB", ROOT / "data" / "app.db")))

    if args.list or args.activate_version:
        if args.activate_version:
            try:
                store.activate(args.activate_version)
            except ValueError as e:
                print(f"ERROR: {e}")
                return 1
        active = store.active_version()
        for version, count in sorted(store.versions().items()):
            print(f"{'*' if version == active else ' '} {version}: {count} chunks")
        print(f"Active version: {active}")
        return 0

    if not args.kb_dir:
        ap.error("kb_dir is required (or use --list / --activate-version)")
    try:
        embedder = GeminiEmbedder(settings.embedding_model, settings.embedding_dim)
        version, indexed, drafts = build_index(store, embedder, args.kb_dir)
    except KBError as e:
        print(f"ERROR: {e}")
        return 1
    except EmbeddingUnavailable as e:
        print(f"ERROR: {e}")
        return 1
    print(f"KB version {version}: {indexed} chunks indexed from verified entries, {drafts} draft entries skipped.")
    if indexed == 0:
        print("ERROR: nothing to index. Mark entries as verified (status, verified_by, verified_on) first.")
        return 1

    if args.activate:
        store.activate(version)
        print(f"Version {version} is now LIVE.")
    else:
        print(f"Not live yet (live version: {store.active_version()}). Re-run with --activate to switch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
