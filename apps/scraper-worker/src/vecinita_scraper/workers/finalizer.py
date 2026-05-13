"""Modal worker for finalizing completed embedding jobs."""

from __future__ import annotations

from typing import Any

from vecinita_scraper.app import (
    APP_SECRETS,
    app,
    spawn_deployed_worker_map,
    store_jobs_queue,
)
from vecinita_scraper.core.db import get_db
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import JobStatus, StoreJobQueueData

logger = get_logger(__name__)


async def run_finalization_job(
    job_data: StoreJobQueueData,
    db: Any | None = None,
) -> dict[str, Any]:
    """Mark a job as completed after embeddings have been persisted."""
    database = db or get_db()
    await database.update_job_status(job_data.job_id, JobStatus.STORING.value)
    await database.update_job_status(job_data.job_id, JobStatus.COMPLETED.value)

    logger.info(
        "Finalized scraping job",
        job_id=job_data.job_id,
        embedding_count=len(job_data.embedding_ids),
    )
    return {
        "job_id": job_data.job_id,
        "embedding_count": len(job_data.embedding_ids),
        "final_status": JobStatus.COMPLETED.value,
    }


@app.function(timeout=300, retries=1, max_containers=2, secrets=APP_SECRETS)
async def finalizer_worker(job_payload: dict[str, Any]) -> dict[str, Any]:
    """Modal entrypoint for finalizing a single job."""
    job_data = StoreJobQueueData.model_validate(job_payload)
    return await run_finalization_job(job_data)


@app.function(timeout=120, max_containers=2, secrets=APP_SECRETS)
async def drain_store_queue(batch_size: int = 10) -> dict[str, int]:
    """Pull pending finalization jobs from the queue and fan them out to workers."""
    payloads: list[dict[str, Any]] = []
    for _ in range(batch_size):
        item = await store_jobs_queue.get.aio(block=False)
        if item is None:
            break
        payloads.append(item)

    await spawn_deployed_worker_map("finalizer_worker", payloads)
    dispatched = len(payloads)

    logger.info("Dispatched finalization jobs from queue", dispatched=dispatched)
    return {"dispatched": dispatched}
