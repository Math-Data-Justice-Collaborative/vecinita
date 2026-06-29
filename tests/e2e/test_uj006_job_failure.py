"""UJ-006 / TC-013: failed ingest surfaces error_code."""

from __future__ import annotations

import contextlib
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.pipeline import run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.internal_write import BatchUpsertResponse

from tests.helpers.json_response import json_str, response_json_object

if TYPE_CHECKING:
    from uuid import UUID

    from vecinita_ingest.models import ScrapedDocument

pytestmark = pytest.mark.e2e


def _bad_fetch(url: str) -> ScrapedDocument:
    _ = url
    msg = "bad_url"
    raise ValueError(msg)


def test_ingest_job_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Failed embed step marks ingest job failed with error_code."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "test-proxy-key")
    store = InMemoryJobStore()

    class _FailingEmbed:
        def embed_batch(self, _texts: list[str]) -> list[list[float]]:
            """Embed batch."""
            msg = "embed_unavailable"
            raise RuntimeError(msg)

        def close(self) -> None:
            """Close."""
            return

    class _Write:
        def upsert_batch(self, _body: object) -> object:
            """Upsert batch."""
            return BatchUpsertResponse(upserted_chunks=0)

        def close(self) -> None:
            """Close."""
            return

    def runner(job_id: UUID) -> None:
        """Runner."""
        with contextlib.suppress(RuntimeError, ValueError):
            run_ingest_job(
                job_id,
                store=store,
                embed_client=_FailingEmbed(),  # type: ignore[arg-type]
                write_client=_Write(),  # type: ignore[arg-type]
                fetch_document=_bad_fetch,
            )

    app = create_app(store=store, require_proxy_auth=True, pipeline_runner=runner)
    client = TestClient(app)
    client.headers["X-Vecinita-Proxy-Key"] = "test-proxy-key"

    create = client.post("/jobs", json={"urls": ["https://invalid.example/bad"]})
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    body = response_json_object(client.get(f"/jobs/{job_id}"))
    assert body["status"] == "failed"
    assert body["error_code"]
