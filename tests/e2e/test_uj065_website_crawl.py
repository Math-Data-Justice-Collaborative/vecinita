"""UJ-065 / TC-202: crawl job soft-fail + GET /jobs/{id}/tree (F60)."""

from __future__ import annotations

import contextlib
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.pipeline import run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_ingest.crawl import normalize_url
from vecinita_ingest.scrape import parse_html
from vecinita_shared_schemas.internal_write import BatchUpsertRequest, BatchUpsertResponse
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_int, json_list, json_str, response_json_object

if TYPE_CHECKING:
    from uuid import UUID

    from vecinita_ingest.models import ScrapedDocument

pytestmark = pytest.mark.e2e

_PROXY_KEY = "test-proxy-key"
_SEED = "https://crawl.example.com/docs/"
_SEED_NORM = normalize_url(_SEED)
_PAGE_A = "https://crawl.example.com/docs/a"
_PAGE_B = "https://crawl.example.com/docs/b"
_PAGE_FAIL = "https://crawl.example.com/docs/fail"
_MIN_PAGES_FETCHED = 2
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION

_HTML_BY_URL: dict[str, str] = {
    _SEED_NORM: """
    <html><body>
      <h1>Docs index</h1>
      <a href="/docs/a">A</a>
      <a href="/docs/b">B</a>
      <a href="/docs/fail">Fail</a>
      <a href="https://other.example/out">Out</a>
    </body></html>
    """,
    _PAGE_A: "<html><body><h1>Page A</h1><p>Alpha content for crawl.</p></body></html>",
    _PAGE_B: "<html><body><h1>Page B</h1><p>Bravo content for crawl.</p></body></html>",
}


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


def _fetch_html(url: str) -> str:
    key = normalize_url(url)
    if key not in _HTML_BY_URL:
        msg = f"missing fixture html for {url}"
        raise KeyError(msg)
    return _HTML_BY_URL[key]


def _fetch_document(url: str) -> ScrapedDocument:
    if normalize_url(url) == normalize_url(_PAGE_FAIL):
        msg = "simulated page fetch failure"
        raise RuntimeError(msg)
    return parse_html(_fetch_html(url), url=url)


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
                fetch_document=_fetch_document,
                fetch_html=_fetch_html,
            )

    app = create_app(store=store, require_proxy_auth=True, pipeline_runner=runner)
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client


def test_uj065_crawl_job_soft_fail_and_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-202 / AC-SC6: crawl completes with pages_failed≥1; tree roots non-empty."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    client = _build_client(store=store, write_client=write_client)

    create = client.post(
        "/jobs",
        json={
            "urls": [_SEED],
            "options": {
                "chunk_size_tokens": 64,
                "crawl": True,
                "max_depth": 2,
                "max_pages": 25,
                "crawl_scope": "same_domain",
            },
        },
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    body = response_json_object(client.get(f"/jobs/{job_id}"))
    assert json_str(body, "status") == "completed"
    metrics = as_json_object(body["metrics"])
    assert json_int(metrics, "pages_fetched") >= _MIN_PAGES_FETCHED
    assert json_int(metrics, "pages_failed") >= 1
    assert metrics.get("crawl_stopped_reason") in {"complete", "max_depth", "max_pages"}

    assert write_client.last_batch is not None
    stored_urls = {str(doc.url).rstrip("/") for doc in write_client.last_batch.documents}
    assert _PAGE_A in stored_urls or f"{_PAGE_A}/" in {
        str(doc.url) for doc in write_client.last_batch.documents
    }
    assert _PAGE_FAIL not in stored_urls
    assert all(doc.source_domain for doc in write_client.last_batch.documents)

    tree = response_json_object(client.get(f"/jobs/{job_id}/tree"))
    roots = json_list(tree, "roots")
    assert roots
    domains = {json_str(as_json_object(root), "label") for root in roots}
    assert "crawl.example.com" in domains


def test_uj065_crawl_false_preserves_single_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-SC7 / UJ-065: crawl=false still ingests only the provided URL."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()
    client = _build_client(store=store, write_client=write_client)

    create = client.post(
        "/jobs",
        json={
            "urls": [_PAGE_A],
            "options": {"chunk_size_tokens": 64, "crawl": False},
        },
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    body = response_json_object(client.get(f"/jobs/{job_id}"))
    assert json_str(body, "status") == "completed"
    assert body["urls"] == [_PAGE_A]
    assert write_client.last_batch is not None
    assert len(write_client.last_batch.documents) == 1
