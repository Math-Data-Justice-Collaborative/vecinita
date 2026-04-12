import pytest

from src.utils.render_env_contract import parse_env_file, validate_shared_render_env

pytestmark = pytest.mark.unit


@pytest.fixture
def minimal_valid_render_env():
    """Minimal env dict satisfying REQUIRED_KEYS and consistency checks for Render."""
    return {
        "ALLOWED_ORIGINS": "http://vecinita-frontend:5173,https://vecinita-frontend.onrender.com",
        "CORS_ORIGINS": "https://vecinita-frontend.onrender.com",
        "DATABASE_URL": "postgresql://user:pass@host/db?sslmode=require",
        "DB_DATA_MODE": "postgres",
        "EMBEDDING_SERVICE_AUTH_TOKEN": "test-embed-token",
        "MODAL_TOKEN_ID": "ak-example",
        "MODAL_TOKEN_SECRET": "as-example",
        "MODAL_WORKSPACE": "vecinita",
        "OLLAMA_MODEL": "llama3.1:8b",
        "RENDER_REMOTE_INFERENCE_ONLY": "true",
        "SCRAPER_API_KEYS": "key1,key2",
        "VECINITA_MODEL_API_URL": "https://vecinita--vecinita-model-api.modal.run",
        "VECINITA_EMBEDDING_API_URL": "https://vecinita--vecinita-embedding-api.modal.run",
        "VECINITA_SCRAPER_API_URL": "https://scraper.modal.run",
        "VITE_GATEWAY_URL": "https://gateway.onrender.com/api/v1",
        "VITE_BACKEND_URL": "https://agent.onrender.com",
        "VITE_VECINITA_SCRAPER_API_URL": "https://scraper.modal.run",
    }


def test_parse_env_file_ignores_comments_and_empty_lines(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
# comment
FOO=bar

BAZ = qux
INVALID_LINE
""",
        encoding="utf-8",
    )

    parsed = parse_env_file(env_file)

    assert parsed == {"FOO": "bar", "BAZ": "qux"}


def test_validate_shared_render_env_accepts_valid_contract(minimal_valid_render_env):
    result = validate_shared_render_env(minimal_valid_render_env)

    assert result.errors == []


def test_validate_shared_render_env_flags_missing_and_inconsistent_values(minimal_valid_render_env):
    env = {
        **minimal_valid_render_env,
        "DATABASE_URL": "https://not-postgres.example.com/db",
        "DB_DATA_MODE": "auto",
        "RENDER_REMOTE_INFERENCE_ONLY": "false",
        "VECINITA_MODEL_API_URL": "https://model.example.com",
        "VECINITA_EMBEDDING_API_URL": "https://embedding.example.com",
        "VECINITA_SCRAPER_API_URL": "https://scraper.example.com",
    }

    result = validate_shared_render_env(env)

    assert "DATABASE_URL must use postgres:// or postgresql:// scheme" in result.errors
    assert "VECINITA_MODEL_API_URL must point to a direct Modal endpoint" in result.errors
    assert "VECINITA_EMBEDDING_API_URL must point to a direct Modal endpoint" in result.errors
    assert "VECINITA_SCRAPER_API_URL must point to a direct Modal endpoint" in result.errors
    assert "RENDER_REMOTE_INFERENCE_ONLY must be enabled for Render runtime" in result.errors
    assert "DB_DATA_MODE must be set to postgres for Render runtime" in result.errors


def test_validate_shared_render_env_warns_when_frontend_origin_missing(minimal_valid_render_env):
    env = {
        **minimal_valid_render_env,
        "ALLOWED_ORIGINS": "https://vecinita-frontend.onrender.com",
    }

    result = validate_shared_render_env(env)

    assert result.errors == []
    assert result.warnings


def test_validate_shared_render_env_requires_sslmode_require_for_database_url(
    minimal_valid_render_env,
):
    env = {**minimal_valid_render_env, "DATABASE_URL": "postgresql://user:pass@host/db"}

    result = validate_shared_render_env(env)

    assert "DATABASE_URL must include sslmode=require for Render runtime" in result.errors


def test_validate_shared_render_env_rejects_scraper_api_keys_template_placeholder(
    minimal_valid_render_env,
):
    env = {
        **minimal_valid_render_env,
        "SCRAPER_API_KEYS": "replace-with-comma-separated-api-keys",
    }

    result = validate_shared_render_env(env)

    assert any("SCRAPER_API_KEYS is still the template placeholder" in e for e in result.errors)


def test_validate_shared_render_env_rejects_reindex_url_without_scheme(minimal_valid_render_env):
    env = {**minimal_valid_render_env, "REINDEX_SERVICE_URL": "vecinita-scraper-api/jobs"}

    result = validate_shared_render_env(env)

    assert any("REINDEX_SERVICE_URL must include" in e for e in result.errors)


def test_validate_shared_render_env_accepts_valid_reindex_url(minimal_valid_render_env):
    env = {
        **minimal_valid_render_env,
        "REINDEX_SERVICE_URL": "https://vecinita--vecinita-scraper-api-fastapi.modal.run/jobs",
    }

    result = validate_shared_render_env(env)

    assert result.errors == []


def test_validate_shared_render_env_rejects_reindex_url_https_without_hostname(
    minimal_valid_render_env,
):
    env = {**minimal_valid_render_env, "REINDEX_SERVICE_URL": "https:///jobs"}

    result = validate_shared_render_env(env)

    assert any("REINDEX_SERVICE_URL must include a hostname" in e for e in result.errors)
