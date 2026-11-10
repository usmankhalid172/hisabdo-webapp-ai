"""Unit tests for the paragraph-aware chunker."""
from src.xictek_website_assistant.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n   ") == []


def test_short_text_returns_single_chunk():
    text = "XICTEK Systems builds AI-powered software products."
    chunks = chunk_text(text, chunk_size_chars=1200, chunk_overlap_chars=200)
    assert chunks == [text]


def test_packs_multiple_paragraphs_into_one_chunk_when_they_fit():
    paragraphs = ["Paragraph one.", "Paragraph two.", "Paragraph three."]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, chunk_size_chars=1200, chunk_overlap_chars=200)
    assert len(chunks) == 1
    for p in paragraphs:
        assert p in chunks[0]


def test_splits_into_multiple_chunks_when_exceeding_chunk_size():
    paragraphs = [f"Paragraph {i}: " + ("word " * 30) for i in range(10)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, chunk_size_chars=300, chunk_overlap_chars=50)
    assert len(chunks) > 1
    for chunk in chunks:
        # allow slack: one oversized paragraph can't be shrunk below itself
        assert len(chunk) <= 300 or chunk.strip() in paragraphs[0]


def test_hard_splits_a_single_paragraph_longer_than_chunk_size():
    long_paragraph = "word " * 500  # no blank-line breaks at all
    chunks = chunk_text(long_paragraph, chunk_size_chars=300, chunk_overlap_chars=50)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)


def test_reconstructs_all_content_across_chunks():
    paragraphs = ["Alpha section.", "Beta section.", "Gamma section."]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, chunk_size_chars=25, chunk_overlap_chars=5)
    joined = " ".join(chunks)
    for p in paragraphs:
        assert p in joined


def test_keeps_a_service_table_together_when_it_fits():
    rows = [
        "Service | Description",
        "Web development | Custom websites and web applications.",
        "Mobile apps | iOS and Android application delivery.",
        "AI solutions | Automation and machine learning services.",
    ]
    text = "\n".join(rows)

    chunks = chunk_text(text, chunk_size_chars=300, chunk_overlap_chars=50)

    assert chunks == [text]


def test_about_and_service_context_fits_production_defaults():
    text = (
        "About Us\n\n"
        "XICTEK builds digital products for businesses and provides ongoing support.\n\n"
        "Core Services\n\n"
        "Service | Description\n"
        "Web development | Custom websites and web applications.\n"
        "Mobile apps | iOS and Android application delivery.\n"
        "AI solutions | Automation and machine learning services."
    )

    assert chunk_text(text) == [text]


def test_splits_oversized_service_tables_only_between_rows_and_repeats_header():
    rows = ["Service | Description"] + [
        f"Service {index} | " + ("Distinctive service details " * 3)
        for index in range(8)
    ]
    chunks = chunk_text("\n".join(rows), chunk_size_chars=150, chunk_overlap_chars=60)

    assert len(chunks) > 1
    assert all(len(chunk) <= 150 for chunk in chunks)
    assert all(chunk.splitlines()[0] == rows[0] for chunk in chunks)
    for row in rows[1:]:
        assert sum(row.strip() in chunk.splitlines() for chunk in chunks) >= 1


def test_keeps_policy_bullets_atomic_when_oversized():
    items = [f"- Policy item {index}: " + ("Keep this complete statement. " * 2) for index in range(8)]
    chunks = chunk_text("\n".join(items), chunk_size_chars=130, chunk_overlap_chars=50)

    assert len(chunks) > 1
    assert all(len(chunk) <= 130 for chunk in chunks)
    assert all(line.startswith("- Policy item ") for chunk in chunks for line in chunk.splitlines())
    for item in items:
        assert sum(item.strip() in chunk.splitlines() for chunk in chunks) >= 1


def test_structured_overlap_repeats_complete_policy_items():
    items = [f"- Policy item {index}: Keep the complete rule." for index in range(6)]
    chunks = chunk_text("\n".join(items), chunk_size_chars=85, chunk_overlap_chars=50)

    assert len(chunks) > 1
    for previous, following in zip(chunks, chunks[1:]):
        assert set(previous.splitlines()) & set(following.splitlines())
    for item in items:
        assert sum(item in chunk.splitlines() for chunk in chunks) >= 1
