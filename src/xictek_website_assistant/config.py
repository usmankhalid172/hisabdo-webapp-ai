"""
Settings for the XICTEK website assistant.

Kept as its own Settings class (not fields bolted onto the shared
`src.config.Settings`) so this module's env surface — embedding model,
index paths, crawl targets, CORS origins, rate limits — stays visibly
scoped to it and doesn't grow the shared config every time this module
needs a new knob. It still reads the same `.env` file, so no extra
wiring is needed to run both modules side by side.

Shared cross-cutting secrets (GROQ_API_KEY, INTERNAL_SERVICE_TOKEN) default
to `src.config.Settings` as the source of truth — this module reads them
from there via get_settings() in llm_client.py / router.py. GROQ_API_KEY
and LLM_PROVIDER can optionally be overridden per-module via
XICTEK_GROQ_API_KEY / XICTEK_LLM_PROVIDER below, for teams that want this
module's chat generation on a separate Groq key from HisabDo's chatbot.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

MODULE_ROOT = Path(__file__).resolve().parent
DEFAULT_INDEX_DIR = MODULE_ROOT / "data" / "index"


class XictekSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="XICTEK_")

    # Optional per-module overrides. Unset (None) by default, in which
    # case llm_client.py falls back to the shared src.config.Settings
    # values — so nothing breaks for anyone who hasn't set these. Set
    # XICTEK_GROQ_API_KEY / XICTEK_LLM_PROVIDER in .env to give this
    # module its own Groq key/provider, separate from HisabDo's chatbot
    # (e.g. so the public website bot can be rate-limited or revoked
    # independently of the product chatbot).
    groq_api_key: str | None = None
    llm_provider: str | None = None

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384
    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 200
    top_k: int = 4
    relevance_threshold: float = 0.35

    # Where the built index (embeddings.npy + chunks.json) lives. The
    # ingest script writes here; the retriever reads from here at startup.
    index_dir: Path = DEFAULT_INDEX_DIR

    # Crawl targets for ingest.py — restricted allow-list of domains the
    # crawler is permitted to fetch from, per the "no shortcuts" scope
    # (company's own site + HisabDo's own public pages, nothing else).
    allowed_crawl_domains: list[str] = ["xicteksystems.com", "www.xicteksystems.com", "hisabdo.app", "www.hisabdo.app"]
    crawl_seed_urls: list[str] = ["https://xicteksystems.com/", "https://hisabdo.app/"]
    crawl_max_pages: int = 300
    crawl_request_delay_seconds: float = 0.5

    # CORS — the real website widget will call this API cross-origin once
    # it's dropped into xicteksystems.com. Empty by default (locked down);
    # set via XICTEK_WIDGET_ALLOWED_ORIGINS once the real domain is
    # confirmed with the team lead. Swagger/demo testing doesn't need
    # this — same-origin requests aren't subject to CORS.
    widget_allowed_origins: list[str] = []

    # Rate limiting (per client IP) — protects the LLM/embedding calls
    # behind this endpoint from abuse even though it's only reachable via
    # Swagger today; the team lead asked for this to be production-real
    # now rather than deferred.
    rate_limit: str = "20/minute"

    # Abuse guard: hard cap on message length so a single request can't be
    # used to blow up embedding/LLM cost or context size.
    max_message_chars: int = 2000


@lru_cache
def get_xictek_settings() -> XictekSettings:
    return XictekSettings()
