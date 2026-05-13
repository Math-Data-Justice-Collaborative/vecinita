"""Unit tests for embedder worker orchestration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from vecinita_scraper.core.models import EmbedJobQueueData, JobStatus
from vecinita_scraper.workers.embedder import run_embedding_job


class FakeQueue:
    """Captures queued items for assertions."""

    def __init__(self) -> None:
        self.items: list[dict[str, object]] = []
        self.put = SimpleNamespace(aio=self._put)

    async def _put(self, payload: dict[str, object]) -> None:
        self.items.append(payload)


class FakeEmbeddingClient:
    """Deterministic embedding client for worker tests."""

    async def batch_embed(self, texts: list[str]) -> dict[str, object]:
        return {
            "embeddings": [[0.1, 0.2], [0.3, 0.4]],
            "model": "test-model",
            "dimensions": 2,
        }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_embedding_job_stores_vectors_and_enqueues_finalization(mock_db) -> None:
    """Embedding results should be stored and forwarded to the finalizer queue."""
    job = EmbedJobQueueData(
        job_id="job-123",
        chunk_ids=["chunk-1", "chunk-2"],
        chunk_texts=["text one", "text two"],
    )
    queue = FakeQueue()
    client = FakeEmbeddingClient()

    result = await run_embedding_job(job, db=mock_db, store_queue=queue, embedding_client=client)

    assert result["embedding_count"] == 2
    assert result["next_status"] == JobStatus.STORING.value
    assert queue.items[0]["embedding_ids"] == ["chunk-1", "chunk-2"]
    mock_db.update_job_status.assert_any_await("job-123", JobStatus.EMBEDDING.value)
    mock_db.store_embeddings.assert_awaited_once()
