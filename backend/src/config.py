"""
Central configuration for the Vecinita backend.

Single source of truth for embedding model, LLM provider chain,
and runtime feature flags. Import from here — never hardcode model
names or provider strings in other modules.
"""

import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Runtime Environment Detection
# ---------------------------------------------------------------------------


def _running_on_render() -> bool:
    """Detect if running on Render platform."""
    return bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"))


def _truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_internal_service_url(raw_url: str | None, *, fallback_url: str) -> str:
    """Resolve the effective URL for an internal upstream service (embedding, Ollama).

    On Render, explicit non-local URLs are preferred. If an endpoint env var is
    missing or points to a local/docker-only hostname, the provided fallback is
    used.

    Args:
        raw_url:      Raw URL from an environment variable (may be None or empty).
        fallback_url: URL to use on Render or when raw_url is absent.

    Returns:
        On Render: non-local URLs when present; otherwise fallback_url.
        Off Render: raw_url if non-empty; otherwise fallback_url.
    """
    candidate = (raw_url or "").strip()

    if _running_on_render():
        if candidate:
            try:
                host = (urlparse(candidate).hostname or "").lower()
            except Exception:
                host = ""

            # Ignore local/docker-style endpoints on Render and force safe fallback.
            if host not in {
                "",
                "localhost",
                "127.0.0.1",
                "0.0.0.0",
                "::1",
                "embedding-service",
                "vecinita-embedding",
                "vecinita-agent",
            }:
                return candidate
        return fallback_url

    return candidate if candidate else fallback_url


def rewrite_deprecated_modal_embedding_host(url: str) -> str | None:
    """Map legacy Modal embedding hostnames to the current ``web_app`` endpoint host.

    Some environments still use ``*-embedding-embeddingservicecontainer-api.modal.run`` while
    the active deployment is ``*-embedding-web-app.modal.run``.

    Replacing only the suffix ``-embeddingservicecontainer-api`` would incorrectly produce
    ``...-embedding-embedding-web-app...``; we replace the full segment
    ``embedding-embeddingservicecontainer-api.modal.run`` → ``embedding-web-app.modal.run``.

    A second pass fixes hosts that already contain the mistaken doubled ``embedding`` segment
    (from older rewrite logic or manual env typos).
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return None

    host = (parsed.hostname or "").strip().lower()
    if not host.endswith(".modal.run"):
        return None

    new_host = host
    if "embedding-embeddingservicecontainer-api.modal.run" in new_host:
        new_host = new_host.replace(
            "embedding-embeddingservicecontainer-api.modal.run",
            "embedding-web-app.modal.run",
        )
    elif "-embedding-embedding-web-app.modal.run" in new_host:
        new_host = new_host.replace(
            "-embedding-embedding-web-app.modal.run",
            "-embedding-web-app.modal.run",
        )
    else:
        return None

    if new_host == host:
        return None

    port_part = f":{parsed.port}" if parsed.port else ""
    netloc = f"{new_host}{port_part}"
    return urlunparse((parsed.scheme or "https", netloc, "", "", "", "")).rstrip("/")


def normalize_agent_service_url(raw: str | None, *, default: str = "http://localhost:8000") -> str:
    """Ensure ``AGENT_SERVICE_URL`` has an HTTP scheme.

    Render ``fromService`` bindings often supply ``host:port`` only; httpx requires
    ``http://`` or ``https://``. Private service mesh on Render uses HTTP to the
    internal hostname.
    """
    candidate = (raw or "").strip()
    if not candidate:
        return default
    if "://" in candidate:
        return candidate
    return f"http://{candidate}"


# ---------------------------------------------------------------------------
# Embedding (must be consistent across indexing AND query-time)
# ---------------------------------------------------------------------------
EMBEDDING_MODEL: str = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
_EMBEDDING_SERVICE_URL_RAW: str = _normalize_internal_service_url(
    os.getenv("VECINITA_EMBEDDING_API_URL")
    or os.getenv("MODAL_EMBEDDING_ENDPOINT")
    or os.getenv("EMBEDDING_SERVICE_URL"),
    fallback_url=(
        "https://vecinita--vecinita-embedding-web-app.modal.run"
        if _running_on_render()
        else "http://localhost:8001"
    ),
)
# Normalize legacy / mistaken Modal hosts once at import (see rewrite_deprecated_modal_embedding_host).
EMBEDDING_SERVICE_URL: str = (
    rewrite_deprecated_modal_embedding_host(_EMBEDDING_SERVICE_URL_RAW)
    or _EMBEDDING_SERVICE_URL_RAW
).rstrip("/")

# ---------------------------------------------------------------------------
# Local LLM runtime
# ---------------------------------------------------------------------------
OLLAMA_BASE_URL: str | None = _normalize_internal_service_url(
    os.getenv("VECINITA_MODEL_API_URL")
    or os.getenv("MODAL_OLLAMA_ENDPOINT")
    or os.getenv("OLLAMA_BASE_URL"),
    fallback_url=(
        "https://vecinita--vecinita-model-api.modal.run"
        if _running_on_render()
        else "http://localhost:11434"
    ),
)
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3")

DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "ollama").lower()

# ---------------------------------------------------------------------------
# Data Database Routing (retrieval/storage path only)
# Render Postgres is the only supported data backend.
# ---------------------------------------------------------------------------
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
DB_DATA_MODE: str = "postgres"


def resolve_data_db_mode() -> str:
    """Resolve backend data-path database mode.

    The backend is postgres-only.
    """

    return "postgres"


def postgres_data_reads_enabled() -> bool:
    """Feature-flagged Postgres data-path reads."""

    return os.getenv("POSTGRES_DATA_READS_ENABLED", "true").lower() in {"1", "true", "yes"}


# ---------------------------------------------------------------------------
# Guardrails AI feature flags
# Disable individual guards via env without redeploying.
# ---------------------------------------------------------------------------
GUARDRAILS_ENABLED: bool = os.getenv("GUARDRAILS_ENABLED", "true").lower() in ("1", "true", "yes")
GUARDRAILS_PROMPT_INJECTION: bool = os.getenv("GUARDRAILS_PROMPT_INJECTION", "true").lower() in (
    "1",
    "true",
    "yes",
)
GUARDRAILS_TOPIC_RELEVANCE: bool = os.getenv("GUARDRAILS_TOPIC_RELEVANCE", "true").lower() in (
    "1",
    "true",
    "yes",
)
GUARDRAILS_PII: bool = os.getenv("GUARDRAILS_PII", "true").lower() in ("1", "true", "yes")
GUARDRAILS_TOXICITY: bool = os.getenv("GUARDRAILS_TOXICITY", "true").lower() in ("1", "true", "yes")
GUARDRAILS_HALLUCINATION: bool = os.getenv("GUARDRAILS_HALLUCINATION", "true").lower() in (
    "1",
    "true",
    "yes",
)

# Seed topic list for the topic-relevance guardrail.
# Override via GUARDRAILS_TOPICS env var (comma-separated).
_default_topics = (
    "water,watershed,environment,climate,habitat,restoration,"
    "community,health,rhode island,providence,woonasquatucket,"
    "pollution,air quality,recycling,sustainability,flood,stormwater,"
    "wildlife,green space,conservation,education,volunteer"
)
GUARDRAILS_TOPIC_LIST: list[str] = [
    t.strip() for t in os.getenv("GUARDRAILS_TOPICS", _default_topics).split(",") if t.strip()
]

# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
ADMIN_TOKEN: str | None = os.getenv("ADMIN_TOKEN")  # optional extra gate
MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).parent
DATA_DIR: Path = BASE_DIR.parent / "data"
