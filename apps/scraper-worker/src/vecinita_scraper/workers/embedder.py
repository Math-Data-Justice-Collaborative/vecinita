"""Modal worker for embedding chunk batches."""

from __future__ import annotations

import json
from typing import Any

from vecinita_scraper.app import (
    APP_SECRETS,
    app,
    embed_jobs_queue,
    modal,
    spawn_deployed_worker_map,
    store_jobs_queue,
)
from vecinita_scraper.clients.embedding_client import EmbeddingClient
from vecinita_scraper.core.db import get_db
from vecinita_scraper.core.errors import EmbeddingError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import EmbedJobQueueData, JobStatus, StoreJobQueueData
from vecinita_scraper.workers.pipeline_errors import (
    ERROR_CATEGORY_EMBEDDING,
    ERROR_CATEGORY_EMBEDDING_PARTIAL,
)

logger = get_logger(__name__)


async def run_embedding_job(
    job_data: EmbedJobQueueData,
    db: Any | None = None,
    store_queue: Any | None = None,
    embedding_client: EmbeddingClient | None = None,
) -> dict[str, Any]:
    """Embed chunk texts, persist vectors, and enqueue finalization."""
    database = db or get_db()
    queue = store_queue or store_jobs_queue
    client = embedding_client or EmbeddingClient()

    await database.update_job_status(job_data.job_id, JobStatus.EMBEDDING.value)
    response = await client.batch_embed(job_data.chunk_texts)
    embeddings = response["embeddings"]

    if len(embeddings) != len(job_data.chunk_ids):
        raise EmbeddingError("Embedding count does not match chunk count")

    records = []
    for chunk_id, embedding in zip(job_data.chunk_ids, embeddings, strict=True):
        records.append(
            {
                "chunk_id": chunk_id,
                "embedding": embedding,
                "model_name": response["model"],
                "dimensions": response["dimensions"],
            }
        )

    await database.store_embeddings(job_data.job_id, records)
    payload = StoreJobQueueData(job_id=job_data.job_id, embedding_ids=job_data.chunk_ids)
    await queue.put.aio(payload.model_dump(mode="json"))

    logger.info(
        "Queued embedding batch for finalization",
        job_id=job_data.job_id,
        embedding_count=len(records),
    )
    return {
        "job_id": job_data.job_id,
        "embedding_count": len(records),
        "next_status": JobStatus.STORING.value,
    }


@app.function(timeout=900, retries=2, max_containers=3, secrets=APP_SECRETS)
@modal.batched(max_batch_size=100, wait_ms=500)
async def embedder_worker(job_payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Modal entrypoint for embedding one or more queued chunk batches."""
    results: list[dict[str, Any]] = []
    client = EmbeddingClient()
    # One get_db() per batch; ConfigError surfaces here if misconfigured.
    db = get_db()

    for payload in job_payloads:
        job_data = EmbedJobQueueData.model_validate(payload)
        try:
            result = await run_embedding_job(job_data, db=db, embedding_client=client)
        except Exception as exc:
            cat = (
                ERROR_CATEGORY_EMBEDDING_PARTIAL
                if job_data.chunk_ids
                else ERROR_CATEGORY_EMBEDDING
            )
            msg = str(exc)
            if job_data.chunk_ids:
                msg = json.dumps(
                    {
                        "message": msg,
                        "partial_completion": True,
                        "requires_reprocess": True,
                    },
                    ensure_ascii=False,
                )
            await db.update_job_status(
                job_data.job_id,
                JobStatus.FAILED.value,
                error_message=msg,
                pipeline_stage="failed",
                error_category=cat,
            )
            logger.exception("Embedding job failed", job_id=job_data.job_id)
            raise EmbeddingError(str(exc)) from exc
        results.append(result)

    return results


@app.function(timeout=120, max_containers=2, secrets=APP_SECRETS)
async def drain_embed_queue(batch_size: int = 10) -> dict[str, int]:
    """Pull pending embed jobs from the queue and fan them out to workers."""
    payloads: list[dict[str, Any]] = []
    for _ in range(batch_size):
        item = await embed_jobs_queue.get.aio(block=False)
        if item is None:
            break
        payloads.append(item)

    await spawn_deployed_worker_map("embedder_worker", payloads)
    dispatched = len(payloads)

    logger.info("Dispatched embedding jobs from queue", dispatched=dispatched)
    return {"dispatched": dispatched}
