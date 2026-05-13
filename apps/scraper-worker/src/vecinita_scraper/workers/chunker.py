"""Modal worker for semantic chunking."""

from __future__ import annotations

from typing import Any

from vecinita_scraper.app import (
    APP_SECRETS,
    app,
    chunk_jobs_queue,
    embed_jobs_queue,
    spawn_deployed_worker_map,
)
from vecinita_scraper.chunkers.semantic_chunker import SemanticChunker
from vecinita_scraper.core.config import get_config
from vecinita_scraper.core.db import get_db
from vecinita_scraper.core.errors import ChunkingError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import (
    ChunkingConfig,
    ChunkJobQueueData,
    EmbedJobQueueData,
    JobStatus,
)
from vecinita_scraper.workers.job_failure import report_worker_job_failure

logger = get_logger(__name__)


async def run_chunking_job(
    job_data: ChunkJobQueueData,
    db: Any | None = None,
    embed_queue: Any | None = None,
) -> dict[str, Any]:
    """Chunk processed markdown and enqueue chunk batches for embedding."""
    database = db or get_db()
    queue = embed_queue or embed_jobs_queue

    await database.update_job_status(job_data.job_id, JobStatus.CHUNKING.value)

    if job_data.chunking_config is None:
        default_config = get_config().chunking
        chunking_config = ChunkingConfig(
            min_size_tokens=default_config.min_size_tokens,
            max_size_tokens=default_config.max_size_tokens,
            overlap_ratio=default_config.overlap_ratio,
        )
    else:
        chunking_config = job_data.chunking_config
    chunker = SemanticChunker()
    chunks = chunker.chunk(job_data.markdown_content, chunking_config)
    chunk_ids = await database.store_chunks(job_data.processed_doc_id, chunks)

    if len(chunk_ids) != len(chunks):
        raise ChunkingError("Stored chunk count does not match generated chunk count")

    batch_size = 100
    queued_batches = 0
    for start in range(0, len(chunks), batch_size):
        chunk_batch = chunks[start : start + batch_size]
        chunk_id_batch = chunk_ids[start : start + batch_size]
        payload = EmbedJobQueueData(
            job_id=job_data.job_id,
            chunk_ids=chunk_id_batch,
            chunk_texts=[chunk["text"] for chunk in chunk_batch],
        )
        await queue.put.aio(payload.model_dump(mode="json"))
        queued_batches += 1

    logger.info(
        "Queued chunk batches for embedding",
        job_id=job_data.job_id,
        chunk_count=len(chunks),
        batch_count=queued_batches,
    )
    return {
        "job_id": job_data.job_id,
        "chunk_count": len(chunks),
        "batch_count": queued_batches,
        "next_status": JobStatus.EMBEDDING.value,
    }


@app.function(timeout=900, retries=2, max_containers=5, secrets=APP_SECRETS)
async def chunker_worker(job_payload: dict[str, Any]) -> dict[str, Any]:
    """Modal entrypoint for chunking a processed document."""
    job_data = ChunkJobQueueData.model_validate(job_payload)

    try:
        result = await run_chunking_job(job_data)
    except Exception as exc:
        await report_worker_job_failure(job_data.job_id, exc)
        logger.exception("Chunking job failed", job_id=job_data.job_id)
        raise ChunkingError(str(exc)) from exc

    logger.info("Chunking job completed", **result)
    return result


@app.function(timeout=120, max_containers=2, secrets=APP_SECRETS)
async def drain_chunk_queue(batch_size: int = 10) -> dict[str, int]:
    """Pull pending chunking jobs from the queue and fan them out to workers."""
    payloads: list[dict[str, Any]] = []
    for _ in range(batch_size):
        item = await chunk_jobs_queue.get.aio(block=False)
        if item is None:
            break
        payloads.append(item)

    await spawn_deployed_worker_map("chunker_worker", payloads)
    dispatched = len(payloads)

    logger.info("Dispatched chunking jobs from queue", dispatched=dispatched)
    return {"dispatched": dispatched}
