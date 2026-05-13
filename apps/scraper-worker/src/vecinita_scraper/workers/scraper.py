"""Modal worker for site crawling with Crawl4AI."""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

from vecinita_scraper.app import (
    APP_SECRETS,
    app,
    process_jobs_queue,
    scrape_jobs_queue,
    spawn_deployed_worker_map,
)
from vecinita_scraper.core.db import get_db
from vecinita_scraper.core.errors import CrawlingError, ValidationError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.core.models import (
    CrawlConfig,
    JobStatus,
    ScrapeJobQueueData,
)
from vecinita_scraper.core.outcome_kinds import FailureCategory, ResponseKind
from vecinita_scraper.crawlers.classification import SUBSTANTIVE_MIN_CHARS
from vecinita_scraper.crawlers.crawl4ai_adapter import Crawl4AIAdapter, CrawledPage
from vecinita_scraper.crawlers.document_fetcher import RoutedDocument, try_direct_document_fetch
from vecinita_scraper.crawlers.outcome_codec import merge_legacy_and_outcome
from vecinita_scraper.workers.ingestion_pipeline import enqueue_page_for_document_pipeline
from vecinita_scraper.workers.job_failure import report_worker_job_failure

logger = get_logger(__name__)


def _hash_content(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()


def crawled_page_from_routed(url: str, routed: RoutedDocument) -> CrawledPage:
    """Normalize direct-fetch RoutedDocument into CrawledPage."""
    text = routed.text.strip()
    substantive = len(text) >= SUBSTANTIVE_MIN_CHARS
    success = bool(routed.success and substantive and routed.failure_category is None)
    failure_category = routed.failure_category
    operator_summary = routed.operator_summary
    err_msg: str | None = None
    if not success:
        if routed.success and not substantive:
            failure_category = (
                FailureCategory.PDF_EMPTY_NON_EXTRACTIVE
                if routed.response_kind == ResponseKind.PDF
                else FailureCategory.TEXT_EMPTY
            )
            operator_summary = (
                "Fetched document text is shorter than the substantive threshold "
                f"({SUBSTANTIVE_MIN_CHARS} characters)."
            )
            err_msg = operator_summary
        else:
            err_msg = routed.operator_summary or "Direct fetch did not yield usable content."

    return CrawledPage(
        url=url,
        markdown=text if routed.response_kind != ResponseKind.PDF else text,
        html="",
        cleaned_html="",
        extracted_content=None,
        links=[],
        media=[],
        metadata={
            "has_markdown": bool(text),
            "link_count": 0,
            "media_count": 0,
            "direct_fetch": True,
        },
        content_hash=_hash_content(text or err_msg or url),
        status_code=routed.status_code,
        success=success,
        error_message=err_msg,
        response_kind=routed.response_kind,
        failure_category=failure_category,
        operator_summary=operator_summary,
    )


async def _maybe_direct_fetch_pages(
    url: str, crawl_config: CrawlConfig
) -> list[CrawledPage] | None:
    """Return pages when URL is handled as PDF/plain text; None to use Crawl4AI."""
    routed = await try_direct_document_fetch(url, crawl_config)
    if routed is None:
        return None
    return [crawled_page_from_routed(url, routed)]


def _persist_error_message(page: CrawledPage) -> str | None:
    if page.success:
        return page.error_message
    if page.failure_category is not None:
        return merge_legacy_and_outcome(
            page.error_message,
            failure_category=page.failure_category,
            response_kind=page.response_kind,
            operator_summary=page.operator_summary,
        )
    return page.error_message


def build_zero_success_aggregate_message(pages: list[CrawledPage], max_items: int = 10) -> str:
    """Structured job-level summary when no page succeeded (contract 011)."""
    rows: list[dict[str, str]] = []
    for p in pages[:max_items]:
        rows.append(
            {
                "url": p.url,
                "failure_category": str(p.failure_category or "unknown"),
                "operator_summary": (p.operator_summary or p.error_message or "")[:2000],
            }
        )
    payload: dict[str, Any] = {
        "outcome_schema_version": 1,
        "aggregate": "no_successful_pages",
        "urls": rows,
    }
    if len(pages) > max_items:
        payload["truncated_remaining"] = len(pages) - max_items
    return json.dumps(payload, ensure_ascii=False)


async def run_scrape_job(
    job_data: ScrapeJobQueueData,
    db: Any | None = None,
    process_queue: Any | None = None,
) -> dict[str, Any]:
    """Execute a scrape job and enqueue extracted content for processing."""
    database = db or get_db()
    queue = process_queue or process_jobs_queue

    if not job_data.url:
        raise ValidationError("Scrape job is missing a URL")

    await database.update_job_status(job_data.job_id, JobStatus.VALIDATING.value)
    await database.update_job_status(job_data.job_id, JobStatus.CRAWLING.value)

    pages: list[CrawledPage]
    direct = await _maybe_direct_fetch_pages(str(job_data.url), job_data.crawl_config)
    if direct is not None:
        pages = direct
    else:
        adapter = Crawl4AIAdapter(job_data.crawl_config)
        pages = await adapter.crawl_site(str(job_data.url))

    if not pages:
        raise CrawlingError(f"No pages were crawled for {job_data.url}")

    await database.update_job_status(job_data.job_id, JobStatus.EXTRACTING.value)

    processed_count = 0
    failed_count = 0

    for page in pages:
        raw_for_store = page.markdown or page.cleaned_html or page.html
        persist_err = _persist_error_message(page)
        crawled_url_id = await database.store_crawled_url(
            job_id=job_data.job_id,
            url=page.url,
            raw_content=raw_for_store,
            content_hash=page.content_hash,
            status="success" if page.success else "failed",
            error_message=persist_err,
            response_kind=str(page.response_kind) if page.response_kind else None,
            failure_category=str(page.failure_category) if page.failure_category else None,
            operator_summary=page.operator_summary,
        )

        if not page.success:
            # FR-009: failed pages (including policy-blocked) never enter chunk / LLM / embed paths.
            failed_count += 1
            continue

        raw_content = page.markdown or page.cleaned_html or page.html
        await enqueue_page_for_document_pipeline(
            job_data=job_data,
            page=page,
            crawled_url_id=crawled_url_id,
            raw_content=raw_content,
            database=database,
            process_queue=queue,
        )
        processed_count += 1

    if processed_count == 0:
        aggregate = build_zero_success_aggregate_message(pages)
        await database.update_job_status(
            job_data.job_id,
            JobStatus.FAILED.value,
            error_message=aggregate,
        )
        raise CrawlingError(f"Job {job_data.job_id} produced no successful pages")

    return {
        "job_id": job_data.job_id,
        "pages_crawled": len(pages),
        "pages_queued": processed_count,
        "pages_failed": failed_count,
        "next_status": JobStatus.PROCESSING.value,
    }


@app.function(timeout=900, retries=2, max_containers=10, secrets=APP_SECRETS)
async def scraper_worker(job_payload: dict[str, Any]) -> dict[str, Any]:
    """Modal entrypoint for processing a single scrape job."""
    job_data = ScrapeJobQueueData.model_validate(job_payload)

    try:
        result = await run_scrape_job(job_data)
    except Exception as exc:
        await report_worker_job_failure(job_data.job_id, exc)
        logger.exception("Scrape job failed", job_id=job_data.job_id, url=job_data.url)
        raise

    db = get_db()
    await db.update_job_status(job_data.job_id, JobStatus.PROCESSING.value)
    logger.info("Scrape job completed", **result)
    return result


@app.function(timeout=120, max_containers=2, secrets=APP_SECRETS)
async def drain_scrape_queue(batch_size: int = 10) -> dict[str, int]:
    """Pull pending scrape jobs from the queue and fan them out to workers."""
    payloads: list[dict[str, Any]] = []
    for _ in range(batch_size):
        item = await scrape_jobs_queue.get.aio(block=False)
        if item is None:
            break
        payloads.append(item)

    await spawn_deployed_worker_map("scraper_worker", payloads)
    dispatched = len(payloads)

    logger.info("Dispatched scrape jobs from queue", dispatched=dispatched)
    return {"dispatched": dispatched}
