
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken


# Tokenizer configuration
ENCODING_NAME = "cl100k_base"
encoding = tiktoken.get_encoding(ENCODING_NAME)


# Initial chunk configurations for HisabDo
CHUNK_CONFIGS = {
    "faq": {
        "chunk_size": 300,
        "chunk_overlap": 30,
        "separators": ["\n\n", "\n", "? ", ". ", " ", ""],
    },

    "accounting_table": {
        "chunk_size": 400,
        "chunk_overlap": 40,
        "separators": ["\n", " | ", " ", ""],
    },

    "workflow": {
        "chunk_size": 500,
        "chunk_overlap": 75,
        "separators": ["\n\n", "\n", ". ", "; ", " ", ""],
    },

    "long_form": {
        "chunk_size": 800,
        "chunk_overlap": 120,
        "separators": ["\n\n", "\n", ". ", " ", ""],
    },
}


# Default configuration (long-form documentation)
CHUNK_SIZE = CHUNK_CONFIGS["long_form"]["chunk_size"]
CHUNK_OVERLAP = CHUNK_CONFIGS["long_form"]["chunk_overlap"]
MIN_CHUNK_SIZE = 1


def chunk_text(
    text,
    document_id="doc_1",
    page_number=None,
    content_type="long_form",
):
    """
    Split text into token-based chunks.

    Supported content types:
    faq
    accounting_table
    workflow
    long_form
    """

    if not text or not text.strip():
        return []

    if content_type not in CHUNK_CONFIGS:
        raise ValueError(
            f"Unsupported content type: {content_type}"
        )

    config = CHUNK_CONFIGS[content_type]

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=ENCODING_NAME,
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=config["separators"],
    )

    text_chunks = splitter.split_text(text.strip())

    results = []

    for index, chunk in enumerate(text_chunks):
        if not chunk.strip():
            continue

        results.append({
            "document_id": document_id,
            "chunk_index": len(results),
            "page_number": page_number,
            "content_type": content_type,
            "token_count": len(encoding.encode(chunk)),
            "text": chunk,
        })

    return results
