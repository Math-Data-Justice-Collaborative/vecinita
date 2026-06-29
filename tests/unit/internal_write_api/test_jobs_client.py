"""Unit tests for DataManagementJobsClient."""

from __future__ import annotations

from typing import cast
from uuid import uuid4

import httpx
import pytest
from vecinita_internal_write_api.jobs_client import (
    DataManagementJobsClient,
    DataManagementJobsClientError,
)


def test_jobs_client_requires_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VECINITA_MODAL_DATA_MGMT_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)

    with pytest.raises(DataManagementJobsClientError, match="required"):
        DataManagementJobsClient()


def test_enqueue_retag_posts_retag_job() -> None:
    document_id = uuid4()
    job_id = uuid4()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/jobs"
        assert request.headers["X-Vecinita-Proxy-Key"] == "proxy-key"
        body = request.read().decode()
        assert str(document_id) in body
        return httpx.Response(202, json={"job_id": str(job_id), "status": "pending"})

    transport = httpx.MockTransport(handler)
    client = DataManagementJobsClient(
        base_url="http://data-mgmt.test",
        proxy_key="proxy-key",
        http_client=httpx.Client(transport=transport, base_url="http://data-mgmt.test"),
    )

    result = client.enqueue_retag(document_id)

    assert result == job_id
    client.close()


def test_enqueue_retag_raises_on_http_error() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(500, text="fail"))
    client = DataManagementJobsClient(
        base_url="http://data-mgmt.test",
        proxy_key="proxy-key",
        http_client=httpx.Client(transport=transport, base_url="http://data-mgmt.test"),
    )

    with pytest.raises(DataManagementJobsClientError, match="500"):
        client.enqueue_retag(uuid4())
    client.close()


def test_jobs_client_closes_owned_http_client() -> None:
    closed: list[bool] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(202, json={"job_id": str(uuid4()), "status": "pending"})

    base_client = httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        http = base_client(
            base_url=cast("str", kwargs.get("base_url", "")),
            timeout=cast("float", kwargs.get("timeout", 60.0)),
            transport=httpx.MockTransport(handler),
        )
        original_close = http.close

        def tracked_close() -> None:
            closed.append(True)
            original_close()

        http.close = tracked_close  # type: ignore[method-assign]
        return http

    import httpx as httpx_module

    original = httpx_module.Client
    httpx_module.Client = client_factory  # type: ignore[misc]
    try:
        client = DataManagementJobsClient(
            base_url="http://data-mgmt.test",
            proxy_key="proxy-key",
        )
        client.close()
    finally:
        httpx_module.Client = original

    assert closed == [True]


def test_jobs_client_does_not_close_injected_client() -> None:
    closed: list[bool] = []
    transport = httpx.MockTransport(
        lambda _request: httpx.Response(202, json={"job_id": str(uuid4()), "status": "pending"}),
    )
    http = httpx.Client(transport=transport, base_url="http://data-mgmt.test")
    original_close = http.close

    def tracked_close() -> None:
        closed.append(True)
        original_close()

    http.close = tracked_close  # type: ignore[method-assign]
    client = DataManagementJobsClient(
        base_url="http://data-mgmt.test",
        proxy_key="proxy-key",
        http_client=http,
    )
    client.close()

    assert closed == []
