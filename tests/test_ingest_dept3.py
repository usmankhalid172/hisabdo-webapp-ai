"""Automated ingestion: new, modified, deleted sources; failed pages; duplicates; parse and vector errors."""

import json
import shutil
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import clean_knowledge_sources as C  # noqa: E402
import ingest_dept3 as I  # noqa: E402

SNAP = ROOT / "data" / "kb" / "sources" / "2026-10-27"
TODAY = date(2026, 11, 10)


@pytest.fixture()
def env(tmp_path):
    snaps = tmp_path / "sources"
    shutil.copytree(SNAP, snaps / SNAP.name)
    out = tmp_path / "kb"
    (out / "dept3").mkdir(parents=True)
    shutil.copy(ROOT / "data" / "kb" / "dept3" / "knowledge_set.jsonl", out / "dept3" / "knowledge_set.jsonl")
    return snaps, out


def copy_fetcher(edit=None, fail=()):
    def fetch(source, snap_dir):
        if source.source_id in fail:
            raise TimeoutError("read timed out")
        html = (SNAP / f"{source.source_id}.html").read_text(encoding="utf-8")
        (snap_dir / f"{source.source_id}.html").write_text(edit(source, html) if edit else html, encoding="utf-8")
    return fetch


def go(env, **kw):
    snaps, out = env
    return I.run(fetch=kw.pop("fetch", True), dry_run=kw.pop("dry_run", False), snapshots_root=snaps, out_root=out,
                 today=TODAY, embed=kw.pop("embed", False), **kw)


def test_unchanged_sources_give_an_empty_diff_and_publish(env):
    rep = go(env, fetcher=copy_fetcher())
    d = rep["stages"]["diff"]
    assert (d["added"], d["modified"], d["deleted"], d["unchanged"]) == ([], [], [], 363)
    assert rep["published"] and not rep["gate_failures"]
    assert (env[1] / "dept3" / "index_manifest.json").exists()


def test_failed_page_is_captured_and_last_good_snapshot_used(env):
    rep = go(env, fetcher=copy_fetcher(fail={"OFF-01"}))
    failed = rep["stages"]["fetch"]["failed_pages"]
    assert [f["source_id"] for f in failed] == ["OFF-01"]
    assert "TimeoutError" in failed[0]["error"] and "stale snapshot 2026-10-27" in failed[0]["fallback"]
    assert rep["stages"]["diff"]["deleted"] == []          # nothing lost because one page failed


def test_modified_page_is_detected(env):
    edit = lambda s, h: h.replace("free offline-first khata", "free offline-first digital khata") \
        if s.source_id == "OFF-01" else h
    rep = go(env, fetcher=copy_fetcher(edit))
    assert rep["stages"]["diff"]["modified"] == ["off-01-001-what-is-hisabdo"]


def test_removed_source_is_reported_and_its_records_deleted(env):
    sources = [s for s in C.approved_sources() if s.source_id != "BLOG-05"]
    rep = go(env, fetcher=copy_fetcher(), sources=sources)
    assert rep["stages"]["sources"]["removed"] == ["BLOG-05"]
    assert rep["stages"]["diff"]["deleted"] and all(r.startswith("blog-05") for r in rep["stages"]["diff"]["deleted"])


def test_parse_error_keeps_previous_records(env):
    edit = lambda s, h: "<html><body></body></html>" if s.source_id == "OFF-02" else h
    rep = go(env, fetcher=copy_fetcher(edit))
    assert [e["source_id"] for e in rep["stages"]["clean"]["parse_errors"]] == ["OFF-02"]
    assert rep["stages"]["records"]["carried_forward_from_previous_run"] > 0
    assert rep["stages"]["diff"]["deleted"] == []


def test_duplicates_are_captured_and_not_published(env):
    rep = go(env, fetcher=copy_fetcher())
    dups = rep["stages"]["dedupe"]["duplicates"]
    assert len(dups) == 2 and all({"removed", "duplicate_of", "reason"} <= set(d) for d in dups)
    published = {json.loads(l)["record_id"] for l in (env[1] / "dept3" / "knowledge_set.jsonl")
                 .read_text(encoding="utf-8").splitlines()}
    assert not {d["removed"] for d in dups} & published and {d["duplicate_of"] for d in dups} <= published


def test_large_drop_blocks_publishing(env):
    sources = C.approved_sources()[:5]
    rep = go(env, fetcher=copy_fetcher(), sources=sources)
    assert rep["gate_failures"] and not rep["published"]
    assert len((env[1] / "dept3" / "knowledge_set.jsonl").read_text(encoding="utf-8").splitlines()) == 363


def test_vector_errors_are_captured(monkeypatch):
    class Fake:
        def __init__(self, *_):
            self.n = 0

        def embed(self, texts):
            self.n += 1
            if self.n == 2:
                return [np.full(384, np.nan)]
            if self.n == 3:
                return [np.zeros(384)]
            if self.n == 4:
                return [np.ones(10)]
            return [np.ones(384)]
    import fastembed
    monkeypatch.setattr(fastembed, "TextEmbedding", Fake)
    recs = [json.loads(l) for l in (ROOT / "data" / "kb" / "dept3" / "knowledge_set.jsonl")
            .read_text(encoding="utf-8").splitlines()[:5]]
    good, errors, info = I.embed_and_check(recs)
    assert len(good) == 2 and [e["error"].split(":")[1].strip() for e in errors] == \
        ["non-finite values", "zero vector", "dimension (10,)"]
