"""Data-management integration/E2E fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.pipeline import fetch_html_fixture
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.auth import reset_auth_config_for_tests

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_PROXY_KEY = "test-proxy-key"
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_EMBED_VECTOR for _ in texts]

    def close(self) -> None:
        return None


class _MockWriteClient:
    def __init__(self) -> None:
        self.last_batch: object | None = None

    def upsert_batch(self, body: object) -> object:
        self.last_batch = body
        from vecinita_shared_schemas.internal_write import BatchUpsertResponse

        chunks = sum(len(doc.chunks) for doc in body.documents)  # type: ignore[attr-defined]
        return BatchUpsertResponse(upserted_chunks=chunks)

    def close(self) -> None:
        return None


@pytest.fixture
def job_store() -> InMemoryJobStore:
    return InMemoryJobStore()


@pytest.fixture
def mock_write() -> _MockWriteClient:
    return _MockWriteClient()


@pytest.fixture
def dm_client(job_store: InMemoryJobStore, mock_write: _MockWriteClient) -> TestClient:
    def runner(job_id):  # type: ignore[no-untyped-def]
        run_job(
            job_id,
            store=job_store,
            embed_client=_MockEmbedClient(),  # type: ignore[arg-type]
            write_client=mock_write,  # type: ignore[arg-type]
            fetch_document=lambda url: fetch_html_fixture(url, fixture_html=_FIXTURE_HTML),
        )

    app = create_app(
        store=job_store,
        require_proxy_auth=True,
        pipeline_runner=runner,
    )
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client


@pytest.fixture(autouse=True)
def proxy_key_env(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("live"):
        return
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")
