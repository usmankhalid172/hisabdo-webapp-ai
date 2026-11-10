"""
Splits long page text into overlapping chunks sized for embedding.

Paragraph-aware: splits on blank lines first and packs paragraphs into
~chunk_size_chars windows rather than cutting mid-sentence at a fixed
character offset, so retrieved context reads coherently. Falls back to a
hard character split only for a single paragraph longer than the chunk
size (e.g. an unformatted blog post pasted as one block).
"""
from __future__ import annotations


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in paragraphs if p]


def _hard_split(paragraph: str, chunk_size: int, overlap: int) -> list[str]:
    if len(paragraph) <= chunk_size:
        return [paragraph]
    step = max(chunk_size - overlap, 1)
    return [paragraph[i : i + chunk_size] for i in range(0, len(paragraph), step)]


def _is_structured_block(lines: list[str]) -> bool:
    if len(lines) < 2:
        return False
    if all("|" in line for line in lines):
        return True
    return all(line.startswith(("-", "*")) for line in lines)


def _split_structured_block(
    lines: list[str], chunk_size: int, overlap: int
) -> list[str]:
    is_table = all("|" in line for line in lines)
    header = lines[0] if is_table else None
    items = lines[1:] if is_table else lines
    chunks: list[str] = []
    start = 0

    while start < len(items):
        prefix = [header] if header else []
        block = prefix.copy()
        end = start

        while end < len(items):
            candidate = block + [items[end]]
            if len("\n".join(candidate)) > chunk_size:
                break
            block = candidate
            end += 1

        if end == start:
            chunks.extend(_hard_split(items[start], chunk_size, overlap))
            start += 1
            continue

        chunks.append("\n".join(block))
        if end == len(items):
            break

        overlap_items: list[str] = []
        overlap_length = len(header) + 1 if header and end else 0
        for item in reversed(items[start:end]):
            added_length = len(item) + (1 if overlap_items or overlap_length else 0)
            if overlap_length + added_length > overlap:
                break
            overlap_items.insert(0, item)
            overlap_length += added_length

        start = max(start + 1, end - len(overlap_items))

    return chunks


def chunk_text(text: str, chunk_size_chars: int = 1200, chunk_overlap_chars: int = 200) -> list[str]:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size_chars:
            if current:
                chunks.append("\n\n".join(current))
                current, current_len = [], 0
            lines = [line.strip() for line in paragraph.splitlines() if line.strip()]
            if _is_structured_block(lines):
                chunks.extend(
                    _split_structured_block(
                        lines, chunk_size_chars, chunk_overlap_chars
                    )
                )
            else:
                chunks.extend(_hard_split(paragraph, chunk_size_chars, chunk_overlap_chars))
            continue

        added_len = len(paragraph) + (2 if current else 0)
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
            added_len = len(paragraph) + (2 if current else 0)

        current.append(paragraph)
        current_len += added_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks
