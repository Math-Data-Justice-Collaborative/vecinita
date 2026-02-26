"""Unit tests for the Chroma-backed database search tool."""

import json
import importlib.util
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

_DB_SEARCH_PATH = Path(__file__).resolve().parents[1] / "src" / "agent" / "tools" / "db_search.py"
_DB_SEARCH_SPEC = importlib.util.spec_from_file_location("src.agent.tools.db_search", _DB_SEARCH_PATH)
assert _DB_SEARCH_SPEC is not None and _DB_SEARCH_SPEC.loader is not None
db_search_module = importlib.util.module_from_spec(_DB_SEARCH_SPEC)
sys.modules[_DB_SEARCH_SPEC.name] = db_search_module
_DB_SEARCH_SPEC.loader.exec_module(db_search_module)

create_db_search_tool = db_search_module.create_db_search_tool
reset_search_options = db_search_module.reset_search_options
set_search_options = db_search_module.set_search_options


@pytest.fixture
def mock_store():
    store = Mock()
    store.query_chunks.return_value = []
    return store


@pytest.fixture
def mock_embedding_model():
    model = Mock()
    model.embed_query.return_value = [0.1] * 384
    return model


@pytest.fixture
def db_search_tool(mock_store, mock_embedding_model):
    return create_db_search_tool(mock_store, mock_embedding_model, match_threshold=0.3, match_count=5)


def test_db_search_returns_empty_when_no_results(db_search_tool, mock_store):
    mock_store.query_chunks.return_value = []
    assert db_search_tool.invoke("nonexistent") == "[]"


def test_db_search_normalizes_documents(db_search_tool, mock_store):
    mock_store.query_chunks.return_value = [
        {
            "content": "Community health services",
            "source_url": "https://example.com/health",
            "source_domain": "example.com",
            "similarity": 0.95,
            "metadata": {"chunk_index": 0, "total_chunks": 2},
        }
    ]

    results = json.loads(db_search_tool.invoke("health services"))
    assert len(results) == 1
    assert results[0]["content"] == "Community health services"
    assert results[0]["source_url"] == "https://example.com/health"
    assert results[0]["source_domain"] == "example.com"
    assert results[0]["chunk_index"] == 0


def test_db_search_calls_embedding_model(db_search_tool, mock_embedding_model):
    db_search_tool.invoke("test query")
    mock_embedding_model.embed_query.assert_called_once_with("test query")


def test_db_search_passes_tag_filter(db_search_tool, mock_store):
    token = set_search_options(tags=["housing", "food"], tag_match_mode="all", include_untagged_fallback=False)
    try:
        db_search_tool.invoke("housing help")
    finally:
        reset_search_options(token)

    assert mock_store.query_chunks.call_count >= 1
    _, kwargs = mock_store.query_chunks.call_args
    assert "where" in kwargs
    where = kwargs["where"]
    assert "$and" in where


def test_db_search_reranks_when_enabled(db_search_tool, mock_store):
    mock_store.query_chunks.return_value = [
        {
            "content": "General neighborhood information",
            "source_url": "https://example.com/general",
            "similarity": 0.93,
            "metadata": {},
        },
        {
            "content": "Housing assistance program and shelter support details",
            "source_url": "https://example.com/housing",
            "similarity": 0.70,
            "metadata": {},
        },
    ]

    token = set_search_options(rerank=True, rerank_top_k=2)
    try:
        results = json.loads(db_search_tool.invoke("housing assistance"))
    finally:
        reset_search_options(token)

    assert results[0]["source_url"] == "https://example.com/housing"


def test_db_search_tool_metadata(db_search_tool):
    assert db_search_tool.name == "db_search"
    assert "knowledge base" in db_search_tool.description.lower()


def test_db_search_uses_supabase_fallback_when_chroma_fails(monkeypatch, mock_embedding_model):
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("chroma unavailable")

    mock_rpc = Mock()
    mock_rpc.execute.return_value = Mock(
        data=[
            {
                "id": "doc-1",
                "content": "Housing support resources",
                "source_url": "https://example.org/housing",
                "source_domain": "example.org",
                "similarity": 0.91,
                "metadata": {"chunk_index": 0, "total_chunks": 1},
            }
        ]
    )
    mock_supabase = Mock()
    mock_supabase.rpc.return_value = mock_rpc

    monkeypatch.setenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setattr(db_search_module, "_SUPABASE_CLIENT", None)
    monkeypatch.setattr(db_search_module, "create_client", lambda _url, _key: mock_supabase)

    tool = create_db_search_tool(mock_store, mock_embedding_model, match_threshold=0.3, match_count=5)
    results = json.loads(tool.invoke("housing"))

    assert len(results) == 1
    assert results[0]["source_url"] == "https://example.org/housing"
    assert results[0]["similarity"] == pytest.approx(0.91)


def test_db_search_returns_empty_when_fallback_disabled_and_chroma_fails(monkeypatch, mock_embedding_model):
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("chroma unavailable")

    monkeypatch.setenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "false")
    monkeypatch.setattr(db_search_module, "_SUPABASE_CLIENT", None)

    tool = create_db_search_tool(mock_store, mock_embedding_model, match_threshold=0.3, match_count=5)
    assert tool.invoke("housing") == "[]"


def test_db_search_supabase_fallback_uses_legacy_rpc_signature_when_tag_signature_missing(monkeypatch, mock_embedding_model):
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("chroma unavailable")

    mock_rpc_chain = Mock()
    mock_rpc_chain.execute.side_effect = [
        Exception("search_similar_documents(tag_filter) does not exist"),
        Mock(
            data=[
                {
                    "id": "doc-legacy-1",
                    "content": "Food pantry support",
                    "source_url": "https://example.org/food",
                    "source_domain": "example.org",
                    "similarity": 0.88,
                    "metadata": {},
                }
            ]
        ),
    ]
    mock_supabase = Mock()
    mock_supabase.rpc.return_value = mock_rpc_chain

    monkeypatch.setenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setattr(db_search_module, "_SUPABASE_CLIENT", None)
    monkeypatch.setattr(db_search_module, "create_client", lambda _url, _key: mock_supabase)

    token = set_search_options(tags=["food"], tag_match_mode="all", include_untagged_fallback=False)
    try:
        tool = create_db_search_tool(mock_store, mock_embedding_model, match_threshold=0.3, match_count=5)
        results = json.loads(tool.invoke("food"))
    finally:
        reset_search_options(token)

    assert len(results) == 1
    assert results[0]["source_url"] == "https://example.org/food"
    assert mock_supabase.rpc.call_count == 2
