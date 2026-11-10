"""
Splits long page text into overlapping chunks sized for embedding.

Paragraph-aware: packs paragraphs into ~chunk_size_chars windows. Markdown
tables are treated as structured blocks and split only between data rows;
when a table needs multiple chunks, its header and separator are repeated.
Falls back to a hard character split only for a single long paragraph.
"""
from __future__ import annotations


def _split_paragraphs(text: str) -> list[str]:
    """Split Markdown into paragraph and table blocks without breaking tables."""
    lines = text.splitlines()
    blocks: list[str] = []
    normal: list[str] = []

    def flush_normal() -> None:
        if normal:
            blocks.append("\n".join(normal).strip())
            normal.clear()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            flush_normal()
            i += 1
            continue

        if i + 1 < len(lines) and _is_markdown_table_row(line) and _is_table_separator(lines[i + 1]):
            flush_normal()
            table_lines = [line, lines[i + 1].strip()]
            i += 2
            while i < len(lines) and lines[i].strip() and _is_markdown_table_row(lines[i].strip()):
                table_lines.append(lines[i].strip())
                i += 1
            blocks.append("\n".join(table_lines))
            continue

        normal.append(line)
        i += 1

    flush_normal()
    return blocks


def _is_markdown_table_row(line: str) -> bool:
    return line.count("|") >= 2


def _is_table_separator(line: str) -> bool:
    cells = line.strip().strip("|").split("|")
    return len(cells) >= 2 and all(
        cell.strip() and all(char in "-: " for char in cell.strip()) and "-" in cell
        for cell in cells
    )


def _hard_split(paragraph: str, chunk_size: int, overlap: int) -> list[str]:
    if len(paragraph) <= chunk_size:
        return [paragraph]
    step = max(chunk_size - overlap, 1)
    return [paragraph[i : i + chunk_size] for i in range(0, len(paragraph), step)]


def _split_table(table: str, chunk_size: int) -> list[str]:
    """Split an oversized table on row boundaries and repeat its header."""
    rows = table.splitlines()
    if len(rows) <= 2:
        # Never cut through a header or a single unusually long data row.
        return [table]

    header = rows[:2]
    body = rows[2:]
    result: list[str] = []
    current = header[:]

    for row in body:
        candidate = "\n".join([*current, row])
        if len(current) > 2 and len(candidate) > chunk_size:
            result.append("\n".join(current))
            current = header[:]
        current.append(row)

    if len(current) > 2 or not result:
        result.append("\n".join(current))
    return result


def chunk_text(text: str, chunk_size_chars: int = 1200, chunk_overlap_chars: int = 200) -> list[str]:
    blocks = _split_paragraphs(text)
    if not blocks:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for block in blocks:
        is_table = "\n" in block and any(_is_table_separator(line) for line in block.splitlines())
        if is_table and len(block) > chunk_size_chars:
            if current:
                chunks.append("\n\n".join(current))
                current, current_len = [], 0
            chunks.extend(_split_table(block, chunk_size_chars))
            continue

        if len(block) > chunk_size_chars:
            if current:
                chunks.append("\n\n".join(current))
                current, current_len = [], 0
            chunks.extend(_hard_split(block, chunk_size_chars, chunk_overlap_chars))
            continue

        added_len = len(block) + (2 if current else 0)
        if current and current_len + added_len > chunk_size_chars:
            chunks.append("\n\n".join(current))
            # Carry the last paragraph forward as overlap context, up to
            # the configured overlap budget.
            overlap_paras: list[str] = []
            overlap_len = 0
            for p in reversed(current):
                if overlap_len + len(p) > chunk_overlap_chars:
                    break
                overlap_paras.insert(0, p)
                overlap_len += len(p)
            current, current_len = overlap_paras, sum(len(p) for p in overlap_paras)
            added_len = len(block) + (2 if current else 0)

        current.append(block)
        current_len += added_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks
