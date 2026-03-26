"""Unit tests for the Chroma-backed database search tool."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

_DB_SEARCH_PATH = Path(__file__).resolve().parents[1] / "src" / "agent" / "tools" / "db_search.py"
_DB_SEARCH_SPEC = importlib.util.spec_from_file_location(
    "src.agent.tools.db_search", _DB_SEARCH_PATH
)
assert _DB_SEARCH_SPEC is not None and _DB_SEARCH_SPEC.loader is not None
db_search_module = importlib.util.module_from_spec(_DB_SEARCH_SPEC)
sys.modules[_DB_SEARCH_SPEC.name] = db_search_module
_DB_SEARCH_SPEC.loader.exec_module(db_search_module)

create_db_search_tool = db_search_module.create_db_search_tool
get_last_search_metrics = db_search_module.get_last_search_metrics
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
    return create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )


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


def test_db_search_reuses_cached_embedding_for_normalized_query(
    monkeypatch, mock_store, mock_embedding_model
):
    monkeypatch.setenv("DB_SEARCH_EMBED_CACHE_SIZE", "8")
    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    tool.invoke("Need housing help")
    tool.invoke("  need   housing   help  ")
    assert mock_embedding_model.embed_query.call_count == 1


def test_db_search_embedding_cache_can_be_disabled(monkeypatch, mock_store, mock_embedding_model):
    monkeypatch.setenv("DB_SEARCH_EMBED_CACHE_SIZE", "0")
    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    tool.invoke("Need housing help")
    tool.invoke("need housing help")
    assert mock_embedding_model.embed_query.call_count == 2


def test_db_search_exposes_latency_metrics(monkeypatch, mock_store, mock_embedding_model):
    monkeypatch.setenv("DB_SEARCH_EMBED_CACHE_SIZE", "8")
    mock_store.query_chunks.return_value = [
        {
            "content": "Housing support resources",
            "source_url": "https://example.org/housing",
            "source_domain": "example.org",
            "similarity": 0.91,
            "metadata": {},
        }
    ]
    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )

    _ = tool.invoke("Need housing support")
    metrics = get_last_search_metrics()

    assert metrics["status"] == "ok"
    assert metrics["retrieval_backend"] == "chroma"
    assert isinstance(metrics["total_ms"], int)
    assert metrics["rows_before_threshold"] == 1
    assert metrics["rows_after_threshold"] == 1


def test_db_search_metrics_marks_cache_hit(monkeypatch, mock_store, mock_embedding_model):
    monkeypatch.setenv("DB_SEARCH_EMBED_CACHE_SIZE", "8")
    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )

    _ = tool.invoke("Need housing help")
    _ = tool.invoke("need   housing   help")
    metrics = get_last_search_metrics()

    assert metrics["cache_hit"] is True


def test_db_search_passes_tag_filter(db_search_tool, mock_store):
    token = set_search_options(
        tags=["housing", "food"], tag_match_mode="all", include_untagged_fallback=False
    )
    try:
        db_search_tool.invoke("housing help")
    finally:
        reset_search_options(token)

    assert mock_store.query_chunks.call_count >= 1
    _, kwargs = mock_store.query_chunks.call_args
    assert "where" in kwargs
    where = kwargs["where"]
    assert "$and" in where


def test_db_search_auto_infers_spanish_tags_for_filtering(monkeypatch, db_search_tool, mock_store):
    mock_store.query_chunks.return_value = [
        {
            "content": "Immigration legal aid resources",
            "source_url": "https://example.org/immigration",
            "source_domain": "example.org",
            "similarity": 0.9,
            "metadata": {"tags": ["immigration"]},
        }
    ]

    monkeypatch.setenv("TAG_FILTER_AUTO_INFER", "true")
    token = set_search_options(tags=[], tag_match_mode="any", include_untagged_fallback=True)
    try:
        _ = db_search_tool.invoke("Necesito ayuda de inmigración")
    finally:
        reset_search_options(token)

    _, kwargs = mock_store.query_chunks.call_args
    where = kwargs.get("where")
    assert where is not None
    assert "immigration" in str(where)


def test_db_search_auto_infers_doctor_intent_from_spanish_typo(
    monkeypatch, db_search_tool, mock_store
):
    mock_store.query_chunks.return_value = []
    monkeypatch.setenv("TAG_FILTER_AUTO_INFER", "true")

    token = set_search_options(tags=[], tag_match_mode="any", include_untagged_fallback=True)
    try:
        _ = db_search_tool.invoke("Dame unos doctos en Providence")
    finally:
        reset_search_options(token)

    _, kwargs = mock_store.query_chunks.call_args
    where = kwargs.get("where")
    assert where is not None
    assert "healthcare providers" in str(where)


def test_db_search_uses_supabase_fallback_when_chroma_query_times_out(
    monkeypatch, mock_embedding_model
):
    mock_store = Mock()

    def _slow_query(**_kwargs):
        import time

        time.sleep(1.2)
        return []

    mock_store.query_chunks.side_effect = _slow_query

    mock_rpc = Mock()
    mock_rpc.execute.return_value = Mock(
        data=[
            {
                "id": "doc-timeout-1",
                "content": "Healthcare directory",
                "source_url": "https://example.org/health",
                "source_domain": "example.org",
                "similarity": 0.9,
                "metadata": {},
            }
        ]
    )
    mock_supabase = Mock()
    mock_supabase.rpc.return_value = mock_rpc

    monkeypatch.setenv("DB_SEARCH_CHROMA_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setattr(db_search_module, "_SUPABASE_CLIENT", None)
    monkeypatch.setattr(db_search_module, "create_client", lambda _url, _key: mock_supabase)

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    results = json.loads(tool.invoke("doctor in providence"))

    assert len(results) == 1
    assert results[0]["source_url"] == "https://example.org/health"


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

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    results = json.loads(tool.invoke("housing"))

    assert len(results) == 1
    assert results[0]["source_url"] == "https://example.org/housing"
    assert results[0]["similarity"] == pytest.approx(0.91)


def test_db_search_returns_empty_when_fallback_disabled_and_chroma_fails(
    monkeypatch, mock_embedding_model
):
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("chroma unavailable")

    monkeypatch.setenv("VECTOR_SYNC_SUPABASE_FALLBACK_READS", "false")
    monkeypatch.setattr(db_search_module, "_SUPABASE_CLIENT", None)

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    assert tool.invoke("housing") == "[]"


def test_db_search_supabase_fallback_uses_legacy_rpc_signature_when_tag_signature_missing(
    monkeypatch, mock_embedding_model
):
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
        tool = create_db_search_tool(
            mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
        )
        results = json.loads(tool.invoke("food"))
    finally:
        reset_search_options(token)

    assert len(results) == 1
    assert results[0]["source_url"] == "https://example.org/food"
    assert mock_supabase.rpc.call_count == 2
