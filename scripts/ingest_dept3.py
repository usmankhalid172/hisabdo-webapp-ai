"""Automated, repeatable ingestion for the Department 3 knowledge base (docs/dept3-ingestion-checklist.md).

    python scripts/ingest_dept3.py --fetch                 # fetch every approved source today, clean, embed, publish
    python scripts/ingest_dept3.py --offline               # rebuild from the latest saved snapshots
    python scripts/ingest_dept3.py --fetch --dry-run       # everything except publishing (report only)

Stages, each captured in the execution report (data/kb/dept3/ingestion/ingest_<run>.json and .md):
  1 sources    approved rows of data/knowledge_source_audit.csv; sources added / removed since the last run
  2 fetch      per source, 2 retries; a failed page keeps its last good snapshot and is marked stale
  3 clean      per source; a parse error keeps that source's previous records (stale) instead of dropping them
  4 dedupe     exact and near duplicates removed (most authoritative / newest copy kept); conflicts flagged
  5 records    standardized records (schema v1.0), schema errors excluded and listed
  6 diff       records added / modified / deleted against the previous knowledge set
  7 vectors    embeddings checked per record (dimension, finite values, non-zero norm); errors excluded and listed;
               index manifest written (model, file hash, parameters, environment, checksum)
  8 publish    only if gates pass: >= 80% of the previous record count, no schema errors in published records,
               privacy scan clean. Otherwise nothing is replaced and the report says why.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_dept3_knowledge_set as B  # noqa: E402
import clean_knowledge_sources as C  # noqa: E402
from src.financial_assistant.grounding import retrieval as RT  # noqa: E402

EMBED_DIM = 384
MIN_KEEP = 0.8


def _fetch_with_retry(source, snap_dir: Path, fetcher, retries: int = 2) -> str | None:
    last = None
    for attempt in range(retries + 1):
        try:
            fetcher(source, snap_dir)
            return None
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {str(exc)[:120]}"
            time.sleep(0.5 * attempt)
    return last


def previous_snapshot(root: Path, source_id: str, before: str) -> Path | None:
    for d in sorted((d for d in root.iterdir() if d.is_dir() and d.name < before), reverse=True):
        if (d / f"{source_id}.html").exists():
            return d / f"{source_id}.html"
    return None


def embed_and_check(records: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Embeds every record; a vector that is the wrong size, not finite, or zero is a parsing error."""
    try:
        from fastembed import TextEmbedding
    except Exception as exc:  # noqa: BLE001
        return records, [], {"status": "skipped", "reason": f"fastembed unavailable: {type(exc).__name__}"}
    model = TextEmbedding(RT.BGE)
    texts = [RT.passage({"title": r["title"], "heading": r["heading"], "body": r["content"].split("\n\n", 1)[1]})
             for r in records]
    t0 = time.perf_counter()
    good, errors, vectors = [], [], []
    for r, t in zip(records, texts):
        try:
            v = np.array(list(model.embed([t]))[0], dtype=np.float32)
            if v.shape != (EMBED_DIM,):
                raise ValueError(f"dimension {v.shape}")
            if not np.all(np.isfinite(v)):
                raise ValueError("non-finite values")
            if float(np.linalg.norm(v)) == 0.0:
                raise ValueError("zero vector")
            vectors.append(v / np.linalg.norm(v))
            good.append(r)
        except Exception as exc:  # noqa: BLE001
            errors.append({"record_id": r["record_id"], "error": f"{type(exc).__name__}: {exc}"[:160]})
    matrix = np.stack(vectors) if vectors else np.zeros((0, EMBED_DIM), np.float32)
    info = {"status": "ok", "vectors": len(vectors), "seconds": round(time.perf_counter() - t0, 1),
            "checksum": hashlib.sha256(np.round(matrix, 5).tobytes()).hexdigest()[:16]}
    return good, errors, info


