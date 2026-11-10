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


def test_keeps_markdown_table_rows_together_when_table_fits():
    table = "| Feature | Detail |\n| --- | --- |\n| Ledger | Records payments |\n| Reports | Exports PDF |"
    chunks = chunk_text(table, chunk_size_chars=200, chunk_overlap_chars=20)
    assert len(chunks) == 1
    assert chunks[0] == table


def test_splits_large_markdown_table_only_between_rows_and_repeats_header():
    table = "\n".join(
        ["| Feature | Specification |", "| --- | --- |"]
        + [f"| Feature {i} | {('detail ' + str(i) + ' ') * 5}|" for i in range(8)]
    )
    chunks = chunk_text(table, chunk_size_chars=130, chunk_overlap_chars=20)
    assert len(chunks) > 1
    expected_header = ["| Feature | Specification |", "| --- | --- |"]
    for chunk in chunks:
        lines = chunk.splitlines()
        assert lines[:2] == expected_header
        assert len(lines) >= 3
        assert all(line.startswith("|") and line.endswith("|") for line in lines)
    for i in range(8):
        assert sum(f"| Feature {i} |" in chunk for chunk in chunks) == 1


def test_does_not_break_a_single_oversized_table_row():
    row = "| Voice entry | " + ("technical detail " * 20) + "|"
    table = "| Feature | Specification |\n| --- | --- |\n" + row
    chunks = chunk_text(table, chunk_size_chars=80, chunk_overlap_chars=10)
    assert len(chunks) == 1
    assert chunks[0].endswith(row)
