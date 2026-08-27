"""EV-030 / F75: optional ingest bilingual translation (TC-252-254).

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-ingest-bilingual-translation.md]
[Spec: docs/test-plan.md §TC-252-254]
"""

from __future__ import annotations

import os
import uuid
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.pipeline import fetch_html_fixture, run_ingest_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_rag.retriever import CorpusPgvectorRetriever
from vecinita_shared_schemas.internal_write import (
    BatchUpsertDocumentResult,
    BatchUpsertRequest,
    BatchUpsertResponse,
)
from vecinita_shared_schemas.json_types import as_json_object
from vecinita_tagging.vocabulary import SeedTag

from tests.helpers.json_response import (
    json_int,
    json_object_list,
    json_str,
    response_json_object,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

pytestmark = [pytest.mark.e2e, pytest.mark.integration]

_FIXTURE_HTML = (
    Path(__file__).resolve().parents[2] / "data" / "fixtures" / "ingest" / "sample-page.html"
).read_text(encoding="utf-8")
_PROXY_KEY = "test-proxy-key"
_API_KEY = "test-internal-key"
_EMBED_VECTOR = [0.01] * EMBEDDING_DIMENSION
_SOURCE_DOC_ID = UUID("11111111-1111-4111-8111-111111111111")
_TRANSLATED_DOC_ID = UUID("22222222-2222-4222-8222-222222222222")
_VOCAB = [SeedTag(slug="housing", label_en="Housing", label_es="Vivienda")]
_EXPECTED_UPSERT_BATCHES = 2


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


class _MockEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [_EMBED_VECTOR for _ in texts]

    def close(self) -> None:
        return


class _StubTranslateClient:
    def translate_chunk(
        self,
        text: str,
        *,
        source_locale: str,
        target_locale: str,
    ) -> str:
        _ = source_locale
        return f"[{target_locale}] {text}"


class _RecordingWriteClient:
    def __init__(self) -> None:
        self.batches: list[BatchUpsertRequest] = []

    def upsert_batch(self, body: BatchUpsertRequest) -> BatchUpsertResponse:
        self.batches.append(body)
        if len(self.batches) == 1:
            doc = body.documents[0]
            return BatchUpsertResponse(
                upserted_chunks=len(doc.chunks),
                documents=[
                    BatchUpsertDocumentResult(
                        document_id=_SOURCE_DOC_ID,
                        url=str(doc.url),
                        language=doc.language,
                    )
                ],
            )
        translated = body.documents[0]
        return BatchUpsertResponse(
            upserted_chunks=len(translated.chunks),
            documents=[
                BatchUpsertDocumentResult(
                    document_id=_TRANSLATED_DOC_ID,
                    url=str(translated.url),
                    language=translated.language,
                )
            ],
        )

    def close(self) -> None:
        return


@pytest.fixture
def bilingual_dm_client(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[TestClient, _RecordingWriteClient]:
    """DM app with stubbed translate path wired through POST /jobs."""
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", _PROXY_KEY)
    store = InMemoryJobStore()
    write_client = _RecordingWriteClient()

    def runner(job_id: UUID) -> None:
        run_ingest_job(
            job_id,
            store=store,
            embed_client=_MockEmbedClient(),  # type: ignore[arg-type]
            write_client=write_client,  # type: ignore[arg-type]
            fetch_document=lambda url: fetch_html_fixture(url, fixture_html=_FIXTURE_HTML),
            translate_client=_StubTranslateClient(),
            tag_vocabulary=_VOCAB,
        )

    app = create_app(store=store, require_proxy_auth=True, pipeline_runner=runner)
    client = TestClient(app)
    client.headers.update({"X-Vecinita-Proxy-Key": _PROXY_KEY})
    return client, write_client


def test_tc252_ingest_translate_locales_completes_with_metrics(
    bilingual_dm_client: tuple[TestClient, _RecordingWriteClient],
) -> None:
    """TC-252: POST /jobs with translate_locales=[es] → completed + translation metrics."""
    client, write_client = bilingual_dm_client

    create = client.post(
        "/jobs",
        json={
            "urls": ["https://example.com/sample-page.html"],
            "options": {"chunk_size_tokens": 64, "translate_locales": ["es"]},
        },
    )
    assert create.status_code == HTTPStatus.ACCEPTED
    job_id = json_str(response_json_object(create), "job_id")

    status = client.get(f"/jobs/{job_id}")
    assert status.status_code == HTTPStatus.OK
    body = response_json_object(status)
    assert json_str(body, "status") == "completed"
    assert body["error_code"] is None
    metrics = as_json_object(body["metrics"])
    assert json_int(metrics, "translated_documents") == 1
    assert json_int(metrics, "translated_chunks") >= 1

    assert len(write_client.batches) == _EXPECTED_UPSERT_BATCHES
    translated = write_client.batches[1].documents[0]
    assert translated.language == "es"
    assert translated.paired_document_id == _SOURCE_DOC_ID
    assert translated.publish_status == "draft"
    assert translated.chunks[0].text.startswith("[es] ")


@pytest.fixture
def write_client() -> TestClient:
    """Internal-write API client for publish_status promotion."""
    os.environ["DATABASE_URL"] = _database_url()
    os.environ["VECINITA_INTERNAL_API_KEY"] = _API_KEY
    return TestClient(create_write_app())


@pytest.fixture
def engine() -> Engine:
    """SQLAlchemy engine for Postgres-backed promote/retrieval tests."""
    return create_engine(_database_url())


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture
def draft_es_document(write_client: TestClient, engine: Engine) -> Iterator[str]:
    """Seed published EN + draft ES siblings; clean up after."""
    doc_url = f"https://ev030-{uuid.uuid4().hex[:10]}.example.com/"
    vector_literal = "[" + ",".join(str(v) for v in _EMBED_VECTOR) + "]"
    batch = write_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": "English source",
                    "language": "en",
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "Community resource hours in English.",
                            "embedding": _EMBED_VECTOR,
                        }
                    ],
                }
            ]
        },
        headers=_auth(),
    )
    assert batch.status_code == HTTPStatus.OK
    batch_body = response_json_object(batch)
    source_id = json_str(json_object_list(batch_body, "documents")[0], "document_id")

    draft = write_client.post(
        "/internal/v1/documents/batch",
        json={
            "documents": [
                {
                    "url": doc_url,
                    "title": "Spanish draft",
                    "language": "es",
                    "publish_status": "draft",
                    "paired_document_id": source_id,
                    "chunks": [
                        {
                            "chunk_index": 0,
                            "text": "Horario del recurso comunitario en español.",
                            "embedding": _EMBED_VECTOR,
                        }
                    ],
                }
            ]
        },
        headers=_auth(),
    )
    assert draft.status_code == HTTPStatus.OK
    draft_id = json_str(
        json_object_list(response_json_object(draft), "documents")[0], "document_id"
    )
    _ = vector_literal
    yield draft_id
    with engine.begin() as conn:
        for doc_id in (draft_id, source_id):
            _ = conn.execute(text("DELETE FROM audit_log WHERE entity_id = :id"), {"id": doc_id})
            _ = conn.execute(
                text("DELETE FROM document_versions WHERE document_id = :id"),
                {"id": doc_id},
            )
            _ = conn.execute(
                text(
                    "DELETE FROM embeddings WHERE chunk_id IN " +  # noqa: S608
                    "(SELECT id FROM chunks WHERE document_id = :id)"
                ),
                {"id": doc_id},
            )
            _ = conn.execute(text("DELETE FROM chunks WHERE document_id = :id"), {"id": doc_id})
            _ = conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": doc_id})


