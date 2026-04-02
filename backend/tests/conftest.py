"""
Shared pytest fixtures and configuration for the Vecinita test suite.
"""

import json
import os
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

# Load environment variables for tests
load_dotenv()


@pytest.fixture(scope="session")
def env_vars():
    """Provide environment variables for tests."""

    def _env_or_default(key: str, default: str) -> str:
        value = os.getenv(key)
        if value is None or str(value).strip() == "":
            return default
        return value

    return {
        "SUPABASE_URL": _env_or_default("SUPABASE_URL", "https://test.supabase.co"),
        "SUPABASE_KEY": _env_or_default("SUPABASE_KEY", "test-key"),
        "OLLAMA_BASE_URL": _env_or_default("OLLAMA_BASE_URL", "http://localhost:10000/model"),
        "MODAL_OLLAMA_ENDPOINT": _env_or_default(
            "MODAL_OLLAMA_ENDPOINT", "http://localhost:10000/model"
        ),
        "OLLAMA_MODEL": _env_or_default("OLLAMA_MODEL", "llama3.1:8b"),
        # Keep tests deterministic regardless of runner-level env overrides.
        "AGENT_ENFORCE_PROXY": "false",
        "DATABASE_URL": _env_or_default("DATABASE_URL", "postgresql://test"),
    }


