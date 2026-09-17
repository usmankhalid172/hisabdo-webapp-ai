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
