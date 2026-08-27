"""Unit coverage for ModalJobsEnqueueClient (F75 catch-up self-enqueue).

[Corpus: feature-list.md §F75]
[Spec: docs/decisions.md §RD-326 RD-335]
"""

from __future__ import annotations

import json
from typing import cast
from uuid import UUID, uuid4

import httpx
import pytest
from vecinita_data_management_backend.modal_jobs_client import (
    ModalJobsEnqueueClient,
    ModalJobsEnqueueError,
)
from vecinita_shared_schemas.json_types import as_json_object

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


def test_modal_jobs_client_requires_url_and_proxy_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing URL or proxy key raises ModalJobsEnqueueError."""
    monkeypatch.delenv("VECINITA_MODAL_DATA_MGMT_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
    with pytest.raises(ModalJobsEnqueueError, match="required"):
        _ = ModalJobsEnqueueClient()

    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "https://dm.example")
    with pytest.raises(ModalJobsEnqueueError, match="required"):
        _ = ModalJobsEnqueueClient()


def test_modal_jobs_client_enqueue_success_and_auth_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /jobs returns job_id; optional Authorization is forwarded."""
    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "https://dm.example/")
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "proxy-secret")
    job_id = uuid4()
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(202, json={"job_id": str(job_id), "status": "pending"})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(
        transport=transport,
        base_url="https://dm.example",
    )
    client = ModalJobsEnqueueClient(http_client=http_client)
    try:
        result = client.enqueue_automation_catchup(
            DOC_ID,
            revision="rev-1",
            embed_status="missing",
            authorization="Bearer jwt",
        )
    finally:
        client.close()
        http_client.close()

    assert result == job_id
    assert len(seen) == 1
    assert seen[0].headers["X-Vecinita-Proxy-Key"] == "proxy-secret"
    assert seen[0].headers["Authorization"] == "Bearer jwt"


def test_modal_jobs_client_enqueue_http_error_raises() -> None:
    """Non-2xx response becomes ModalJobsEnqueueError."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="unavailable")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(
        transport=transport,
        base_url="https://dm.example",
    )
    client = ModalJobsEnqueueClient(
        base_url="https://dm.example",
        proxy_key="proxy",
        http_client=http_client,
    )
    try:
        with pytest.raises(ModalJobsEnqueueError, match="503"):
            _ = client.enqueue_automation_catchup(
                DOC_ID,
                revision="1",
                embed_status="failed",
            )
    finally:
        client.close()
        http_client.close()


def test_modal_jobs_client_close_skips_injected_http_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Injected httpx.Client is not closed by ModalJobsEnqueueClient.close()."""
    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "https://dm.example")
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "proxy")
    closed = False

    class _TrackingClient(httpx.Client):
        def close(self) -> None:
            nonlocal closed
            closed = True
            super().close()

    http_client = _TrackingClient(base_url="https://dm.example")
    client = ModalJobsEnqueueClient(http_client=http_client)
    client.close()
    assert closed is False
    http_client.close()
    assert closed is True


def test_modal_jobs_client_owned_close_does_not_raise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Owned client close path runs without error (covers _owns=True)."""
    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "https://dm.example")
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "proxy")
    client = ModalJobsEnqueueClient()
    client.close()
    client.close()


def test_modal_jobs_client_enqueue_freshness_refresh_success() -> None:
    """F76 enqueue_freshness_refresh POSTs job_type and force/refresh flags."""
    job_id = uuid4()
    bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:

        decoded = cast("object", json.loads(request.content.decode()))
        bodies.append(as_json_object(decoded))
        return httpx.Response(202, json={"job_id": str(job_id), "status": "pending"})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://dm.example")
    client = ModalJobsEnqueueClient(
        base_url="https://dm.example",
        proxy_key="proxy",
        http_client=http_client,
    )
    try:
        result = client.enqueue_freshness_refresh(
            DOC_ID,
            force=False,
            refresh_enabled=True,
            is_stale=True,
        )
    finally:
        client.close()
        http_client.close()

    assert result == job_id
    assert len(bodies) == 1
    options = as_json_object(bodies[0]["options"])
    assert options["job_type"] == "freshness_refresh"
    assert options["document_id"] == str(DOC_ID)
    assert options["refresh_enabled"] is True
    assert options["is_stale"] is True
    assert options["force"] is False


def test_modal_jobs_client_enqueue_freshness_forwards_authorization() -> None:
    """Optional Authorization header is forwarded on freshness enqueue."""
    job_id = uuid4()
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(202, json={"job_id": str(job_id), "status": "pending"})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://dm.example")
    client = ModalJobsEnqueueClient(
        base_url="https://dm.example",
        proxy_key="proxy",
        http_client=http_client,
    )
    try:
        result = client.enqueue_freshness_refresh(
            DOC_ID,
            force=True,
            authorization="Bearer jwt-token",
        )
    finally:
        client.close()
        http_client.close()

    assert result == job_id
    assert seen[0].headers["Authorization"] == "Bearer jwt-token"


def test_modal_jobs_client_enqueue_freshness_http_error_raises() -> None:
    """Non-2xx freshness enqueue becomes ModalJobsEnqueueError."""

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="bad gateway")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://dm.example")
    client = ModalJobsEnqueueClient(
        base_url="https://dm.example",
        proxy_key="proxy",
        http_client=http_client,
    )
    try:
        with pytest.raises(ModalJobsEnqueueError, match="enqueue_freshness_refresh"):
            _ = client.enqueue_freshness_refresh(DOC_ID, force=True)
    finally:
        client.close()
        http_client.close()