@pytest.fixture(scope="session", autouse=True)
def _agent_module_path_compatibility():
    """Provide compatibility aliases for canonical agent test imports."""
    if os.getenv("SKIP_AGENT_MAIN_IMPORT", "false").lower() in {"1", "true", "yes"}:
        yield
        return

    import importlib.machinery
    import sys
    import types
    from unittest.mock import Mock

    # Avoid importing broken/binary torch during test module import.
    if "torch" not in sys.modules:
        fake_torch = types.ModuleType("torch")
        fake_torch.__version__ = "0.0-test"
        fake_torch.__spec__ = importlib.machinery.ModuleSpec("torch", loader=None)
        sys.modules["torch"] = fake_torch

    # Stub embedding service client before importing src.agent.main.
    fake_embedding_module = types.ModuleType("src.embedding_service.client")
    fake_chroma_store_module = types.ModuleType("src.services.chroma_store")
    fake_psycopg2_module = types.ModuleType("psycopg2")
    fake_psycopg2_extras_module = types.ModuleType("psycopg2.extras")

    class _FakeChromaStore:
        def heartbeat(self):
            return True

    def _fake_create_embedding_client(*_args, **_kwargs):
        mock_embedding = Mock()
        mock_embedding.embed_query = Mock(return_value=[0.1] * 384)
        mock_embedding.embed_documents = Mock(return_value=[[0.1] * 384])
        return mock_embedding

    def _fake_get_chroma_store(*_args, **_kwargs):
        return Mock(heartbeat=Mock(return_value=True))

    fake_embedding_module.create_embedding_client = _fake_create_embedding_client
    fake_chroma_store_module.ChromaStore = _FakeChromaStore
    fake_chroma_store_module.get_chroma_store = _fake_get_chroma_store
    fake_psycopg2_extras_module.RealDictCursor = object
    fake_psycopg2_module.extras = fake_psycopg2_extras_module
    sys.modules["src.embedding_service.client"] = fake_embedding_module
    sys.modules["src.services.chroma_store"] = fake_chroma_store_module
    sys.modules["psycopg2"] = fake_psycopg2_module
    sys.modules["psycopg2.extras"] = fake_psycopg2_extras_module

    # Set minimal env vars so module-level LLM provider validation passes.
    _test_env_defaults = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "OLLAMA_BASE_URL": "http://localhost:10000/model",
        "MODAL_OLLAMA_ENDPOINT": "http://localhost:10000/model",
        "OLLAMA_MODEL": "llama3.1:8b",
        "AGENT_ENFORCE_PROXY": "false",
        "DATABASE_URL": "postgresql://test",
    }
    _original_env: dict[str, str | None] = {}
    for _k, _v in _test_env_defaults.items():
        _original_env[_k] = os.environ.get(_k)
        os.environ[_k] = _v

    __import__("src.agent.main")

    yield

    # Restore original environment values exactly, including empty strings.
    for _k, _original_value in _original_env.items():
        if _original_value is None:
            os.environ.pop(_k, None)
        else:
            os.environ[_k] = _original_value


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client for testing."""
    mock_client = Mock()
    mock_client.table = Mock(return_value=Mock())
    mock_client.rpc = Mock(return_value=Mock())
    return mock_client


@pytest.fixture
def mock_embedding_model():
    """Create a mock embedding model."""
    mock_model = Mock()
    mock_model.embed_query = Mock(return_value=[0.1] * 384)  # Mock embedding vector
    return mock_model


@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = "Test response from LLM"
    mock_llm.invoke = Mock(return_value=mock_response)
    return mock_llm


@pytest.fixture
def fastapi_client(env_vars, monkeypatch):
    """Create a FastAPI test client with env vars applied before app import.

    This ensures any environment-based configuration in `main` is picked up
    after tests set or mock environment variables.
    """
    # Ensure required env vars are set prior to importing the app module
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Patch dependencies before importing app
    from unittest.mock import MagicMock

    with (
        patch("src.agent.main.create_client") as mock_supabase,
        patch("src.agent.main.ChatOllama") as mock_ollama,
        patch("src.agent.main.HuggingFaceEmbeddings") as mock_embeddings,
    ):
        # Setup mocks
        mock_supabase_client = MagicMock()
        mock_supabase_client.rpc.return_value.execute.return_value.data = []
        mock_supabase.return_value = mock_supabase_client

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        mock_ollama.return_value = mock_llm

        mock_embedding_model = MagicMock()
        mock_embedding_model.embed_query.return_value = [0.1] * 384
        mock_embeddings.return_value = mock_embedding_model

        # Import after mocks are set
        from src.agent.main import app

        return TestClient(app)


@pytest.fixture
def auth_proxy_client(env_vars, monkeypatch):
    """Create a TestClient for the auth proxy service."""
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    import importlib.util
    import sys
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    auth_main_path = repo_root / "auth" / "src" / "main.py"
    module_name = "vecinita_auth_proxy_main"

    spec = importlib.util.spec_from_file_location(module_name, auth_main_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load auth proxy module from {auth_main_path}")

    auth_module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = auth_module
    spec.loader.exec_module(auth_module)

    return TestClient(auth_module.app)


@pytest.fixture
def mock_auth_header():
    """Provide a standard auth header for gateway auth tests."""
    return {"Authorization": "Bearer sk_vp_test_key_1234567890"}


@pytest.fixture
def parse_sse_events():
    """Parse raw SSE response text into JSON event objects."""

    def _parse(text: str):
        events = []
        for line in text.split("\n"):
            if not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if not payload:
                continue
            try:
                events.append(json.loads(payload))
            except json.JSONDecodeError:
                continue
        return events

    return _parse


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    test_file = tmp_path / "test_input.txt"
    test_file.write_text("test content")
    return test_file


@pytest.fixture
def sample_documents():
    """Provide sample document data for testing."""
    return [
        {
            "id": "1",
            "content": "Sample document content about housing policy.",
            "source": "https://example.com/housing",
            "source_url": "https://example.com/housing",
            "created_at": "2024-01-01T00:00:00Z",
        },
        {
            "id": "2",
            "content": "Community resources and support services.",
            "source": "https://example.com/community",
            "source_url": "https://example.com/community",
            "created_at": "2024-01-02T00:00:00Z",
        },
    ]


@pytest.fixture
def sample_chunks():
    """Provide sample document chunks for testing."""
    return [
        {
            "content": "Chunk 1: Information about housing.",
            "source_url": "https://example.com/housing",
            "chunk_index": 0,
            "total_chunks": 2,
        },
        {
            "content": "Chunk 2: More housing information.",
            "source_url": "https://example.com/housing",
            "chunk_index": 1,
            "total_chunks": 2,
        },
    ]
