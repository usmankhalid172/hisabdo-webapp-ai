
import os
import logging
from typing import Sequence

from dotenv import load_dotenv
from openai import (
    OpenAI,
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
    RetryError,
)

load_dotenv()

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL", "text-embedding-3-small"
)
VECTOR_DIMENSION = int(
    os.getenv("EMBEDDING_DIMENSIONS", "1536")
)
BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
TIMEOUT = float(os.getenv("EMBEDDING_TIMEOUT", "20"))
MAX_RETRIES = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))
MAX_CHARS = int(os.getenv("EMBEDDING_MAX_CHARS", "8000"))

if VECTOR_DIMENSION < 1:
    raise ValueError("EMBEDDING_DIMENSIONS must be positive.")
if BATCH_SIZE < 1:
    raise ValueError("EMBEDDING_BATCH_SIZE must be positive.")
if MAX_RETRIES < 0 or MAX_CHARS < 1 or TIMEOUT <= 0:
    raise ValueError("Invalid embedding configuration.")

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not configured.")

client = OpenAI(
    api_key=API_KEY,
    timeout=TIMEOUT,
    max_retries=0,
)


class EmbeddingProviderError(RuntimeError):
    """Raised when the embedding provider fails."""


RETRYABLE_ERRORS = (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)


@retry(
    retry=retry_if_exception_type(RETRYABLE_ERRORS),
    wait=wait_random_exponential(min=1, max=8),
    stop=stop_after_attempt(MAX_RETRIES + 1),
    reraise=True,
)
def _request_embeddings(texts: list[str]) -> list[list[float]]:
    """Send a batch and preserve the original input order."""
    response = client.embeddings.create(
        model=MODEL_NAME,
        input=texts,
        dimensions=VECTOR_DIMENSION,
        encoding_format="float",
    )

    if len(response.data) != len(texts):
        raise EmbeddingProviderError(
            "Embedding provider returned an unexpected vector count."
        )

    ordered = sorted(response.data, key=lambda item: item.index)

    vectors = [item.embedding for item in ordered]

    if any(len(vector) != VECTOR_DIMENSION for vector in vectors):
        raise EmbeddingProviderError(
            "Embedding provider returned an unexpected vector dimension."
        )

    return vectors


def generate_embeddings(chunks: Sequence[str]) -> list[list[float]]:
    """
    Generate one vector per text chunk using batched API requests.

    Empty input returns an empty list.
    Invalid chunks raise ValueError.
    Provider failures raise EmbeddingProviderError.
    """
    if isinstance(chunks, (str, bytes)):
        raise ValueError("Provide a list of text chunks, not a single string.")

    texts = list(chunks)

    if not texts:
        return []

    for index, text in enumerate(texts):
        if not isinstance(text, str) or not text.strip():
            raise ValueError(
                f"Chunk {index} is empty or is not a string."
            )

        if len(text) > MAX_CHARS:
            raise ValueError(
                f"Chunk {index} exceeds the {MAX_CHARS}-character limit. "
                "Split it into smaller chunks first."
            )

    all_vectors = []

    for start in range(0, len(texts), BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]

        try:
            vectors = _request_embeddings(batch)
        except RETRYABLE_ERRORS as exc:
            logger.exception("Embedding provider failed after retries.")
            raise EmbeddingProviderError(
                "OpenAI embeddings failed after retries. "
                "Check your network, API limits, and provider status."
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected embedding provider failure.")
            raise EmbeddingProviderError(
                "Unable to generate embeddings. Check the API "
                "configuration and provider response."
            ) from exc

        all_vectors.extend(vectors)

    if len(all_vectors) != len(texts):
        raise EmbeddingProviderError(
            "Embedding count does not match the input chunk count."
        )

    return all_vectors
