import pytest
from unittest.mock import Mock

from src.services.chroma_store import ChromaStore

pytestmark = pytest.mark.unit


def test_upsert_chunks_drops_empty_tags_from_metadata():
    store = ChromaStore()
    mock_chunks = Mock()
    store._chunks = mock_chunks

    inserted = {}

    def _capture(**kwargs):
        inserted.update(kwargs)

    mock_chunks.upsert.side_effect = _capture

    count = store.upsert_chunks(
        [
            {
                "id": "row-1",
                "content": "text",
                "embedding": [0.1, 0.2, 0.3],
                "source_url": "https://wrwc.org/services",
                "metadata": {"tags": []},
            }
        ]
    )

    assert count == 1
    metadata = inserted["metadatas"][0]
    assert "tags" not in metadata


def test_upsert_source_drops_empty_tags_from_metadata():
    store = ChromaStore()
    mock_sources = Mock()
    store._sources = mock_sources

    inserted = {}

    def _capture(**kwargs):
        inserted.update(kwargs)

    mock_sources.upsert.side_effect = _capture

    store.upsert_source(url="https://wrwc.org/chat", metadata={"tags": []}, title="Chat")

    metadata = inserted["metadatas"][0]
    assert metadata["url"] == "https://wrwc.org/chat"
    assert "tags" not in metadata
