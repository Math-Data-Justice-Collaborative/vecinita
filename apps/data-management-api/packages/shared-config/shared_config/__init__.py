from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from . import env_deprecation


class BaseServiceSettings(BaseSettings):
    """Base settings shared by all Vecinita backend services.

    List fields (e.g. cors_origins) must be provided as JSON arrays when
    set via environment variables:  ALLOWED_ORIGINS='["http://localhost:3000"]'
    """

    open_api_key: str = Field(
        "",
        validation_alias=AliasChoices("OPEN_API_KEY", "OPENAI_API_KEY"),
        description="Optional OpenAI-compatible API key (legacy OPENAI_API_KEY accepted).",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    host: str = "0.0.0.0"
    port: int = 8000

    # URLs of downstream services (used by services that call others).
    # Contract names (003-consolidate-scraper-dm) are accepted alongside legacy VECINITA_* env vars.
    scraper_service_url: str = Field(
        "http://localhost:8001",
        validation_alias=AliasChoices(
            "SCRAPER_SERVICE_BASE_URL",
            "VECINITA_SCRAPER_API_URL",
        ),
    )
    model_service_url: str = Field(
        "http://localhost:8002",
        validation_alias=AliasChoices(
            "MODEL_SERVICE_BASE_URL",
            "VECINITA_MODEL_API_URL",
        ),
    )
    embedding_service_url: str = Field(
        "http://localhost:8003",
        validation_alias=AliasChoices(
            "EMBEDDING_SERVICE_BASE_URL",
            "VECINITA_EMBEDDING_API_URL",
        ),
    )

    # Modal function invocation (align with backend/src/services/modal/invoker.py).
    modal_function_invocation: str = Field(
        "",
        validation_alias=AliasChoices("MODAL_FUNCTION_INVOCATION"),
        description="auto|1|0|http — prefer Modal SDK for configured upstreams when enabled.",
    )
    modal_token_id: str = Field(
        "",
        validation_alias=AliasChoices("MODAL_TOKEN_ID", "MODAL_AUTH_KEY"),
    )
    modal_token_secret: str = Field(
        "",
        validation_alias=AliasChoices("MODAL_TOKEN_SECRET", "MODAL_AUTH_SECRET"),
    )
    modal_environment_name: str = Field(
        "",
        validation_alias=AliasChoices("MODAL_ENVIRONMENT_NAME", "MODAL_ENV"),
    )
    modal_scraper_app_name: str = Field(
        "vecinita-scraper",
        validation_alias=AliasChoices("MODAL_SCRAPER_APP_NAME"),
    )
    modal_scraper_health_function: str = Field(
        "health_check",
        validation_alias=AliasChoices("MODAL_SCRAPER_HEALTH_FUNCTION"),
    )
    modal_embedding_app_name: str = Field(
        "vecinita-embedding",
        validation_alias=AliasChoices("MODAL_EMBEDDING_APP_NAME"),
    )
    modal_embedding_single_function: str = Field(
        "embed_query",
        validation_alias=AliasChoices("MODAL_EMBEDDING_SINGLE_FUNCTION"),
    )
    modal_embedding_batch_function: str = Field(
        "embed_batch",
        validation_alias=AliasChoices("MODAL_EMBEDDING_BATCH_FUNCTION"),
    )
    modal_model_app_name: str = Field(
        "vecinita-model",
        validation_alias=AliasChoices("MODAL_MODEL_APP_NAME"),
    )
    modal_model_predict_function: str = Field(
        "predict",
        validation_alias=AliasChoices("MODAL_MODEL_PREDICT_FUNCTION"),
    )
    modal_model_chat_function: str = Field(
        "chat_completion",
        validation_alias=AliasChoices("MODAL_MODEL_CHAT_FUNCTION"),
    )

    # CORS — set as a JSON array string: ALLOWED_ORIGINS='["https://example.com"]'
    # Defaults include the standard data-management-frontend dev port (5174)
    # and the chat-frontend dev ports.  In production override this via env var
    # to the Render frontend hostname(s) only.
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5174",
            "http://localhost:5173",
            "http://localhost:3000",
        ],
        alias="ALLOWED_ORIGINS",
    )


@lru_cache
def get_settings() -> BaseServiceSettings:
    env_deprecation.warn_legacy_aliases()
    return BaseServiceSettings()
