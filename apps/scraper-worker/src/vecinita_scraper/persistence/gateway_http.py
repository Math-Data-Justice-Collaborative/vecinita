"""HTTP client for pipeline persistence via Render gateway internal endpoints."""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from vecinita_scraper.core.errors import DatabaseError
from vecinita_scraper.core.logger import get_logger
from vecinita_scraper.workers.pipeline_retry import (
    gateway_retry_policy_from_env,
    is_transient_http_status,
    max_gateway_http_retries,
    sleep_before_retry_seconds,
)

logger = get_logger(__name__)

_PIPELINE_PREFIX = "/api/v1/internal/scraper-pipeline"
_HEADER = "X-Scraper-Pipeline-Ingest-Token"


def _timeout_seconds() -> float:
    raw = str(os.getenv("SCRAPER_GATEWAY_HTTP_TIMEOUT_SECONDS", "300")).strip()
    try:
        return max(30.0, float(raw))
    except ValueError:
        return 300.0


class GatewayHttpPipelinePersistence:
    """Async persistence that POSTs to the gateway instead of opening Postgres on Modal."""

    def __init__(self, base_url: str, token: str) -> None:
        self._base = base_url.rstrip("/")
        self._headers = {_HEADER: token.strip()}

    def _url(self, path: str) -> str:
        return f"{self._base}{_PIPELINE_PREFIX}{path}"

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        headers = {**self._headers, **(extra_headers or {})}
        retry_kw = gateway_retry_policy_from_env()
        max_tries = max_gateway_http_retries()
        for attempt in range(max_tries):
            try:
                async with httpx.AsyncClient(timeout=_timeout_seconds()) as client:
                    r = await client.request(method, self._url(path), json=json, headers=headers)
            except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
                if attempt + 1 >= max_tries:
                    logger.exception("Gateway pipeline HTTP error", path=path)
                    raise DatabaseError(f"Gateway pipeline HTTP error: {exc}") from exc
                delay = sleep_before_retry_seconds(attempt + 1, **retry_kw)
                await asyncio.sleep(delay)
                continue
            except httpx.HTTPError as exc:
                logger.exception("Gateway pipeline HTTP error", path=path)
                raise DatabaseError(f"Gateway pipeline HTTP error: {exc}") from exc

            if r.status_code >= 400 and is_transient_http_status(r.status_code):
                if attempt + 1 >= max_tries:
                    detail = (r.text or "")[:2000]
                    raise DatabaseError(
                        f"Gateway pipeline error {r.status_code} for {path}: {detail}"
                    )
                delay = sleep_before_retry_seconds(attempt + 1, **retry_kw)
                await asyncio.sleep(delay)
                continue

            if r.status_code >= 400:
                detail = (r.text or "")[:2000]
                raise DatabaseError(
                    f"Gateway pipeline error {r.status_code} for {path}: {detail}"
                )
            return r

        raise RuntimeError("unexpected fallthrough in _request")  # pragma: no cover

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        error_message: str | None = None,
        *,
        pipeline_stage: str | None = None,
        error_category: str | None = None,
        request_id: str | None = None,
    ) -> None:
        body: dict[str, Any] = {"status": status, "error_message": error_message}
        if pipeline_stage is not None:
            body["pipeline_stage"] = pipeline_stage
        if error_category is not None:
            body["error_category"] = error_category
        extra: dict[str, str] = {}
        if request_id and str(request_id).strip():
            extra["X-Request-Id"] = str(request_id).strip()
        await self._request(
            "POST",
            f"/jobs/{job_id}/status",
            json=body,
            extra_headers=extra or None,
        )

    async def store_crawled_url(
        self,
        job_id: str,
        url: str,
        raw_content: str,
        content_hash: str,
        status: str = "success",
        error_message: str | None = None,
        *,
        response_kind: str | None = None,
        failure_category: str | None = None,
        operator_summary: str | None = None,
    ) -> str:
        body: dict[str, Any] = {
            "job_id": job_id,
            "url": url,
            "raw_content": raw_content,
            "content_hash": content_hash,
            "status": status,
            "error_message": error_message,
        }
        if response_kind is not None:
            body["response_kind"] = response_kind
        if failure_category is not None:
            body["failure_category"] = failure_category
        if operator_summary is not None:
            body["operator_summary"] = operator_summary
        r = await self._request(
            "POST",
            "/crawled-urls",
            json=body,
        )
        data = r.json()
        cid = data.get("crawled_url_id")
        if not cid:
            raise DatabaseError("Gateway did not return crawled_url_id")
        return str(cid)

    async def store_extracted_content(
        self,
        crawled_url_id: str,
        content_type: str,
        raw_content: str,
    ) -> str:
        r = await self._request(
            "POST",
            "/extracted-content",
            json={
                "crawled_url_id": crawled_url_id,
                "content_type": content_type,
                "raw_content": raw_content,
            },
        )
        data = r.json()
        eid = data.get("extracted_content_id")
        if not eid:
            raise DatabaseError("Gateway did not return extracted_content_id")
        return str(eid)

    async def store_processed_document(
        self,
        extracted_content_id: str,
        markdown_content: str,
        tables_json: str | None = None,
        metadata_json: str | None = None,
    ) -> str:
        r = await self._request(
            "POST",
            "/processed-documents",
            json={
                "extracted_content_id": extracted_content_id,
                "markdown_content": markdown_content,
                "tables_json": tables_json,
                "metadata_json": metadata_json,
            },
        )
        data = r.json()
        pid = data.get("processed_doc_id")
        if not pid:
            raise DatabaseError("Gateway did not return processed_doc_id")
        return str(pid)

    async def store_chunks(self, processed_doc_id: str, chunks: list[dict[str, Any]]) -> list[str]:
        r = await self._request(
            "POST",
            "/chunks",
            json={"processed_doc_id": processed_doc_id, "chunks": chunks},
        )
        data = r.json()
        ids = data.get("chunk_ids")
        if not isinstance(ids, list):
            raise DatabaseError("Gateway did not return chunk_ids")
        return [str(x) for x in ids]

    async def store_embeddings(self, job_id: str, chunk_embeddings: list[dict[str, Any]]) -> None:
        await self._request(
            "POST",
            "/embeddings",
            json={"job_id": job_id, "chunk_embeddings": chunk_embeddings},
        )