def model_file_hash() -> dict:
    import os
    root = Path(os.environ.get("FASTEMBED_CACHE_PATH", Path(os.environ.get("TEMP", "/tmp")) / "fastembed_cache"))
    files = sorted(root.glob("models--qdrant--bge-small-en-v1.5-onnx-q/snapshots/*/model_optimized.onnx"))
    if not files:
        return {"onnx_file": None}
    f = files[-1]
    return {"onnx_file": f"{f.parent.parent.parent.name}/snapshots/{f.parent.name}/{f.name}",
            "onnx_sha256": hashlib.sha256(f.read_bytes()).hexdigest()}


def environment() -> dict:
    vers = {"python": platform.python_version()}
    for mod in ("fastembed", "onnxruntime", "numpy", "tokenizers", "bs4"):
        try:
            vers[mod] = __import__(mod).__version__
        except Exception:  # noqa: BLE001
            vers[mod] = None
    return vers


def run(fetch: bool, dry_run: bool, snapshots_root: Path = C.SNAPSHOTS, out_root: Path = ROOT / "data" / "kb",
        today: date | None = None, fetcher=C.fetch, sources=None, embed: bool = True) -> dict:
    today = today or date.today()
    t_start = time.perf_counter()
    rep = {"run_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"), "mode": "fetch" if fetch
           else "offline", "dry_run": dry_run, "stages": {}, "published": False, "gate_failures": []}
    sources = sources if sources is not None else C.approved_sources()
    prev_path = out_root / "dept3" / "knowledge_set.jsonl"
    previous = [json.loads(l) for l in prev_path.read_text(encoding="utf-8").splitlines() if l.strip()] \
        if prev_path.exists() else []
    prev_sources = {r["source_id"] for r in previous}
    now_sources = {s.source_id for s in sources}
    rep["stages"]["sources"] = {"approved": len(sources), "added": sorted(now_sources - prev_sources),
                                "removed": sorted(prev_sources - now_sources) if previous else []}

    # 2 fetch
    snapshots_root.mkdir(parents=True, exist_ok=True)
    if fetch:
        snap_dir = snapshots_root / today.isoformat()
        snap_dir.mkdir(parents=True, exist_ok=True)
        failed = []
        for s in sources:
            err = _fetch_with_retry(s, snap_dir, fetcher)
            if err:
                prev = previous_snapshot(snapshots_root, s.source_id, today.isoformat())
                if prev:
                    shutil.copy(prev, snap_dir / f"{s.source_id}.html")
                failed.append({"source_id": s.source_id, "url": s.url, "error": err,
                               "fallback": f"stale snapshot {prev.parent.name}" if prev else "none: source skipped"})
        rep["stages"]["fetch"] = {"fetched": len(sources) - len(failed), "failed_pages": failed}
    else:
        snap_dir = sorted(d for d in snapshots_root.iterdir() if d.is_dir())[-1]
        rep["stages"]["fetch"] = {"skipped": f"offline, snapshots {snap_dir.name}", "failed_pages": []}
    retrieved_on = date.fromisoformat(snap_dir.name)

    # 3 clean
    chunks, parse_errors, warnings, stale_sources = [], [], [], []
    for s in sources:
        page_file = snap_dir / f"{s.source_id}.html"
        try:
            if not page_file.exists():
                raise FileNotFoundError("no snapshot")
            cs, r = C.clean_source(s, page_file.read_text(encoding="utf-8"), retrieved_on, {x.url for x in sources})
            if not cs:
                raise ValueError("no content extracted")
            chunks += cs
            warnings += [f"{s.source_id}: {w}" for w in r["warnings"] if w.startswith("NOT FOUND")]
        except Exception as exc:  # noqa: BLE001
            parse_errors.append({"source_id": s.source_id, "error": f"{type(exc).__name__}: {exc}"[:160]})
            stale_sources.append(s.source_id)
    rep["stages"]["clean"] = {"chunks": len(chunks), "parse_errors": parse_errors,
                              "meaning_check_failures": warnings}

    # 4 dedupe + conflicts
    priority = {s.source_id: s.priority for s in sources}
    kept, duplicates = C.remove_duplicates(chunks, priority)
    conflicts = C.flag_conflicts(kept)
    for c in kept:
        c.content_sha256 = hashlib.sha256(f"{c.heading}\n{c.body}".encode()).hexdigest()
    rep["stages"]["dedupe"] = {"duplicates": duplicates, "conflicts": [c["fact"] for c in conflicts]}

    # 5 records
    from dataclasses import asdict
    schema = json.loads(B.SCHEMA.read_text(encoding="utf-8"))
    records, schema_errors, purged = [], [], []
    for c in (asdict(k) for k in kept):
        if B.PROMO.search(c["heading"]) or B.PROMO.search(c["body"]):
            purged.append(c["id"])
            continue
        r = B.to_record(c)
        errs = B.validate(r, schema)
        (schema_errors.append({"record_id": r["record_id"], "errors": errs}) if errs else records.append(r))
    carried = [r for r in previous if r["source_id"] in stale_sources]   # parse failure: keep last good records
    records += carried
    rep["stages"]["records"] = {"records": len(records), "promotional_purged": purged, "schema_errors": schema_errors,
                                "carried_forward_from_previous_run": len(carried)}

    # 6 diff
    old = {r["record_id"]: r["content_sha256"] for r in previous}
    new = {r["record_id"]: r["content_sha256"] for r in records}
    rep["stages"]["diff"] = {"added": sorted(set(new) - set(old)), "deleted": sorted(set(old) - set(new)),
                             "modified": sorted(k for k in set(new) & set(old) if new[k] != old[k]),
                             "unchanged": sum(1 for k in set(new) & set(old) if new[k] == old[k])}

    # 7 vectors + manifest
    if embed:
        records, vector_errors, vinfo = embed_and_check(records)
    else:
        vector_errors, vinfo = [], {"status": "skipped", "reason": "embed=False"}
    manifest = {
        "kb_version": RT.kb_version([{"content_sha256": r["content_sha256"]} for r in records]),
        "records": len(records), "snapshot": snap_dir.name, "schema_version": B.SCHEMA_VERSION,
        "embedding": {"library": "fastembed", "model": RT.BGE, "resolved_repo": "qdrant/bge-small-en-v1.5-onnx-q",
                      **model_file_hash(), "dimensions": EMBED_DIM, "normalisation": "L2",
                      "query_prefix": RT.BGE_QUERY_PREFIX, "similarity": "cosine (dot product of unit vectors)",
                      "passage_text": "title. heading.\\nbody", **vinfo},
        "lexical": {"algorithm": "BM25", "k1": 1.5, "b": 0.75, "saturation_k": 5.0,
                    "tokenizer": "[a-z0-9]+|Urdu letters, English and Roman Urdu stop words removed"},
        "retrieval": {"hybrid_alpha": RT.HYBRID_ALPHA, "threshold": RT.HYBRID_THRESHOLD, "top_k": RT.HYBRID_TOP_K,
                      "margin": RT.HYBRID_MARGIN, "candidates": RT.CANDIDATES,
                      "lexical_fallback": {"threshold": RT.LEXICAL_THRESHOLD, "top_k": RT.LEXICAL_TOP_K,
                                           "margin": RT.LEXICAL_MARGIN}},
        "chunking": {"faq": "one question and answer per record, never split", "sections": f"<= {C.MAX_CHARS} chars, "
                     "split at sub-headings then paragraphs, never inside a sentence", "overlap": "none",
                     "short_intros": "sections < 150 chars merged into the next section"},
        "environment": environment()}
    rep["stages"]["vectors"] = {**vinfo, "vector_errors": vector_errors}

    # 8 gates + publish
    if previous and len(records) < MIN_KEEP * len(previous):
        rep["gate_failures"].append(f"record count {len(records)} < {MIN_KEEP:.0%} of previous {len(previous)}")
    pii = [r["record_id"] for r in records if RT._PII.search(r["content"].replace("hisabdo.app@gmail.com", ""))]
    if pii:
        rep["gate_failures"].append(f"personal identifiers in {pii[:5]}")
    out_dir = out_root / "dept3"
    if not dry_run and not rep["gate_failures"]:
        out_dir.mkdir(parents=True, exist_ok=True)
        with (out_dir / "knowledge_set.jsonl").open("w", encoding="utf-8", newline="\n") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        (out_dir / "index_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
        rep["published"] = True
    rep["manifest"] = manifest
    rep["seconds"] = round(time.perf_counter() - t_start, 1)
    return rep


def markdown(rep: dict) -> str:
    s = rep["stages"]
    d = s["diff"]
    lines = [f"# Ingestion execution report · {rep['run_at']}", "",
             f"* Mode: **{rep['mode']}**{' (dry run)' if rep['dry_run'] else ''} · published: **{rep['published']}** · "
             f"{rep['seconds']} s",
             f"* Gate failures: {rep['gate_failures'] or 'none'}", "",
             "| Stage | Result |", "|---|---|",
             f"| Sources | {s['sources']['approved']} approved · added {s['sources']['added'] or 'none'} · removed "
             f"{s['sources']['removed'] or 'none'} |",
             f"| Fetch | {s['fetch'].get('fetched', s['fetch'].get('skipped'))} · failed pages: "
             f"{len(s['fetch']['failed_pages'])} |",
             f"| Clean | {s['clean']['chunks']} chunks · parse errors: {len(s['clean']['parse_errors'])} · meaning-check "
             f"failures: {len(s['clean']['meaning_check_failures'])} |",
             f"| Dedupe | duplicates removed: {len(s['dedupe']['duplicates'])} · conflicts flagged: "
             f"{s['dedupe']['conflicts'] or 'none'} |",
             f"| Records | {s['records']['records']} · promotional purged: {len(s['records']['promotional_purged'])} · "
             f"schema errors: {len(s['records']['schema_errors'])} · carried forward: "
             f"{s['records']['carried_forward_from_previous_run']} |",
             f"| Diff | added {len(d['added'])} · modified {len(d['modified'])} · deleted {len(d['deleted'])} · "
             f"unchanged {d['unchanged']} |",
             f"| Vectors | {s['vectors'].get('vectors', s['vectors'].get('reason'))} · errors: "
             f"{len(s['vectors']['vector_errors'])} · checksum {s['vectors'].get('checksum', '-')} |", ""]
    for title, items in (("Failed pages", s["fetch"]["failed_pages"]), ("Parse errors", s["clean"]["parse_errors"]),
                         ("Duplicates", s["dedupe"]["duplicates"]), ("Vector errors", s["vectors"]["vector_errors"]),
                         ("Modified records", d["modified"]), ("Added records", d["added"]),
                         ("Deleted records", d["deleted"])):
        if items:
            lines += [f"## {title}", ""] + [f"* {json.dumps(i, ensure_ascii=False)[:200]}" for i in items[:40]] + [""]
    return "\n".join(lines) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--fetch", action="store_true")
    g.add_argument("--offline", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rep = run(fetch=a.fetch, dry_run=a.dry_run)
    out = ROOT / "data" / "kb" / "dept3" / "ingestion"
    out.mkdir(parents=True, exist_ok=True)
    stem = f"ingest_{datetime.now().strftime('%Y-%m-%d_%H%M')}_{rep['mode']}{'_dryrun' if a.dry_run else ''}"
    (out / f"{stem}.json").write_text(json.dumps(rep, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / f"{stem}.md").write_text(markdown(rep), encoding="utf-8")
    print(markdown(rep))
    return 0 if not rep["gate_failures"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
