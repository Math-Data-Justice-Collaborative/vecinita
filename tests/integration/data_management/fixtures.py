"""Data-management integration/E2E fixtures (loaded via ``tests.conftest`` pytest_plugins)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.pipeline import fetch_html_fixture
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.auth import reset_auth_config_for_tests
from vecinita_shared_schemas.internal_write import BatchUpsertResponse

if TYPE_CHECKING:
    from uuid import UUID

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[3] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_PROXY_KEY = "test-proxy-key"
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed batch."""
        return [_EMBED_VECTOR for _ in texts]

    def close(self) -> None:
        """Close."""
        return


class _MockWriteClient:
    def __init__(self) -> None:
        self.last_batch: object | None = None

    def upsert_batch(self, body: object) -> object:
        """Upsert batch."""
        self.last_batch = body
        chunks = sum(len(doc.chunks) for doc in body.documents)  # type: ignore[attr-defined]
        return BatchUpsertResponse(upserted_chunks=chunks)

    def close(self) -> None:
        """Close."""
        return


@pytest.fixture
def job_store() -> InMemoryJobStore:
    """Return a fresh in-memory job store."""
    return InMemoryJobStore()


@pytest.fixture
def mock_write() -> _MockWriteClient:
    """Return a mock internal-write client recording the last batch."""
    return _MockWriteClient()


@pytest.fixture
def dm_client(job_store: InMemoryJobStore, mock_write: _MockWriteClient) -> TestClient:
    """Return a data-management TestClient with mocked embed/write pipeline."""

    def runner(job_id: UUID) -> None:
        """Runner."""
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
    """Set proxy-key auth env unless the test is marked ``live``."""
    node = cast("pytest.Item", request.node)
    if node.get_closest_marker("live"):
        return
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")
