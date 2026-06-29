"""Unit tests for vecinita_data_management_backend.write_client."""

from __future__ import annotations

import json
from typing import cast
from uuid import uuid4

import httpx
import pytest
from pydantic import HttpUrl
from vecinita_data_management_backend.write_client import (
    InternalWriteClient,
    InternalWriteClientError,
)
from vecinita_embedding_client import EMBEDDING_DIMENSION
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    ChunkUpsert,
    DocumentDetail,
    DocumentUpsert,
    TagInput,
    TagPatchResponse,
)

_EMBEDDING = [0.01] * EMBEDDING_DIMENSION
_DOCUMENT_ID = uuid4()


def test_write_client_requires_env_or_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VECINITA_INTERNAL_WRITE_URL", raising=False)
    monkeypatch.delenv("VECINITA_INTERNAL_API_KEY", raising=False)

    with pytest.raises(InternalWriteClientError, match="VECINITA_INTERNAL_WRITE_URL"):
        InternalWriteClient()


def test_upsert_batch_posts_documents() -> None:
    seen: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(cast("dict[str, object]", json.loads(request.content.decode())))
        assert request.headers["Authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"upserted_chunks": 2})

    transport = httpx.MockTransport(handler)
    client = InternalWriteClient(
        "http://write.test",
        api_key="test-key",
        http_client=httpx.Client(transport=transport, base_url="http://write.test"),
    )
    body = BatchUpsertRequest(
        documents=[
            DocumentUpsert(
                url=HttpUrl("https://example.com/doc"),
                chunks=[
                    ChunkUpsert(chunk_index=0, text="chunk", embedding=_EMBEDDING),
                ],
            )
        ]
    )

    response = client.upsert_batch(body)

    assert isinstance(response, BatchUpsertResponse)
    assert response.upserted_chunks == 2
    assert seen
    client.close()


def test_upsert_batch_raises_on_http_error() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(500, json={}))
    client = InternalWriteClient(
        "http://write.test",
        api_key="test-key",
        http_client=httpx.Client(transport=transport, base_url="http://write.test"),
    )

    with pytest.raises(InternalWriteClientError, match="500"):
        client.upsert_batch(
            BatchUpsertRequest(
                documents=[
                    DocumentUpsert(
                        url=HttpUrl("https://example.com/doc"),
                        chunks=[
                            ChunkUpsert(chunk_index=0, text="chunk", embedding=_EMBEDDING),
                        ],
                    )
                ]
            )
        )
    client.close()


def test_get_document_detail_returns_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == f"/internal/v1/documents/{_DOCUMENT_ID}"
        return httpx.Response(
            200,
            json={
                "document_id": str(_DOCUMENT_ID),
                "title": "Notice",
                "text": "Body text",
                "language": "en",
                "url": "https://example.com/doc",
            },
        )

    transport = httpx.MockTransport(handler)
    client = InternalWriteClient(
        "http://write.test",
        api_key="test-key",
        http_client=httpx.Client(transport=transport, base_url="http://write.test"),
    )

    detail = client.get_document_detail(_DOCUMENT_ID)

    assert isinstance(detail, DocumentDetail)
    assert detail.text == "Body text"
    client.close()


def test_get_document_detail_raises_on_http_error() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(404, json={}))
    client = InternalWriteClient(
        "http://write.test",
        api_key="test-key",
        http_client=httpx.Client(transport=transport, base_url="http://write.test"),
    )

    with pytest.raises(InternalWriteClientError, match="404"):
        client.get_document_detail(_DOCUMENT_ID)
    client.close()


def test_patch_document_tags_posts_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == f"/internal/v1/documents/{_DOCUMENT_ID}/tags"
        return httpx.Response(
            200,
            json={"tags": [{"slug": "housing", "label": "Housing", "source": "llm"}]},
        )

    transport = httpx.MockTransport(handler)
    client = InternalWriteClient(
        "http://write.test",
        api_key="test-key",
        http_client=httpx.Client(transport=transport, base_url="http://write.test"),
    )

    response = client.patch_document_tags(
        _DOCUMENT_ID,
        [TagInput(slug="housing", label="Housing", source="llm")],
    )

    assert isinstance(response, TagPatchResponse)
    assert response.tags[0].slug == "housing"
    client.close()


def test_patch_document_tags_raises_on_http_error() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(400, json={}))
    client = InternalWriteClient(
        "http://write.test",
        api_key="test-key",
        http_client=httpx.Client(transport=transport, base_url="http://write.test"),
    )

    with pytest.raises(InternalWriteClientError, match="400"):
        client.patch_document_tags(_DOCUMENT_ID, [])
    client.close()


def test_write_client_closes_owned_client(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[bool] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"upserted_chunks": 0})

    base_client = httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        client = base_client(
            base_url=cast("str", kwargs.get("base_url", "")),
            timeout=cast("float", kwargs.get("timeout", 60.0)),
            transport=httpx.MockTransport(handler),
        )
        original_close = client.close

        def tracked_close() -> None:
            closed.append(True)
            original_close()

        client.close = tracked_close  # type: ignore[method-assign]
        return client

    monkeypatch.setattr(httpx, "Client", client_factory)
    client = InternalWriteClient("http://write.test", api_key="test-key")
    client.close()

    assert closed == [True]


def test_write_client_does_not_close_injected_http_client() -> None:
    closed: list[bool] = []

    transport = httpx.MockTransport(
        lambda _request: httpx.Response(200, json={"upserted_chunks": 0}),
    )
    http = httpx.Client(transport=transport, base_url="http://write.test")
    original_close = http.close

    def tracked_close() -> None:
        closed.append(True)
        original_close()

    http.close = tracked_close  # type: ignore[method-assign]
    client = InternalWriteClient("http://write.test", api_key="test-key", http_client=http)
    client.close()

    assert closed == []
