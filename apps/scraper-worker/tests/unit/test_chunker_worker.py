"""Unit tests for chunker worker orchestration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from vecinita_scraper.core.models import ChunkingConfig, ChunkJobQueueData, JobStatus
from vecinita_scraper.workers.chunker import run_chunking_job


class FakeQueue:
    """Captures queued items for assertions."""

    def __init__(self) -> None:
        self.items: list[dict[str, object]] = []
        self.put = SimpleNamespace(aio=self._put)

    async def _put(self, payload: dict[str, object]) -> None:
        self.items.append(payload)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_chunking_job_stores_chunks_and_enqueues_embedding_batches(
    mock_db, monkeypatch
) -> None:
    """Chunked documents should be persisted and queued for embedding."""
    job = ChunkJobQueueData(
        job_id="job-123",
        processed_doc_id="processed-1",
        markdown_content="chunk one\n\nchunk two",
        chunking_config=ChunkingConfig(min_size_tokens=100, max_size_tokens=200, overlap_ratio=0.2),
    )
    queue = FakeQueue()
    chunks = [
        {"text": "chunk one", "position": 0, "token_count": 2, "semantic_boundary": True},
        {"text": "chunk two", "position": 1, "token_count": 2, "semantic_boundary": True},
    ]

    monkeypatch.setattr(
        "vecinita_scraper.workers.chunker.SemanticChunker.chunk",
        lambda self, markdown_content, config: chunks,
    )
    mock_db.store_chunks.return_value = ["chunk-1", "chunk-2"]

    result = await run_chunking_job(job, db=mock_db, embed_queue=queue)

    assert result["chunk_count"] == 2
    assert result["next_status"] == JobStatus.EMBEDDING.value
    assert queue.items[0]["chunk_ids"] == ["chunk-1", "chunk-2"]
    mock_db.update_job_status.assert_any_await("job-123", JobStatus.CHUNKING.value)
