"""Configuration loading from environment variables."""

import os
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache

from vecinita_scraper.core.errors import ConfigError

_dotenv_load: Callable[..., bool] | None
try:
    from dotenv import load_dotenv as _dotenv_load
except ImportError:  # pragma: no cover - fallback for minimal test environments
    _dotenv_load = None


def _load_dotenv() -> bool:
    if _dotenv_load is None:
        return False
    dotenv_loader: Callable[..., bool] = _dotenv_load
    return dotenv_loader()


_load_dotenv()


def _env(name: str, default: str = "") -> str:
    """Return environment value as a guaranteed string."""
    return os.getenv(name) or default


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse boolean-like environment values."""
    value = _env(name, "true" if default else "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _env_csv(name: str) -> list[str]:
    """Parse comma-separated environment values."""
    return [item.strip() for item in _env(name).split(",") if item.strip()]


@dataclass
class PostgresConfig:
    """Render Postgres configuration."""

    database_url: str

    @staticmethod
    def from_env() -> "PostgresConfig":
        """Load Postgres config from environment.

        ``DATABASE_URL`` is canonical on **Render** (``fromDatabase`` / shared env groups;
        internal ``dpg-…-a`` hostnames are fine there — see Render Postgres docs).

        ``MODAL_DATABASE_URL`` is optional and, when set, **overrides** ``DATABASE_URL`` /
        ``DB_URL``. Modal scraper functions run outside Render's private network, so they
        must use a hostname reachable from the public internet (Render **external** database
        URL from the dashboard *Connect* menu, or PgBouncer with a public listener). If Modal
        secrets only copy the Render web service's internal ``DATABASE_URL``, connections
        fail with ``could not translate host name … to address``.
        """
        modal = _env("MODAL_DATABASE_URL").strip()
        if modal:
            return PostgresConfig(database_url=modal)
        primary = _env("DATABASE_URL").strip()
        fallback = _env("DB_URL").strip()
        return PostgresConfig(database_url=primary or fallback)

    def validate(self) -> None:
        """Validate Postgres configuration."""
        if not self.database_url:
            raise ConfigError(
                "Missing required Postgres configuration: MODAL_DATABASE_URL, DATABASE_URL, "
                "or DB_URL (see PostgresConfig.from_env docstring for Modal vs Render)"
            )


@dataclass
class ModalConfig:
    """Modal configuration."""

    token_id: str
    token_secret: str
    workspace: str

    @staticmethod
    def from_env() -> "ModalConfig":
        """Load Modal config from environment."""
        return ModalConfig(
            token_id=os.getenv("MODAL_TOKEN_ID", ""),
            token_secret=os.getenv("MODAL_TOKEN_SECRET", ""),
            workspace=os.getenv("MODAL_WORKSPACE", ""),
        )

    def validate(self) -> None:
        """Validate Modal config (optional in dev, required in prod)."""
        if os.getenv("ENVIRONMENT") == "production":
            if not all([self.token_id, self.token_secret]):
                raise ConfigError(
                    "Missing required Modal configuration in production: "
                    "MODAL_TOKEN_ID, MODAL_TOKEN_SECRET"
                )


@dataclass
class APIConfig:
    """External API configuration."""

    ollama_base_url: str
    embedding_upstream_url: str
    modal_function_invocation: bool
    modal_embedding_app_name: str
    modal_embedding_single_function: str
    modal_embedding_batch_function: str
    modal_environment_name: str

    @staticmethod
    def from_env() -> "APIConfig":
        """Load API config from environment."""
        return APIConfig(
            ollama_base_url=_env("OLLAMA_BASE_URL"),
            embedding_upstream_url=_env("EMBEDDING_UPSTREAM_URL"),
            modal_function_invocation=_env_bool("MODAL_FUNCTION_INVOCATION", default=False),
            modal_embedding_app_name=_env("MODAL_EMBEDDING_APP_NAME", "vecinita-embedding"),
            modal_embedding_single_function=_env(
                "MODAL_EMBEDDING_SINGLE_FUNCTION", "embed_query"
            ),
            modal_embedding_batch_function=_env(
                "MODAL_EMBEDDING_BATCH_FUNCTION", "embed_batch"
            ),
            modal_environment_name=_env("MODAL_ENVIRONMENT_NAME") or _env("MODAL_ENV", ""),
        )

    def validate(self) -> None:
        """Validate API config."""
        if self.modal_function_invocation:
            return
        if not all([self.embedding_upstream_url]):
            raise ConfigError("Missing required API configuration: EMBEDDING_UPSTREAM_URL")


@dataclass
class AuthConfig:
    """API key authentication configuration."""

    api_keys: tuple[str, ...]
    debug_bypass_auth: bool

    @staticmethod
    def from_env() -> "AuthConfig":
        """Load auth config from environment."""
        api_keys = _env_csv("SCRAPER_API_KEYS")
        legacy_admin_token = _env("DEV_ADMIN_BEARER_TOKEN").strip()
        if legacy_admin_token and legacy_admin_token not in api_keys:
            api_keys.append(legacy_admin_token)

        return AuthConfig(
            api_keys=tuple(api_keys),
            debug_bypass_auth=_env_bool("SCRAPER_DEBUG_BYPASS_AUTH", default=False),
        )

    def validate(self, environment: str) -> None:
        """Validate auth config with environment safety checks."""
        dev_only_envs = {"development", "dev", "local", "test"}

        if self.debug_bypass_auth and environment not in dev_only_envs:
            raise ConfigError(
                "SCRAPER_DEBUG_BYPASS_AUTH can only be enabled in local/dev environments"
            )

        if not self.debug_bypass_auth and not self.api_keys and environment != "test":
            raise ConfigError(
                "Missing required auth configuration: set SCRAPER_API_KEYS "
                "(or DEV_ADMIN_BEARER_TOKEN for compatibility)"
            )

        # Bearer header parsing uses a single whitespace split; DM frontend sends the same.
        # Keep rules aligned with backend/src/utils/scraper_api_keys.py.
        for idx, key in enumerate(self.api_keys):
            seg = idx + 1
            if not key.strip():
                raise ConfigError(f"SCRAPER_API_KEYS segment {seg} is empty.")
            if any(ch.isspace() for ch in key):
                raise ConfigError(
                    f"SCRAPER_API_KEYS segment {seg} contains whitespace; not compatible "
                    "with Authorization: Bearer or the data-management API key login."
                )
            if any(ord(ch) < 32 for ch in key):
                raise ConfigError(
                    f"SCRAPER_API_KEYS segment {seg} contains control characters; remove them."
                )


@dataclass
class CrawlConfig:
    """Crawl4AI configuration."""

    timeout_seconds: int
    max_depth: int

    @staticmethod
    def from_env() -> "CrawlConfig":
        """Load crawl config from environment."""
        return CrawlConfig(
            timeout_seconds=int(os.getenv("CRAWL4AI_TIMEOUT_SECONDS", "60")),
            max_depth=int(os.getenv("CRAWL4AI_MAX_DEPTH", "3")),
        )


@dataclass
class ChunkingConfig:
    """Chunking configuration."""

    min_size_tokens: int
    max_size_tokens: int
    overlap_ratio: float

    @staticmethod
    def from_env() -> "ChunkingConfig":
        """Load chunking config from environment."""
        return ChunkingConfig(
            min_size_tokens=int(os.getenv("CHUNK_MIN_SIZE_TOKENS", "256")),
            max_size_tokens=int(os.getenv("CHUNK_MAX_SIZE_TOKENS", "1024")),
            overlap_ratio=float(os.getenv("CHUNK_OVERLAP_RATIO", "0.2")),
        )


class Config:
    """Main configuration class."""

    def __init__(self) -> None:
        """Initialize configuration from environment."""
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        self.postgres = PostgresConfig.from_env()
        self.modal = ModalConfig.from_env()
        self.api = APIConfig.from_env()
        self.auth = AuthConfig.from_env()
        self.crawl = CrawlConfig.from_env()
        self.chunking = ChunkingConfig.from_env()

    def validate(self) -> None:
        """Validate all configuration."""
        self.postgres.validate()
        self.auth.validate(self.environment)
        if self.environment == "production":
            self.modal.validate()


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get cached configuration instance."""
    config = Config()
    config.validate()
    return config
