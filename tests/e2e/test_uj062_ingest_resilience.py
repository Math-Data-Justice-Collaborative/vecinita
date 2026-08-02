"""UJ-062 / TC-187-190: ingest resilience via POST /jobs -> runner -> GET /jobs (F47-F48)."""

from __future__ import annotations

import contextlib
import json
from hashlib import sha256
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, cast

import httpx
import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.pipeline import fetch_html_fixture, run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION, EmbeddingClient
from vecinita_shared_schemas.internal_write import BatchUpsertRequest, BatchUpsertResponse
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import json_object_list, json_str, response_json_object

if TYPE_CHECKING:
    from uuid import UUID

pytestmark = pytest.mark.e2e

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_PROXY_KEY = "test-proxy-key"
_URL = "https://example.com/sample-page.html"
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION
_ZERO_EMBED_CALLS = 0
_TRANSIENT_FAILURES_BEFORE_OK = 2
_MIN_ATTEMPTS_AFTER_RETRY = 3


class _CountingEmbedClient:
    """Stub embed client that records batch call counts."""

    def __init__(self) -> None:
        self.batch_calls = 0

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch and increment call counter."""
        self.batch_calls += 1
        return [_EMBED_VECTOR for _ in texts]

    def close(self) -> None:
        """Close."""
        return


class _HashAwareWriteClient:
    """Write client that remembers content_hash for F47 skip lookups."""

    def __init__(self) -> None:
        self.last_batch: BatchUpsertRequest | None = None
        self._hashes: dict[str, str] = {}

    def seed_hash(self, url: str, content_hash: str) -> None:
        """Seed a prior ingest content_hash for skip tests."""
        self._hashes[url] = content_hash

    def get_content_hash_by_url(self, url: str) -> str | None:
        """Return stored content_hash when present."""
        return self._hashes.get(url)

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        """Upsert batch and cache hashes."""
        self.last_batch = body
        for doc in body.documents:
            digest = doc.content_hash
            if digest is not None:
                self._hashes[str(doc.url)] = digest
        chunks = sum(len(doc.chunks) for doc in body.documents)
        return BatchUpsertResponse(upserted_chunks=chunks)

    def close(self) -> None:
        """Close."""
        return


def _fixture_digest() -> str:
    scraped = fetch_html_fixture(_URL, fixture_html=_FIXTURE_HTML)
    return sha256(scraped.text.encode("utf-8")).hexdigest()


def _build_client(
    *,
    store: InMemoryJobStore,
    embed_client: object,
    write_client: object,
) -> TestClient:
    def runner(job_id: UUID) -> None:
        with contextlib.suppress(Exception):
            run_ingest_job(
                job_id,
                store=store,
                embed_client=embed_client,  # type: ignore[arg-type]
                write_client=write_client,  # type: ignore[arg-type]
                fetch_document=lambda url: fetch_html_fixture(url, fixture_html=_FIXTURE_HTML),
            )

    app = create_app(store=store, require_proxy_auth=True, pipeline_runner=runner)
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client


def test_uj062_same_content_hash_skips_re_embed(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-187 / AC-IR1: re-ingest with force=false skips embed when hash matches."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    store = InMemoryJobStore()
    embed_client = _CountingEmbedClient()
    write_client = _HashAwareWriteClient()
    write_client.seed_hash(_URL, _fixture_digest())
    client = _build_client(store=store, embed_client=embed_client, write_client=write_client)

    create = client.post(
        "/jobs",
        json={"urls": [_URL], "options": {"chunk_size_tokens": 64, "force": False}},
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    body = response_json_object(client.get(f"/jobs/{job_id}"))
    assert json_str(body, "status") == "completed"
    assert embed_client.batch_calls == _ZERO_EMBED_CALLS
    assert write_client.last_batch is not None
    assert write_client.last_batch.documents[0].chunks == []
    metrics = as_json_object(body["metrics"])
    assert metrics["skipped_unchanged"] == 1
    assert metrics["urls_failed_embed"] == 0

    listed = response_json_object(client.get("/jobs"))
    job_ids = {json_str(job, "job_id") for job in json_object_list(listed, "jobs")}
    assert job_id in job_ids


def test_uj062_force_bypasses_content_hash_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-188 / AC-IR2: force=true re-embeds even when content_hash matches."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    store = InMemoryJobStore()
    embed_client = _CountingEmbedClient()
    write_client = _HashAwareWriteClient()
    write_client.seed_hash(_URL, _fixture_digest())
    client = _build_client(store=store, embed_client=embed_client, write_client=write_client)

    create = client.post(
        "/jobs",
        json={"urls": [_URL], "options": {"chunk_size_tokens": 64, "force": True}},
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    body = response_json_object(client.get(f"/jobs/{job_id}"))
    assert json_str(body, "status") == "completed"
    assert embed_client.batch_calls >= 1
    assert write_client.last_batch is not None
    assert write_client.last_batch.documents[0].chunks


def test_uj062_transient_embed_failure_retries_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-189 / AC-IR3: EmbeddingClient recovers from transient 503s."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    monkeypatch.setenv("VECINITA_EMBED_BATCH_SIZE", "2")
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "3")
    monkeypatch.setenv("VECINITA_EMBED_RETRY_BACKOFF_S", "0")

    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        payload = as_json_object(cast("object", json.loads(request.content.decode())))
        texts = cast("list[object]", payload.get("texts", []))
        attempts["n"] += 1
        if attempts["n"] <= _TRANSIENT_FAILURES_BEFORE_OK:
            return httpx.Response(503, text="temporary")
        return httpx.Response(
            200,
            json={"embeddings": [_EMBED_VECTOR for _ in texts]},
        )

    transport = httpx.MockTransport(handler)
    embed_client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    store = InMemoryJobStore()
    write_client = _HashAwareWriteClient()
    client = _build_client(store=store, embed_client=embed_client, write_client=write_client)

    create = client.post(
        "/jobs",
        json={"urls": [_URL], "options": {"chunk_size_tokens": 64, "force": True}},
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    body = response_json_object(client.get(f"/jobs/{job_id}"))
    assert json_str(body, "status") == "completed"
    assert attempts["n"] >= _MIN_ATTEMPTS_AFTER_RETRY
    assert write_client.last_batch is not None
    assert write_client.last_batch.documents[0].chunks
    embed_client.close()


def test_uj062_exhausted_embed_retries_fail_job(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-190 / AC-IR4: exhausted embed retries mark the job failed."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    monkeypatch.setenv("VECINITA_EMBED_MAX_RETRIES", "1")
    monkeypatch.setenv("VECINITA_EMBED_RETRY_BACKOFF_S", "0")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    transport = httpx.MockTransport(handler)
    embed_client = EmbeddingClient(
        "http://embed.test",
        http_client=httpx.Client(transport=transport, base_url="http://embed.test"),
    )
    store = InMemoryJobStore()
    write_client = _HashAwareWriteClient()
    client = _build_client(store=store, embed_client=embed_client, write_client=write_client)

    create = client.post(
        "/jobs",
        json={"urls": [_URL], "options": {"chunk_size_tokens": 64, "force": True}},
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    body = response_json_object(client.get(f"/jobs/{job_id}"))
    assert json_str(body, "status") == "failed"
    assert body["error_code"]
    metrics = as_json_object(body["metrics"])
    assert metrics["urls_failed_embed"] == 1
    embed_client.close()
