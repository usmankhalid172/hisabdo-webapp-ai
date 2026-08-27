"""RAG knowledge base for the AI Financial Assistant.

Loads the saving-tips markdown corpus from ``data/saving_tips.md`` and
splits it into retrievable chunks. Each ``## Heading`` section becomes one
chunk with ``title`` and ``tags`` metadata so the retriever can apply
simple metadata filtering, following the team's recommendation to use simple
document chunking + metadata with the option of reranking if needed.

The corpus is treated as general, safe, non-personalised financial education
content (no sensitive data). It is the source of grounding for SAVING_TIP
responses, which helps reduce hallucinated advice.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

DataDirectory = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_SOURCE = DataDirectory / "saving_tips.md"

# Metadata for each known section title -> list of retrieval tag keywords.
_SECTION_TAGS = {
    "Budgeting to save money": ["budget", "plan", "limit", "saving"],
    "Track weekly spending to save": ["track", "weekly", "review", "save"],
    "Reduce dining-out costs to save": ["dining", "restaurant", "cook", "save"],
    "Cut grocery spending to save": ["grocery", "groceries", "shopping", "save"],
    "Reduce transport and fuel to save": ["transport", "fuel", "car", "save"],
}


@dataclass
class Chunk:
    """A single retrievable knowledge-base chunk."""
    index: int
    title: str
    text: str
    tags: List[str] = None


def load_knowledge_base(path=None) -> List[Chunk]:
    """Load the markdown corpus and split it into chunks by ``## `` section."""
    path = path or DEFAULT_SOURCE
    raw = Path(path).read_text(encoding="utf-8")
    chunks: List[Chunk] = []
    current_title = None
    current_lines: List[str] = []

    def flush(index, title, lines):
        if title is not None and lines:
            chunks.append(Chunk(index=index, title=title,
                              text=" ".join(l.strip() for l in lines).strip(),
                              tags=_SECTION_TAGS.get(title, [])))

    for line in raw.splitlines():
        if line.startswith("## "):
            flush(len(chunks), current_title, current_lines)
            current_title = line[3:].strip()
            current_lines = []
        elif line.strip() and not line.startswith("#"):
            current_lines.append(line)

    flush(len(chunks), current_title, current_lines)
    return chunks


def lookup_chunk(chunks: List[Chunk], title: str) -> Optional[Chunk]:
    """Return a chunk by exact or partial title match."""
    for c in chunks:
        if c.title.lower() == title.lower() or title.lower() in c.title.lower():
            return c
    return None