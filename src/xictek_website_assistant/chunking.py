"""
Splits long page text into overlapping chunks sized for embedding.

Paragraph-aware: splits on blank lines first and packs paragraphs into
~chunk_size_chars windows rather than cutting mid-sentence at a fixed
character offset, so retrieved context reads coherently. Falls back to a
hard character split only for a single paragraph longer than the chunk
size (e.g. an unformatted blog post pasted as one block). Job-role
sections are chunked separately, with their role title repeated when a
long requirements section needs multiple chunks.
"""
from __future__ import annotations

import re


_ROLE_TITLE_RE = re.compile(
    r"\b(developer|engineer|architect|designer|intern|analyst|manager|specialist|"
    r"consultant|officer|administrator|technician|coordinator|director|lead)\b",
    re.IGNORECASE,
)


def _split_paragraphs(text: str) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in paragraphs if p]


def _hard_split(paragraph: str, chunk_size: int, overlap: int) -> list[str]:
    if len(paragraph) <= chunk_size:
        return [paragraph]
    step = max(chunk_size - overlap, 1)
    return [paragraph[i : i + chunk_size] for i in range(0, len(paragraph), step)]


def _is_role_title(paragraph: str) -> bool:
    return (
        len(paragraph) <= 120
        and not paragraph.endswith((".", "?", "!", ":"))
        and _ROLE_TITLE_RE.search(paragraph) is not None
    )


def _chunk_paragraphs(
    paragraphs: list[str], chunk_size: int, overlap: int
) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        if len(paragraph) > chunk_size:
            if current:
                chunks.append("\n\n".join(current))
                current, current_len = [], 0
            chunks.extend(_hard_split(paragraph, chunk_size, overlap))
            continue

        added_len = len(paragraph) + (2 if current else 0)
        if current and current_len + added_len > chunk_size:
            chunks.append("\n\n".join(current))
            overlap_paras: list[str] = []
            overlap_len = 0
            for p in reversed(current):
                if overlap_len + len(p) > overlap:
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


def _chunk_role_section(
    title: str, paragraphs: list[str], chunk_size: int, overlap: int
) -> list[str]:
    section = "\n\n".join([title, *paragraphs])
    if len(section) <= chunk_size:
        return [section]

    body = "\n\n".join(paragraphs)
    title_prefix = f"{title}\n\n"
    body_chunk_size = max(chunk_size - len(title_prefix), 1)
    body_overlap = min(overlap, max(body_chunk_size - 1, 0))
    return [
        f"{title_prefix}{part}" if part else title
        for part in _hard_split(body, body_chunk_size, body_overlap)
    ]


def chunk_text(text: str, chunk_size_chars: int = 1200, chunk_overlap_chars: int = 200) -> list[str]:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    chunks: list[str] = []
    regular_paragraphs: list[str] = []
    index = 0
    while index < len(paragraphs):
        paragraph = paragraphs[index]
        if not _is_role_title(paragraph):
            regular_paragraphs.append(paragraph)
            index += 1
            continue

        if regular_paragraphs:
            chunks.extend(
                _chunk_paragraphs(
                    regular_paragraphs, chunk_size_chars, chunk_overlap_chars
                )
            )
            regular_paragraphs = []

        section_paragraphs: list[str] = []
        index += 1
        while index < len(paragraphs) and not _is_role_title(paragraphs[index]):
            section_paragraphs.append(paragraphs[index])
            index += 1
        chunks.extend(
            _chunk_role_section(
                paragraph,
                section_paragraphs,
                chunk_size_chars,
                chunk_overlap_chars,
            )
        )

    if regular_paragraphs:
        chunks.extend(
            _chunk_paragraphs(
                regular_paragraphs, chunk_size_chars, chunk_overlap_chars
            )
        )

    return chunks
