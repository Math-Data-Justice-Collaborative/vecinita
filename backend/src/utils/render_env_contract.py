"""Validation helpers for the shared Render environment contract.

This module enforces a minimal safety contract for the shared
`.env.prod.render` environment group. The goal is to catch configuration
regressions before deploys by validating required keys and critical
cross-key consistency constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

REQUIRED_KEYS: set[str] = {
    "DATABASE_URL",
    "OLLAMA_MODEL",
    "RENDER_REMOTE_INFERENCE_ONLY",
    "MODAL_TOKEN_SECRET",
    "VECINITA_MODEL_API_URL",
    "VECINITA_EMBEDDING_API_URL",
    "VECINITA_SCRAPER_API_URL",
    "VITE_GATEWAY_URL",
    "VITE_BACKEND_URL",
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
    _validate_modal_endpoints(env, result)
    _validate_strict_flags(env, result)
    _validate_frontend_contract(env, result)
    return result
