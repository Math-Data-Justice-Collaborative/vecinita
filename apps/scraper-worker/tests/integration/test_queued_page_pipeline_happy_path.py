"""Queued page pipeline ordering with gateway + Modal boundaries mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = [pytest.mark.integration]


@pytest.mark.asyncio
async def test_happy_path_persists_via_gateway_sequence() -> None:
    """Worker-side persistence posts status → chunks → embeddings in order (contract sketch)."""
    from vecinita_scraper.persistence.gateway_http import GatewayHttpPipelinePersistence

    calls: list[tuple[str, str, dict | None]] = []

    async def fake_request(
        self: GatewayHttpPipelinePersistence,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        extra_headers: dict[str, str] | None = None,
    ):
        calls.append((method, path, json))
        r = MagicMock()
        r.text = ""
        if "/jobs/" in path and path.endswith("/status"):
            r.status_code = 204
        elif "/crawled-urls" in path:
            r.status_code = 200
            r.json = lambda: {"crawled_url_id": "cu-1"}
        elif "/extracted-content" in path:
            r.status_code = 200
            r.json = lambda: {"extracted_content_id": "ec-1"}
        elif "/processed-documents" in path:
            r.status_code = 200
            r.json = lambda: {"processed_doc_id": "pd-1"}
        elif "/chunks" in path:
            r.status_code = 200
            r.json = lambda: {"chunk_ids": ["chunk-1"]}
        elif "/embeddings" in path:
            r.status_code = 204
        else:
            r.status_code = 200
            r.json = lambda: {}
        return r

    with patch.object(GatewayHttpPipelinePersistence, "_request", new=fake_request):
        g = GatewayHttpPipelinePersistence("https://gw.example", "tok")
        await g.update_job_status(
            "job-1",
            "chunking",
            pipeline_stage="chunking",
            request_id="rid-1",
        )
        await g.store_crawled_url(
            "job-1",
            "https://example.com/p",
            "raw",
            "a" * 64,
        )
        await g.store_extracted_content("cu-1", "text/html", "body")
        await g.store_processed_document("ec-1", "# md")
        await g.store_chunks(
            "pd-1",
            [{"text": "t", "raw_text": "t", "position": 0}],
        )
        await g.store_embeddings(
            "job-1",
            [{"chunk_id": "chunk-1", "embedding": [0.0] * 384}],
        )

    paths = [c[1] for c in calls]
    assert paths[0].endswith("/jobs/job-1/status")
    assert any(p.endswith("/crawled-urls") for p in paths)
    assert any(p.endswith("/chunks") for p in paths)
    assert paths[-1].endswith("/embeddings")
