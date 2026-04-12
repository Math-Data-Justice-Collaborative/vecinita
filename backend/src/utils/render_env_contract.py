"""Validation helpers for the shared Render environment contract.

This module enforces a minimal safety contract for the shared
`.env.prod.render` environment group. The goal is to catch configuration
regressions before deploys by validating required keys and critical
cross-key consistency constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REQUIRED_KEYS: set[str] = {
    "ALLOWED_ORIGINS",
    "CORS_ORIGINS",
    "DATABASE_URL",
    "EMBEDDING_SERVICE_AUTH_TOKEN",
    "MODAL_TOKEN_ID",
    "MODAL_TOKEN_SECRET",
    "MODAL_WORKSPACE",
    "OLLAMA_MODEL",
    "RENDER_REMOTE_INFERENCE_ONLY",
    "SCRAPER_API_KEYS",
    "VECINITA_MODEL_API_URL",
    "VECINITA_EMBEDDING_API_URL",
    "VECINITA_SCRAPER_API_URL",
    "VITE_GATEWAY_URL",
    "VITE_BACKEND_URL",
    "VITE_VECINITA_SCRAPER_API_URL",
}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_env_file(path: str | Path) -> dict[str, str]:
    """Parse dotenv-style KEY=VALUE lines from a file path."""
    env: dict[str, str] = {}
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _validate_required_keys(env: dict[str, str], result: ValidationResult) -> None:
    for key in sorted(REQUIRED_KEYS):
        if not env.get(key, "").strip():
            result.errors.append(f"Missing required key: {key}")


def _validate_scraper_api_keys_not_placeholder(
    env: dict[str, str], result: ValidationResult
) -> None:
    """Reject template placeholder values that pass non-empty checks but break prod startup."""
    raw = (env.get("SCRAPER_API_KEYS") or "").strip().lower()
    if raw == "replace-with-comma-separated-api-keys":
        result.errors.append(
            "SCRAPER_API_KEYS is still the template placeholder; set one or more real "
            "comma-separated Bearer secrets in Render (shared env group) and in Modal "
            "secret vecinita-scraper-env if you serve the scraper API on Modal"
        )


def _validate_db_data_mode(env: dict[str, str], result: ValidationResult) -> None:
    mode = (env.get("DB_DATA_MODE") or "").strip().lower()
    if mode != "postgres":
        result.errors.append("DB_DATA_MODE must be set to postgres for Render runtime")


def _validate_database_url(env: dict[str, str], result: ValidationResult) -> None:
    database_url = (env.get("DATABASE_URL") or "").strip()
    if not database_url:
        return

    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        result.errors.append("DATABASE_URL must use postgres:// or postgresql:// scheme")
        return

    if not parsed.hostname:
        result.errors.append("DATABASE_URL must include a hostname")

    query = parse_qs(parsed.query or "")
    sslmode_values = [value.strip().lower() for value in query.get("sslmode", []) if value]
    if "require" not in sslmode_values:
        result.errors.append("DATABASE_URL must include sslmode=require for Render runtime")


def _validate_modal_endpoints(env: dict[str, str], result: ValidationResult) -> None:
    model_endpoint = env.get("VECINITA_MODEL_API_URL", "")
    embed_endpoint = env.get("VECINITA_EMBEDDING_API_URL", "")
    scraper_endpoint = env.get("VECINITA_SCRAPER_API_URL", "")

    if model_endpoint and ".modal.run" not in model_endpoint:
        result.errors.append("VECINITA_MODEL_API_URL must point to a direct Modal endpoint")

    if embed_endpoint and ".modal.run" not in embed_endpoint:
        result.errors.append("VECINITA_EMBEDDING_API_URL must point to a direct Modal endpoint")

    if scraper_endpoint and ".modal.run" not in scraper_endpoint:
        result.errors.append("VECINITA_SCRAPER_API_URL must point to a direct Modal endpoint")


def _validate_strict_flags(env: dict[str, str], result: ValidationResult) -> None:
    if not _is_truthy(env.get("RENDER_REMOTE_INFERENCE_ONLY")):
        result.errors.append("RENDER_REMOTE_INFERENCE_ONLY must be enabled for Render runtime")


def _validate_provider_keys(env: dict[str, str], result: ValidationResult) -> None:
    provider_keys = ["GROQ_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]
    if not any((env.get(key) or "").strip() for key in provider_keys):
        result.warnings.append(
            "No LLM provider key set (GROQ_API_KEY/OPENAI_API_KEY/DEEPSEEK_API_KEY); "
            "verify remote inference provider configuration"
        )


def _validate_frontend_contract(env: dict[str, str], result: ValidationResult) -> None:
    allowed = env.get("ALLOWED_ORIGINS", "")
    # Keep a warning-level contract for local/staging parity with internal frontend hostnames.
    expects_internal_dev_origin = "vecinita-frontend:5173"
    if expects_internal_dev_origin not in allowed:
        result.warnings.append(
            "ALLOWED_ORIGINS does not explicitly include vecinita-frontend:5173; verify intended staging/dev CORS contract"
        )


def validate_shared_render_env(env: dict[str, str]) -> ValidationResult:
    """Validate shared Render env contract used by multiple services."""
    result = ValidationResult()
    _validate_required_keys(env, result)
    _validate_scraper_api_keys_not_placeholder(env, result)
    _validate_db_data_mode(env, result)
    _validate_database_url(env, result)
    _validate_modal_endpoints(env, result)
    _validate_strict_flags(env, result)
    _validate_provider_keys(env, result)
    _validate_frontend_contract(env, result)
    return result
