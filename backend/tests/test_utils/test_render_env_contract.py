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
        "DATABASE_URL": "postgresql://user:pass@host/db",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "sb_secret_x",
        "OLLAMA_MODEL": "llama3.1:8b",
        "AGENT_ENFORCE_PROXY": "true",
        "RENDER_REMOTE_INFERENCE_ONLY": "true",
        "PROXY_AUTH_TOKEN": "token",
        "VECINITA_MODEL_API_URL": "http://vecinita-modal-proxy-v1:10000/model",
        "VECINITA_EMBEDDING_API_URL": "http://vecinita-modal-proxy-v1:10000/embedding",
        "VECINITA_SCRAPER_API_URL": "https://scraper.modal.run",
        "VITE_GATEWAY_URL": "https://gateway.onrender.com/api/v1",
        "VITE_BACKEND_URL": "https://agent.onrender.com",
        "ALLOWED_ORIGINS": "http://vecinita-frontend:5173,https://vecinita-frontend.onrender.com",
    }

    result = validate_shared_render_env(env)

    assert result.errors == []


def test_validate_shared_render_env_flags_missing_and_inconsistent_values():
    env = {
        "DATABASE_URL": "postgresql://user:pass@host/db",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "sb_secret_x",
        "OLLAMA_MODEL": "llama3.1:8b",
        "AGENT_ENFORCE_PROXY": "false",
        "RENDER_REMOTE_INFERENCE_ONLY": "false",
        "PROXY_AUTH_TOKEN": "token",
        "VECINITA_MODEL_API_URL": "https://model.modal.run",
        "VECINITA_EMBEDDING_API_URL": "https://embedding.modal.run",
        "VECINITA_SCRAPER_API_URL": "https://scraper.modal.run",
        "VITE_GATEWAY_URL": "https://gateway.onrender.com/api/v1",
        "VITE_BACKEND_URL": "https://agent.onrender.com",
    }

    result = validate_shared_render_env(env)

    assert (
        "VECINITA_MODEL_API_URL must route through vecinita-modal-proxy-v1:10000/model"
        in result.errors
    )
    assert (
        "VECINITA_EMBEDDING_API_URL must route through vecinita-modal-proxy-v1:10000/embedding"
        in result.errors
    )
    assert "AGENT_ENFORCE_PROXY must be enabled for Render runtime" in result.errors
    assert "RENDER_REMOTE_INFERENCE_ONLY must be enabled for Render runtime" in result.errors


def test_validate_shared_render_env_warns_when_frontend_origin_missing():
    env = {
        "DATABASE_URL": "postgresql://user:pass@host/db",
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "sb_secret_x",
        "OLLAMA_MODEL": "llama3.1:8b",
        "AGENT_ENFORCE_PROXY": "true",
        "RENDER_REMOTE_INFERENCE_ONLY": "true",
        "PROXY_AUTH_TOKEN": "token",
        "VECINITA_MODEL_API_URL": "http://vecinita-modal-proxy-v1:10000/model",
        "VECINITA_EMBEDDING_API_URL": "http://vecinita-modal-proxy-v1:10000/embedding",
        "VECINITA_SCRAPER_API_URL": "https://scraper.modal.run",
        "VITE_GATEWAY_URL": "https://gateway.onrender.com/api/v1",
        "VITE_BACKEND_URL": "https://agent.onrender.com",
        "ALLOWED_ORIGINS": "https://vecinita-frontend.onrender.com",
    }

    result = validate_shared_render_env(env)

    assert result.errors == []
    assert result.warnings
