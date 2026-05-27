"""UJ-006 / TC-013: failed ingest surfaces error_code."""

from __future__ import annotations

import contextlib

import pytest
from fastapi.testclient import TestClient
from tests.helpers.json_response import json_str, response_json_object
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.pipeline import run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore

pytestmark = pytest.mark.e2e


def test_ingest_job_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "test-proxy-key")
    store = InMemoryJobStore()

    class _FailingEmbed:
        def embed_batch(self, texts: list[str]) -> list[list[float]]:
            raise RuntimeError("embed_unavailable")

        def close(self) -> None:
            return None

    class _Write:
        def upsert_batch(self, body: object) -> object:
            from vecinita_shared_schemas.internal_write import BatchUpsertResponse

            return BatchUpsertResponse(upserted_chunks=0)

        def close(self) -> None:
            return None

    def runner(job_id):  # type: ignore[no-untyped-def]
        with contextlib.suppress(RuntimeError, ValueError):
            run_ingest_job(
                job_id,
                store=store,
                embed_client=_FailingEmbed(),  # type: ignore[arg-type]
                write_client=_Write(),  # type: ignore[arg-type]
                fetch_document=lambda url: (_ for _ in ()).throw(ValueError("bad_url")),
            )

    app = create_app(store=store, require_proxy_auth=True, pipeline_runner=runner)
    client = TestClient(app)
    client.headers["X-Vecinita-Proxy-Key"] = "test-proxy-key"

    create = client.post("/jobs", json={"urls": ["https://invalid.example/bad"]})
    assert create.status_code == 202
    job_id = json_str(response_json_object(create), "job_id")

    body = response_json_object(client.get(f"/jobs/{job_id}"))
    assert body["status"] == "failed"
    assert body["error_code"]
