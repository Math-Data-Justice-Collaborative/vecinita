"""Unit tests for the Postgres database search tool."""

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
def db_search_tool(mock_store, mock_embedding_model, monkeypatch):
    monkeypatch.setattr(
        db_search_module,
        "_query_postgres_fallback",
        lambda **kwargs: mock_store.query_chunks(**kwargs),
    )
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

    monkeypatch.setattr(
        db_search_module,
        "_query_postgres_fallback",
        lambda **kwargs: mock_store.query_chunks(**kwargs),
    )

    _ = tool.invoke("Need housing support")
    metrics = get_last_search_metrics()

    assert metrics["status"] == "ok"
    assert metrics["retrieval_backend"] == "postgres"
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
    assert kwargs.get("tags") == ["housing", "food"]
    assert kwargs.get("tag_mode") == "all"
    assert kwargs.get("include_untagged_fallback") is False


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
    assert "immigration" in kwargs.get("tags", [])


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
    assert "healthcare providers" in kwargs.get("tags", [])


def test_db_search_returns_empty_when_postgres_returns_no_rows(monkeypatch, mock_embedding_model):
    mock_store = Mock()
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", lambda **_kwargs: [])

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    results = json.loads(tool.invoke("doctor in providence"))

    assert results == []


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


def test_db_search_returns_postgres_rows_when_available(monkeypatch, mock_embedding_model):
    mock_store = Mock()
    monkeypatch.setattr(
        db_search_module,
        "_query_postgres_fallback",
        lambda **_kwargs: [
            {
                "id": "doc-1",
                "content": "Housing support resources",
                "source_url": "https://example.org/housing",
                "source_domain": "example.org",
                "similarity": 0.91,
                "metadata": {"chunk_index": 0, "total_chunks": 1},
            }
        ],
    )

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    results = json.loads(tool.invoke("housing"))

    assert len(results) == 1
    assert results[0]["source_url"] == "https://example.org/housing"
    assert results[0]["similarity"] == pytest.approx(0.91)


def test_db_search_returns_empty_when_fallback_disabled_and_primary_store_fails(
    monkeypatch, mock_embedding_model
):
    mock_store = Mock()
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", lambda **_kwargs: [])

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    assert tool.invoke("housing") == "[]"


def test_db_search_uses_postgres_fallback_when_data_mode_is_postgres(
    monkeypatch, mock_embedding_model
):
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("primary store unavailable")

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setenv("POSTGRES_DATA_READS_ENABLED", "true")

    mock_postgres = Mock(
        return_value=[
            {
                "id": "doc-pg-1",
                "content": "Postgres fallback result",
                "source_url": "https://example.org/postgres",
                "source_domain": "example.org",
                "similarity": 0.87,
                "metadata": {},
            }
        ]
    )
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", mock_postgres)

    import src.config as app_config

    importlib.reload(app_config)

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    results = json.loads(tool.invoke("housing"))

    assert len(results) == 1
    assert results[0]["source_url"] == "https://example.org/postgres"
    metrics = get_last_search_metrics()
    assert metrics["retrieval_backend"] == "postgres"


def test_db_search_prefers_postgres_when_database_url_present(monkeypatch, mock_embedding_model):
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("primary store unavailable")

    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

    postgres_mock = Mock(return_value=[])
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", postgres_mock)

    import src.config as app_config

    importlib.reload(app_config)

    tool = create_db_search_tool(
        mock_store, mock_embedding_model, match_threshold=0.3, match_count=5
    )
    _ = tool.invoke("housing")

    assert postgres_mock.called


def test_db_search_tag_filter_uses_postgres_only(
    monkeypatch, mock_embedding_model
):
    mock_store = Mock()
    mock_store.query_chunks.side_effect = RuntimeError("primary store unavailable")
    postgres_mock = Mock(
        return_value=[
            {
                "id": "doc-legacy-1",
                "content": "Food pantry support",
                "source_url": "https://example.org/food",
                "source_domain": "example.org",
                "similarity": 0.88,
                "metadata": {},
            }
        ]
    )
    monkeypatch.setattr(db_search_module, "_query_postgres_fallback", postgres_mock)

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
    assert postgres_mock.called
