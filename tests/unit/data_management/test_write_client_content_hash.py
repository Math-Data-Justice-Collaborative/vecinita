"""Unit tests for InternalWriteClient content_hash lookup (F47 / #163)."""

from __future__ import annotations

from http import HTTPStatus
from uuid import uuid4

import httpx
import pytest
from vecinita_data_management_backend.write_client import (
    InternalWriteClient,
    InternalWriteClientError,
)


def test_get_content_hash_by_url_returns_hash() -> None:
    """Client parses DocumentContentHashResponse from write API."""
    document_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/internal/v1/documents/content-hash"
        assert request.url.params["url"] == "https://example.com/doc"
        return httpx.Response(
            HTTPStatus.OK,
            json={
                "url": "https://example.com/doc",
                "content_hash": "abc123",
                "document_id": str(document_id),
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://write.test")
    client = InternalWriteClient(
        base_url="https://write.test",
        api_key="test-key",
        http_client=http_client,
    )
    assert client.get_content_hash_by_url("https://example.com/doc") == "abc123"


def test_get_content_hash_by_url_returns_none_when_unknown() -> None:
    """Unknown URL yields null content_hash → None."""

    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(
            HTTPStatus.OK,
            json={
                "url": "https://example.com/missing",
                "content_hash": None,
                "document_id": None,
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://write.test")
    client = InternalWriteClient(
        base_url="https://write.test",
        api_key="test-key",
        http_client=http_client,
    )
    assert client.get_content_hash_by_url("https://example.com/missing") is None


def test_get_content_hash_by_url_raises_on_http_error() -> None:
    """Non-2xx content-hash lookup raises InternalWriteClientError."""

    def handler(request: httpx.Request) -> httpx.Response:
        _ = request
        return httpx.Response(HTTPStatus.BAD_GATEWAY, text="upstream down")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://write.test")
    client = InternalWriteClient(
        base_url="https://write.test",
        api_key="test-key",
        http_client=http_client,
    )
    with pytest.raises(InternalWriteClientError, match="get_content_hash_by_url"):
        client.get_content_hash_by_url("https://example.com/doc")
