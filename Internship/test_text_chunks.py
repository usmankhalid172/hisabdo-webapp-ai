from text_chunks import (
    chunk_text,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    MIN_CHUNK_SIZE,
)

text = (
    "HisabDo manages business expenses. "
    "It tracks sales and customer payments. "
    "Business owners organize tasks and notes. "
) * 100

chunks = chunk_text(
    text,
    document_id="hisabdo_test",
    page_number=1,
)

assert chunks, "No chunks generated"

for index, chunk in enumerate(chunks):
    content = chunk["text"]

    assert len(content) <= CHUNK_SIZE, "Chunk too large"
    assert len(content) >= MIN_CHUNK_SIZE, "Chunk too small"
    assert chunk["document_id"] == "hisabdo_test"
    assert chunk["chunk_index"] == index
    assert chunk["page_number"] == 1

# Check the actual shared text between consecutive chunks
for index in range(len(chunks) - 1):
    first = chunks[index]["text"]
    second = chunks[index + 1]["text"]

    shared = 0
    max_length = min(len(first), len(second), CHUNK_OVERLAP)

    for size in range(1, max_length + 1):
        if first.endswith(second[:size]):
            shared = size

    print(f"Chunks {index} -> {index + 1}: overlap = {shared} characters")

print("\nChunk size and metadata checks passed!")
print("Total chunks:", len(chunks))