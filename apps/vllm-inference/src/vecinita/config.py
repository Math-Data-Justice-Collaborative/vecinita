"""Application configuration and supported model registry."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "vecinita-model"
    default_model: str = "gemma3"
    models_path: str = "/models"
    ollama_host: str = "http://localhost:11434"
    # Seconds to keep a container alive after last request
    scaledown_window: int = 300
    # Request timeout in seconds
    timeout: int = 600
    # Startup preload model; blank falls back to default_model.
    startup_model: str | None = None
    # Lifecycle retry behavior for startup preload.
    retry_limit: int = Field(default=3, ge=1)
    retry_backoff_ms: int = 1000
    # Active lifecycle registry identifier.
    lifecycle_registry_id: str = "default"


settings = Settings()


def resolve_startup_model_id() -> str:
    """Return configured startup model id, falling back to default model."""
    model_id = (settings.startup_model or "").strip() or settings.default_model
    if model_id not in SUPPORTED_MODELS:
        supported = ", ".join(sorted(SUPPORTED_MODELS))
        raise ValueError(
            f"Unsupported startup model '{model_id}'. Supported models: {supported}"
        )
    return model_id

# Registry of supported models.
# Each entry maps a friendly model ID to its backend and backend-specific name.
SUPPORTED_MODELS: dict[str, dict] = {
    "gemma3": {"backend": "ollama", "ollama_name": "gemma3"},
    "llama3.2": {"backend": "ollama", "ollama_name": "llama3.2"},
    "llama3.2:1b": {"backend": "ollama", "ollama_name": "llama3.2:1b"},
    "llama3.1": {"backend": "ollama", "ollama_name": "llama3.1"},
    "llama3.1:8b": {"backend": "ollama", "ollama_name": "llama3.1:8b"},
    "mistral": {"backend": "ollama", "ollama_name": "mistral"},
    "phi3": {"backend": "ollama", "ollama_name": "phi3"},
    "gemma2": {"backend": "ollama", "ollama_name": "gemma2"},
    "gemma2:2b": {"backend": "ollama", "ollama_name": "gemma2:2b"},
}
