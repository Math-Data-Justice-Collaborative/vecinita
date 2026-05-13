"""Modal worker for document processing with Docling."""

from __future__ import annotations

from typing import Any

from vecinita_scraper.app import (
    APP_SECRETS,
    app,
    chunk_jobs_queue,
    process_jobs_queue,
    spawn_deployed_worker_map,
)
from vecinita_scraper.core.db import get_db
from vecinita_scraper.core.errors import ProcessingError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import ChunkJobQueueData, JobStatus, ProcessJobQueueData
from vecinita_scraper.processors.docling_processor import DoclingProcessor
from vecinita_scraper.workers.job_failure import report_worker_job_failure

logger = get_logger(__name__)


async def run_processing_job(
    job_data: ProcessJobQueueData,
    db: Any | None = None,
    chunk_queue: Any | None = None,
) -> dict[str, Any]:
    """Process extracted content and enqueue it for chunking."""
    database = db or get_db()
    queue = chunk_queue or chunk_jobs_queue

    await database.update_job_status(job_data.job_id, JobStatus.PROCESSING.value)

    processor = DoclingProcessor()
    processed_document = processor.process_content(
        raw_content=job_data.raw_content,
        content_type=job_data.content_type,
    )
    processed_doc_id = await database.store_processed_document(
        extracted_content_id=job_data.extracted_content_id,
        markdown_content=processed_document.markdown_content,
        tables_json=processed_document.tables_json,
        metadata_json=processed_document.metadata_json,
    )

    chunk_payload = ChunkJobQueueData(
        job_id=job_data.job_id,
        processed_doc_id=processed_doc_id,
        markdown_content=processed_document.markdown_content,
        chunking_config=None,
    )
    await queue.put.aio(chunk_payload.model_dump(mode="json"))

    logger.info(
        "Queued processed document for chunking",
        job_id=job_data.job_id,
        processed_doc_id=processed_doc_id,
    )
    return {
        "job_id": job_data.job_id,
        "processed_doc_id": processed_doc_id,
        "next_status": JobStatus.CHUNKING.value,
    }


@app.function(timeout=900, retries=2, max_containers=5, secrets=APP_SECRETS)
async def processor_worker(job_payload: dict[str, Any]) -> dict[str, Any]:
    """Modal entrypoint for processing a single extracted document."""
    job_data = ProcessJobQueueData.model_validate(job_payload)

    try:
        result = await run_processing_job(job_data)
    except Exception as exc:
        await report_worker_job_failure(job_data.job_id, exc)
        logger.exception("Processing job failed", job_id=job_data.job_id)
        raise ProcessingError(str(exc)) from exc

    logger.info("Processing job completed", **result)
    return result


@app.function(timeout=120, max_containers=2, secrets=APP_SECRETS)
async def drain_process_queue(batch_size: int = 10) -> dict[str, int]:
    """Pull pending processing jobs from the queue and fan them out to workers."""
    payloads: list[dict[str, Any]] = []
    for _ in range(batch_size):
        item = await process_jobs_queue.get.aio(block=False)
        if item is None:
            break
        payloads.append(item)

    await spawn_deployed_worker_map("processor_worker", payloads)
    dispatched = len(payloads)

    logger.info("Dispatched processing jobs from queue", dispatched=dispatched)
    return {"dispatched": dispatched}
