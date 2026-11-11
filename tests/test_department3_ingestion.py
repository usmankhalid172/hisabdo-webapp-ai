
"""Tests for Department 3 deterministic knowledge ingestion."""

import json

import pytest

from scripts import department3_ingestion as ingestion


@pytest.fixture
def isolated_ingestion(tmp_path, monkeypatch):
    root = tmp_path
    data_dir = root / "data"
    out_dir = data_dir / "department3_ingestion"
    docs_dir = root / "docs"

    data_dir.mkdir()
    docs_dir.mkdir()

    monkeypatch.setattr(ingestion, "ROOT", root)
    monkeypatch.setattr(ingestion, "SOURCE", data_dir / "faq_docs.json")
    monkeypatch.setattr(ingestion, "OUT", out_dir)
    monkeypatch.setattr(ingestion, "STATE", out_dir / "state.json")
    monkeypatch.setattr(ingestion, "CHUNKS", out_dir / "chunks.json")
    monkeypatch.setattr(ingestion, "FAILURES", out_dir / "failures.json")
    monkeypatch.setattr(ingestion, "EMBEDDINGS", out_dir / "embeddings.npy")
    monkeypatch.setattr(
        ingestion,
        "REPORT",
        docs_dir / "department3_automated_ingestion_execution_report.md",
    )

    def write_source(records):
        ingestion.SOURCE.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return write_source


def approved_doc(doc_id="faq-001", text="This is approved guidance."):
    return {
        "id": doc_id,
        "title": f"Title {doc_id}",
        "text": text,
        "verified": True,
        "content_status": "approved",
        "content_type": "faq",
    }


def test_approval_requires_verified_and_approved_status():
    assert ingestion.is_approved({
        "verified": True,
        "content_status": "approved",
    })

    assert not ingestion.is_approved({
        "verified": False,
        "content_status": "approved",
    })

    assert not ingestion.is_approved({
        "verified": True,
        "content_status": "pending",
    })


@pytest.mark.parametrize(
    ("content_type", "expected"),
    [
        ("faq", "faq"),
        ("structured_faq", "faq"),
        ("table", "accounting_feature_table"),
        ("workflow", "workflow_guideline"),
        ("documentation", "long_form_documentation"),
    ],
)
def test_content_classification(content_type, expected):
    assert ingestion.classify({"content_type": content_type}) == expected


def test_content_text_supports_list_and_dictionary():
    list_doc = {
        "title": "Features",
        "text": [["Feature A", "Available"], ["Feature B", "Pending"]],
    }
    dict_doc = {
        "title": "Details",
        "text": {"status": "active", "version": 2},
    }

    assert "Feature A | Available" in ingestion.content_text(list_doc)
    assert '"status": "active"' in ingestion.content_text(dict_doc)


def test_content_text_rejects_empty_title_or_body():
    with pytest.raises(ValueError):
        ingestion.content_text({"title": "", "text": "Some content"})

    with pytest.raises(ValueError):
        ingestion.content_text({"title": "Title", "text": "  "})


def test_split_chunks_respects_size_and_overlap():
    words = [f"word{i}" for i in range(11)]
    chunks = ingestion.split_chunks(" ".join(words), size=5, overlap=2)

    assert len(chunks) == 4
    assert chunks[0].split() == words[0:5]
    assert chunks[1].split() == words[3:8]
    assert chunks[2].split() == words[6:11]


def test_split_chunks_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        ingestion.split_chunks("some words", size=5, overlap=5)


