"""Unit tests for the Chroma-backed database search tool."""

import json
from unittest.mock import Mock

import pytest

from src.agent.tools.db_search import create_db_search_tool, reset_search_options, set_search_options


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
