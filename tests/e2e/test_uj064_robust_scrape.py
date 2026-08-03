"""UJ-064 / TC-199: single-URL robust scrape via POST /jobs → runner → GET /jobs (F59)."""

from __future__ import annotations

import contextlib
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.pipeline import fetch_html_fixture, run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.internal_write import BatchUpsertRequest, BatchUpsertResponse
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_object_list, json_str, response_json_object

if TYPE_CHECKING:
    from uuid import UUID

pytestmark = pytest.mark.e2e

_BOILERPLATE_HTML = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "ingest" / "boilerplate.html"
).read_text(encoding="utf-8")
_PROXY_KEY = "test-proxy-key"
_URL = "https://example.com/community-center"
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION


class _RecordingWriteClient:
    """Write client that records the last batch upsert."""

    def __init__(self) -> None:
        self.last_batch: BatchUpsertRequest | None = None

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        """Upsert batch and retain payload for assertions."""
        self.last_batch = body
        chunks = sum(len(doc.chunks) for doc in body.documents)
        return BatchUpsertResponse(upserted_chunks=chunks)

    def close(self) -> None:
        """Close."""
        return


class _StubEmbedClient:
    """Deterministic embed stub for ingest e2e."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return fixed-dimension vectors."""
        return [_EMBED_VECTOR for _ in texts]

    def close(self) -> None:
        """Close."""
        return


def _build_client(
    *,
    store: InMemoryJobStore,
    write_client: _RecordingWriteClient,
) -> TestClient:
    def runner(job_id: UUID) -> None:
        with contextlib.suppress(Exception):
            run_ingest_job(
                job_id,
                store=store,
                embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
                write_client=write_client,  # type: ignore[arg-type]
                fetch_document=lambda url: fetch_html_fixture(
                    url,
                    fixture_html=_BOILERPLATE_HTML,
                ),
            )

    app = create_app(store=store, require_proxy_auth=True, pipeline_runner=runner)
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client


def test_uj064_single_url_robust_scrape_strips_boilerplate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-199 / AC-SC1: crawl=false job completes; stored text lacks nav/footer chrome."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    client = _build_client(store=store, write_client=write_client)

    create = client.post(
        "/jobs",
        json={
            "urls": [_URL],
            "options": {"chunk_size_tokens": 64, "crawl": False},
        },
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    body = response_json_object(client.get(f"/jobs/{job_id}"))
    assert json_str(body, "status") == "completed"
    assert body["urls"] == [_URL]

    assert write_client.last_batch is not None
    assert len(write_client.last_batch.documents) == 1
    doc = write_client.last_batch.documents[0]
    assert str(doc.url).rstrip("/") == _URL
    assert doc.title == "Community center hours"
    assert doc.language is not None
    assert doc.content_hash is not None
    assert doc.chunks
    text = doc.body_text or ""
    assert "Community center hours" in text
    assert "eastside community center" in text
    assert "Monday to Friday" in text
    assert "Youth tutoring" in text
    assert "NAV_BOILERPLATE_MARKER" not in text
    assert "FOOTER_BOILERPLATE_MARKER" not in text
    assert "SIDEBAR_PROMO_MARKER" not in text

    metrics = as_json_object(body["metrics"]) if body.get("metrics") is not None else {}
    assert metrics.get("urls_failed_embed", 0) == 0

    listed = response_json_object(client.get("/jobs"))
    job_ids = {json_str(job, "job_id") for job in json_object_list(listed, "jobs")}
    assert job_id in job_ids