def test_load_json_requires_array(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('{"not": "an array"}', encoding="utf-8")

    with pytest.raises(ValueError, match="JSON array"):
        ingestion.load_json(path)


def test_run_stages_only_approved_documents(isolated_ingestion):
    isolated_ingestion([
        approved_doc(),
        {
            "id": "faq-002",
            "title": "Unapproved",
            "text": "Do not stage this.",
            "verified": False,
            "content_status": "pending",
        },
    ])

    result = ingestion.run()

    state = json.loads(ingestion.STATE.read_text(encoding="utf-8"))
    chunks = json.loads(ingestion.CHUNKS.read_text(encoding="utf-8"))

    assert result["source_records"] == 2
    assert result["approved_indexed_documents"] == 1
    assert result["unverified_or_unapproved_excluded"] == 1
    assert len(chunks) == 1
    assert set(state["documents"]) == {"faq-001"}
    assert ingestion.REPORT.exists()


def test_second_run_reuses_unchanged_chunks(isolated_ingestion):
    isolated_ingestion([approved_doc()])

    first_result = ingestion.run()
    first_chunks = json.loads(
        ingestion.CHUNKS.read_text(encoding="utf-8")
    )

    second_result = ingestion.run()
    second_chunks = json.loads(
        ingestion.CHUNKS.read_text(encoding="utf-8")
    )

    assert first_result["new_documents"] == 1
    assert second_result["unchanged_documents"] == 1
    assert second_result["new_documents"] == 0
    assert first_chunks == second_chunks


def test_modified_document_is_rechunked(isolated_ingestion):
    isolated_ingestion([approved_doc(text="Original guidance.")])
    ingestion.run()

    isolated_ingestion([approved_doc(text="Updated guidance.")])
    result = ingestion.run()

    chunks = json.loads(ingestion.CHUNKS.read_text(encoding="utf-8"))

    assert result["modified_documents"] == 1
    assert "Updated guidance." in chunks[0]["text"]


def test_deleted_and_unapproved_documents_are_distinguished(
    isolated_ingestion,
):
    isolated_ingestion([
        approved_doc("faq-001"),
        approved_doc("faq-002"),
    ])
    ingestion.run()

    isolated_ingestion([
        {
            **approved_doc("faq-001"),
            "verified": False,
            "content_status": "pending",
        },
    ])

    result = ingestion.run()

    assert result["deleted_documents"] == ["faq-002"]
    assert result["removed_from_staging"] == ["faq-001"]


def test_duplicate_content_is_staged_only_once(isolated_ingestion):
    isolated_ingestion([
        dict(
            approved_doc("faq-001", "Same approved content."),
            title="Same title",
        ),
        dict(
            approved_doc("faq-002", "Same approved content."),
            title="Same title",
        ),
    ])

    result = ingestion.run()

    state = json.loads(ingestion.STATE.read_text(encoding="utf-8"))
    chunks = json.loads(ingestion.CHUNKS.read_text(encoding="utf-8"))

    assert result["duplicate_content_records"] == 1
    assert len(chunks) == 1
    assert state["documents"]["faq-002"]["duplicate_of"] == "faq-001"


def test_invalid_source_record_is_logged(isolated_ingestion):
    isolated_ingestion([
        approved_doc(),
        {"title": "Missing ID", "text": "Some content"},
    ])

    result = ingestion.run()
    failures = json.loads(
        ingestion.FAILURES.read_text(encoding="utf-8")
    )

    assert result["failures"] == 1
    assert failures[0]["category"] == "record_parse"


def test_embeddings_require_a_pinned_revision(isolated_ingestion):
    isolated_ingestion([approved_doc()])

    result = ingestion.run(
        build_embeddings_requested=True,
        model_revision=None,
    )

    assert result["embedding_status"] == "failed_missing_pinned_revision"
    assert result["failures"] == 1


def test_stale_embeddings_are_removed_when_revision_is_missing(
    isolated_ingestion,
):
    isolated_ingestion([approved_doc()])

    ingestion.EMBEDDINGS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    ingestion.EMBEDDINGS.write_bytes(b"stale-vector-data")

    result = ingestion.run(
        build_embeddings_requested=True,
        model_revision=None,
    )

    assert result["embedding_status"] == "failed_missing_pinned_revision"
    assert not ingestion.EMBEDDINGS.exists()


def test_invalid_source_url_is_rejected_without_network_access():
    errors = ingestion.check_approved_pages({
        "http://hisabdo.app/faq",
        "https://unapproved.example/faq",
    })

    assert len(errors) == 2
    assert all(item["category"] == "page_rejected" for item in errors)
