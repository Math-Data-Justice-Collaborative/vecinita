"""UJ-023 / #89 (F32): Job Management tab — server-sourced list of running/completed/failed jobs.

Job status used to live only in `JobForm`'s component-local state on `/corpus`; navigating to
another tab dropped it (same class as #53). The fix makes job visibility server-sourced via a
`GET /jobs` list endpoint that backs the new Job Management tab. These E2E tests exercise that
endpoint through the full data-management ASGI app: newest-first ordering, `?status=` filtering,
failed jobs surfacing `error_code` / `error_message`, and persistence independent of any client
navigation (the source of truth is the server, so re-fetching after a tab switch shows the job).
"""

from __future__ import annotations

import contextlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.pipeline import fetch_html_fixture, run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION

from tests.helpers.json_response import json_object_list, json_str, response_json_object

pytestmark = pytest.mark.e2e

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_PROXY_KEY = "test-proxy-key"
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION
_GOOD_URL = "https://example.com/sample-page.html"
_BAD_URL = "https://invalid.example/bad-page.html"


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_EMBED_VECTOR for _ in texts]

    def close(self) -> None:
        return None


class _MockWriteClient:
    def upsert_batch(self, body: object) -> object:
        from vecinita_shared_schemas.internal_write import BatchUpsertResponse

        chunks = sum(len(doc.chunks) for doc in body.documents)  # type: ignore[attr-defined]
        return BatchUpsertResponse(upserted_chunks=chunks)

    def close(self) -> None:
        return None


def _fetch(url: str):  # type: ignore[no-untyped-def]
    if _BAD_URL in url:
        msg = "bad_url"
        raise ValueError(msg)
    return fetch_html_fixture(url, fixture_html=_FIXTURE_HTML)


@pytest.fixture
def dm_jobs_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    store = InMemoryJobStore()

    def runner(job_id) -> None:  # type: ignore[no-untyped-def]
        with contextlib.suppress(ValueError):
            run_ingest_job(
                job_id,
                store=store,
                embed_client=_MockEmbedClient(),  # type: ignore[arg-type]
                write_client=_MockWriteClient(),  # type: ignore[arg-type]
                fetch_document=_fetch,
            )

    app = create_app(store=store, require_proxy_auth=True, pipeline_runner=runner)
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client


def _create_job(client: TestClient, url: str) -> str:
    create = client.post("/jobs", json={"urls": [url], "options": {"chunk_size_tokens": 64}})
    assert create.status_code == 202
    return json_str(response_json_object(create), "job_id")


def test_list_jobs_returns_all_states_newest_first(dm_jobs_client: TestClient) -> None:
    completed_id = _create_job(dm_jobs_client, _GOOD_URL)  # created first -> older
    failed_id = _create_job(dm_jobs_client, _BAD_URL)  # created second -> newest

    body = response_json_object(dm_jobs_client.get("/jobs"))
    jobs = json_object_list(body, "jobs")
    assert len(jobs) == 2
    # Newest first: the failed job was created last.
    assert json_str(jobs[0], "job_id") == failed_id
    assert json_str(jobs[1], "job_id") == completed_id

    by_id = {json_str(job, "job_id"): job for job in jobs}
    assert json_str(by_id[completed_id], "status") == "completed"
    assert json_str(by_id[failed_id], "status") == "failed"


def test_list_jobs_status_filter(dm_jobs_client: TestClient) -> None:
    completed_id = _create_job(dm_jobs_client, _GOOD_URL)
    failed_id = _create_job(dm_jobs_client, _BAD_URL)

    failed_only = response_json_object(dm_jobs_client.get("/jobs", params={"status": "failed"}))
    assert [json_str(job, "job_id") for job in json_object_list(failed_only, "jobs")] == [failed_id]

    completed_only = response_json_object(
        dm_jobs_client.get("/jobs", params={"status": "completed"})
    )
    assert [json_str(job, "job_id") for job in json_object_list(completed_only, "jobs")] == [
        completed_id
    ]

    running_only = response_json_object(dm_jobs_client.get("/jobs", params={"status": "running"}))
    assert json_object_list(running_only, "jobs") == []


def test_failed_job_surfaces_error_code_and_message(dm_jobs_client: TestClient) -> None:
    failed_id = _create_job(dm_jobs_client, _BAD_URL)

    body = response_json_object(dm_jobs_client.get("/jobs"))
    failed = next(
        job for job in json_object_list(body, "jobs") if json_str(job, "job_id") == failed_id
    )
    assert json_str(failed, "status") == "failed"
    assert failed["error_code"]
    assert failed["error_message"]
    assert json_str(failed, "job_type") == "ingest"


def test_jobs_persist_across_client_navigation(dm_jobs_client: TestClient) -> None:
    """A job created from one 'tab' is still listed on a later request (server-sourced)."""
    job_id = _create_job(dm_jobs_client, _GOOD_URL)

    # Simulate the operator navigating away and later opening the Job Management tab:
    # a brand-new request (no client state) still sees the job because it lives server-side.
    listed = response_json_object(dm_jobs_client.get("/jobs"))
    assert job_id in {json_str(job, "job_id") for job in json_object_list(listed, "jobs")}
