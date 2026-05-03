"""Internal HTTP API: Modal scraper workers persist pipeline state via the Render gateway."""

from __future__ import annotations

import logging
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request, status
from pydantic import BaseModel, Field

from src.services.ingestion import modal_scraper_pipeline_persist as pipeline_persist
from src.utils.scraper_api_keys import scraper_api_key_segments

router = APIRouter(
    prefix="/internal/scraper-pipeline",
    tags=["Internal scraper pipeline"],
    include_in_schema=False,
)

logger = logging.getLogger(__name__)

_PIPELINE_TOKEN_HEADER = "X-Scraper-Pipeline-Ingest-Token"


def _allowed_pipeline_ingest_tokens() -> frozenset[str]:
    """Modal workers send one key; gateway accepts any segment from SCRAPER_API_KEYS."""
    return frozenset(scraper_api_key_segments(os.getenv("SCRAPER_API_KEYS")))


async def require_pipeline_ingest_token(
    x_scraper_pipeline_ingest_token: Annotated[str | None, Header()] = None,
) -> None:
    allowed = _allowed_pipeline_ingest_tokens()
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SCRAPER_API_KEYS is not configured on the gateway (required for pipeline ingest)",
        )
    got = (x_scraper_pipeline_ingest_token or "").strip()
    if not got or got not in allowed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing scraper pipeline ingest token",
        )


class UpdateJobStatusBody(BaseModel):
    status: str = Field(..., min_length=1)
    error_message: str | None = None
    pipeline_stage: str | None = Field(
        default=None,
        description="Normative pipeline stage; merged into ``scraping_jobs.metadata`` when set.",
    )
    error_category: str | None = Field(
        default=None,
        description="Short machine code merged into ``metadata``; may prefix ``error_message``.",
    )


@router.post(
    "/jobs/{job_id}/status",
    dependencies=[Depends(require_pipeline_ingest_token)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def ingest_update_job_status(
    job_id: Annotated[str, Path(min_length=1)],
    body: UpdateJobStatusBody,
    request: Request,
) -> None:
    try:
        pipeline_persist.update_job_status(
            job_id,
            body.status,
            body.error_message,
            pipeline_stage=body.pipeline_stage,
            error_category=body.error_category,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    cid = getattr(request.state, "correlation_id", None)
    xrid = (request.headers.get("X-Request-Id") or "").strip() or None
    logger.info(
        "scraper_pipeline_job_status_ingest job_id=%s correlation_id=%s x_request_id=%s "
        "pipeline_stage=%s error_category=%s",
        job_id,
        cid,
        xrid,
        body.pipeline_stage,
        body.error_category,
    )


class StoreCrawledUrlBody(BaseModel):
    job_id: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    raw_content: str = ""
    content_hash: str = Field(..., min_length=1)
    status: str = "success"
    error_message: str | None = None


class CrawledUrlCreated(BaseModel):
    crawled_url_id: str


@router.post(
    "/crawled-urls",
    response_model=CrawledUrlCreated,
    dependencies=[Depends(require_pipeline_ingest_token)],
)
async def ingest_store_crawled_url(body: StoreCrawledUrlBody) -> CrawledUrlCreated:
    try:
        cid = pipeline_persist.store_crawled_url(
            body.job_id,
            body.url,
            body.raw_content,
            body.content_hash,
            status=body.status,
            error_message=body.error_message,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return CrawledUrlCreated(crawled_url_id=cid)


class StoreExtractedContentBody(BaseModel):
    crawled_url_id: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    raw_content: str = Field(..., min_length=1)


class ExtractedContentCreated(BaseModel):
    extracted_content_id: str


@router.post(
    "/extracted-content",
    response_model=ExtractedContentCreated,
    dependencies=[Depends(require_pipeline_ingest_token)],
)
async def ingest_store_extracted_content(
    body: StoreExtractedContentBody,
) -> ExtractedContentCreated:
    try:
        eid = pipeline_persist.store_extracted_content(
            body.crawled_url_id,
            body.content_type,
            body.raw_content,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return ExtractedContentCreated(extracted_content_id=eid)


class StoreProcessedDocumentBody(BaseModel):
    extracted_content_id: str = Field(..., min_length=1)
    markdown_content: str = Field(..., min_length=1)
    tables_json: str | None = None
    metadata_json: str | None = None


class ProcessedDocumentCreated(BaseModel):
    processed_doc_id: str


@router.post(
    "/processed-documents",
    response_model=ProcessedDocumentCreated,
    dependencies=[Depends(require_pipeline_ingest_token)],
)
async def ingest_store_processed_document(
    body: StoreProcessedDocumentBody,
) -> ProcessedDocumentCreated:
    try:
        pid = pipeline_persist.store_processed_document(
            body.extracted_content_id,
            body.markdown_content,
            body.tables_json,
            body.metadata_json,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return ProcessedDocumentCreated(processed_doc_id=pid)


class StoreChunksBody(BaseModel):
    processed_doc_id: str = Field(..., min_length=1)
    chunks: list[dict[str, Any]] = Field(default_factory=list)


class ChunksCreated(BaseModel):
    chunk_ids: list[str]


@router.post(
    "/chunks",
    response_model=ChunksCreated,
    dependencies=[Depends(require_pipeline_ingest_token)],
)
async def ingest_store_chunks(body: StoreChunksBody) -> ChunksCreated:
    try:
        ids = pipeline_persist.store_chunks(body.processed_doc_id, body.chunks)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return ChunksCreated(chunk_ids=ids)


class StoreEmbeddingsBody(BaseModel):
    job_id: str = Field(..., min_length=1)
    chunk_embeddings: list[dict[str, Any]] = Field(default_factory=list)


@router.post(
    "/embeddings",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_pipeline_ingest_token)],
)
async def ingest_store_embeddings(body: StoreEmbeddingsBody) -> None:
    try:
        pipeline_persist.store_embeddings(body.job_id, body.chunk_embeddings)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