def test_tc253_promote_draft_publish_status(
    write_client: TestClient,
    draft_es_document: str,
) -> None:
    """TC-253: PATCH publish_status draft → published returns updated document."""
    patched = write_client.patch(
        f"/internal/v1/documents/{draft_es_document}",
        json={"publish_status": "published"},
        headers=_auth(),
    )
    assert patched.status_code == HTTPStatus.OK
    body = response_json_object(patched)
    assert json_str(body, "document_id") == draft_es_document
    assert json_str(body, "publish_status") == "published"


def test_tc254_retriever_excludes_draft_documents(
    engine: Engine,
    draft_es_document: str,
) -> None:
    """TC-254: draft ES sibling is invisible to pgvector retrieval until promoted."""
    retriever = CorpusPgvectorRetriever(
        embed_fn=lambda _q: _EMBED_VECTOR,
        database_url=_database_url(),
        top_k=5,
    )
    before = retriever.retrieve_chunks("horario recurso comunitario", language="es")
    assert all(chunk.document_id != UUID(draft_es_document) for chunk in before)

    with engine.begin() as conn:
        _ = conn.execute(
            text("UPDATE documents SET publish_status = 'published' WHERE id = :id"),
            {"id": draft_es_document},
        )
    after = retriever.retrieve_chunks("horario recurso comunitario", language="es")
    assert any(chunk.document_id == UUID(draft_es_document) for chunk in after)
