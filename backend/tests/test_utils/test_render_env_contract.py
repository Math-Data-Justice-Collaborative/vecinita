import pytest

from src.utils.render_env_contract import parse_env_file, validate_shared_render_env

pytestmark = pytest.mark.unit


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


def test_validate_shared_render_env_accepts_valid_contract():
    env = {
        "DATABASE_URL": "postgresql://user:pass@host/db?sslmode=require",
        "DB_DATA_MODE": "postgres",
        "OLLAMA_MODEL": "llama3.1:8b",
        "RENDER_REMOTE_INFERENCE_ONLY": "true",
        "MODAL_TOKEN_SECRET": "as-example",
        "VECINITA_MODEL_API_URL": "https://vecinita--vecinita-model-api.modal.run",
        "VECINITA_EMBEDDING_API_URL": "https://vecinita--vecinita-embedding-api.modal.run",
        "VECINITA_SCRAPER_API_URL": "https://scraper.modal.run",
        "VITE_GATEWAY_URL": "https://gateway.onrender.com/api/v1",
        "VITE_BACKEND_URL": "https://agent.onrender.com",
        "ALLOWED_ORIGINS": "http://vecinita-frontend:5173,https://vecinita-frontend.onrender.com",
    }

    result = validate_shared_render_env(env)

    assert result.errors == []


def test_validate_shared_render_env_flags_missing_and_inconsistent_values():
    env = {
        "DATABASE_URL": "https://not-postgres.example.com/db",
        "DB_DATA_MODE": "auto",
        "OLLAMA_MODEL": "llama3.1:8b",
        "RENDER_REMOTE_INFERENCE_ONLY": "false",
        "MODAL_TOKEN_SECRET": "as-example",
        "VECINITA_MODEL_API_URL": "https://model.example.com",
        "VECINITA_EMBEDDING_API_URL": "https://embedding.example.com",
        "VECINITA_SCRAPER_API_URL": "https://scraper.example.com",
        "VITE_GATEWAY_URL": "https://gateway.onrender.com/api/v1",
        "VITE_BACKEND_URL": "https://agent.onrender.com",
    }

    result = validate_shared_render_env(env)

    assert "DATABASE_URL must use postgres:// or postgresql:// scheme" in result.errors
    assert "VECINITA_MODEL_API_URL must point to a direct Modal endpoint" in result.errors
    assert "VECINITA_EMBEDDING_API_URL must point to a direct Modal endpoint" in result.errors
    assert "VECINITA_SCRAPER_API_URL must point to a direct Modal endpoint" in result.errors
    assert "RENDER_REMOTE_INFERENCE_ONLY must be enabled for Render runtime" in result.errors
    assert "DB_DATA_MODE must be set to postgres for Render runtime" in result.errors


def test_validate_shared_render_env_warns_when_frontend_origin_missing():
    env = {
        "DATABASE_URL": "postgresql://user:pass@host/db?sslmode=require",
        "DB_DATA_MODE": "postgres",
        "OLLAMA_MODEL": "llama3.1:8b",
        "RENDER_REMOTE_INFERENCE_ONLY": "true",
        "MODAL_TOKEN_SECRET": "as-example",
        "VECINITA_MODEL_API_URL": "https://vecinita--vecinita-model-api.modal.run",
        "VECINITA_EMBEDDING_API_URL": "https://vecinita--vecinita-embedding-api.modal.run",
        "VECINITA_SCRAPER_API_URL": "https://scraper.modal.run",
        "VITE_GATEWAY_URL": "https://gateway.onrender.com/api/v1",
        "VITE_BACKEND_URL": "https://agent.onrender.com",
        "ALLOWED_ORIGINS": "https://vecinita-frontend.onrender.com",
    }

    result = validate_shared_render_env(env)

    assert result.errors == []
    assert result.warnings


def test_validate_shared_render_env_requires_sslmode_require_for_database_url():
    env = {
        "DATABASE_URL": "postgresql://user:pass@host/db",
        "DB_DATA_MODE": "postgres",
        "OLLAMA_MODEL": "llama3.1:8b",
        "RENDER_REMOTE_INFERENCE_ONLY": "true",
        "MODAL_TOKEN_SECRET": "as-example",
        "VECINITA_MODEL_API_URL": "https://vecinita--vecinita-model-api.modal.run",
        "VECINITA_EMBEDDING_API_URL": "https://vecinita--vecinita-embedding-api.modal.run",
        "VECINITA_SCRAPER_API_URL": "https://scraper.modal.run",
        "VITE_GATEWAY_URL": "https://gateway.onrender.com/api/v1",
        "VITE_BACKEND_URL": "https://agent.onrender.com",
        "ALLOWED_ORIGINS": "http://vecinita-frontend:5173,https://vecinita-frontend.onrender.com",
    }

    result = validate_shared_render_env(env)

    assert "DATABASE_URL must include sslmode=require for Render runtime" in result.errors
