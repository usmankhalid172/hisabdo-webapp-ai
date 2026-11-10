from unittest.mock import patch

import numpy as np

from src.xictek_website_assistant.chunking import chunk_text
from src.xictek_website_assistant.config import XictekSettings
from src.xictek_website_assistant.ingest import CrawledPage, build_index


def _synthetic_project(index: int) -> str:
    return "\n\n".join(
        [
            f"Project {index}: Synthetic case study structure only",
            (
                "Summary: This synthetic project summary describes the business "
                "problem, implementation scope, and delivery approach. "
            )
            * 3,
            "Technology stack: Python, FastAPI, PostgreSQL, Docker, and cloud deployment.",
            (
                "Project metrics: Baseline 100 units; after implementation 75 units; "
                "improvement 25 percent. Synthetic values, not client facts."
            ),
        ]
    )


def test_portfolio_size_keeps_synthetic_project_facts_coherent():
    settings = XictekSettings(_env_file=None)
    projects = [_synthetic_project(index) for index in range(1, 5)]
    text = "\n\n".join(projects)

    chunks = chunk_text(
        text,
        settings.portfolio_chunk_size_chars,
        settings.portfolio_chunk_overlap_chars,
    )

    assert settings.portfolio_chunk_size_chars == 900
    assert settings.portfolio_chunk_overlap_chars == 180
    assert all(len(chunk) <= settings.portfolio_chunk_size_chars for chunk in chunks)
    for index in range(1, 5):
        project_chunks = [chunk for chunk in chunks if f"Project {index}:" in chunk]
        assert any(
            "Technology stack:" in chunk and "Project metrics:" in chunk
            for chunk in project_chunks
        )


def test_build_index_uses_portfolio_parameters_only_for_portfolio_urls():
    settings = XictekSettings(_env_file=None)
    calls = []

    def record_chunking(text, size, overlap):
        calls.append((size, overlap))
        return chunk_text(text, size, overlap)

    def embed(texts):
        return np.zeros((len(texts), 4), dtype="float32")

    pages = [
        CrawledPage(
            "https://xicteksystems.com/portfolio",
            "Portfolio",
            "Public portfolio summary.",
        ),
        CrawledPage(
            "https://xicteksystems.com/blog/project",
            "Project article",
            "General site summary.",
        ),
    ]
    with (
        patch("src.xictek_website_assistant.ingest.get_xictek_settings", return_value=settings),
        patch("src.xictek_website_assistant.ingest.chunk_text", side_effect=record_chunking),
        patch("src.xictek_website_assistant.ingest.embed_texts", side_effect=embed),
    ):
        build_index(pages)

    assert calls == [
        (settings.portfolio_chunk_size_chars, settings.portfolio_chunk_overlap_chars),
        (settings.chunk_size_chars, settings.chunk_overlap_chars),
    ]


def test_portfolio_path_matching_handles_nested_paths_and_trailing_slash():
    settings = XictekSettings(_env_file=None)
    from src.xictek_website_assistant.ingest import _chunking_parameters

    portfolio_parameters = (
        settings.portfolio_chunk_size_chars,
        settings.portfolio_chunk_overlap_chars,
    )

    assert _chunking_parameters("https://example.test/portfolio/", settings) == portfolio_parameters
    assert _chunking_parameters("https://example.test/portfolio/case-study", settings) == portfolio_parameters
    assert _chunking_parameters("https://example.test/portfolioish", settings) == (
        settings.chunk_size_chars,
        settings.chunk_overlap_chars,
    )
