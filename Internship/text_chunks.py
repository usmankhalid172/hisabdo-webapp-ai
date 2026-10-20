import re

# Configuration
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 50


def chunk_text(text, document_id="doc_1", page_number=None):
    if not text or not text.strip():
        return []

    # Split at sentence and paragraph boundaries
    sentences = re.split(
        r'(?<=[.!?])\s+|\n+',
        text.strip()
    )

    # Split exceptionally long sentences at word boundaries
    units = []
    for sentence in sentences:
        words = sentence.split()
        current = ""

        for word in words:
            candidate = f"{current} {word}".strip()

            if len(candidate) > CHUNK_SIZE:
                if current:
                    units.append(current)
                current = word
            else:
                current = candidate

        if current:
            units.append(current)

    chunks = []
    current = ""

    for unit in units:
        candidate = f"{current} {unit}".strip()

        if len(candidate) <= CHUNK_SIZE:
            current = candidate
            continue

        if len(current) >= MIN_CHUNK_SIZE:
            chunks.append(current)

        # Start the next chunk with a word-boundary overlap
        words = current.split()
        overlap_words = []
        overlap_length = 0

        for word in reversed(words):
            extra = len(word) + (1 if overlap_words else 0)

            if overlap_length + extra > CHUNK_OVERLAP:
                break

            overlap_words.insert(0, word)
            overlap_length += extra

        current = " ".join(overlap_words)
        current = f"{current} {unit}".strip()

        # Safety fallback if overlap plus unit exceeds the limit
        if len(current) > CHUNK_SIZE:
            current = unit

    if current and len(current) >= MIN_CHUNK_SIZE:
        chunks.append(current)

    return [
        {
            "document_id": document_id,
            "chunk_index": index,
            "page_number": page_number,
            "text": chunk,
        }
        for index, chunk in enumerate(chunks)
    ]