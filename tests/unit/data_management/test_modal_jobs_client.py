"""Unit coverage for ModalJobsEnqueueClient (F75 catch-up self-enqueue).

[Corpus: feature-list.md §F75]
[Spec: docs/decisions.md §RD-326 RD-335]
"""

from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from vecinita_data_management_backend.modal_jobs_client import (
    ModalJobsEnqueueClient,
    ModalJobsEnqueueError,
)

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


def test_modal_jobs_client_requires_url_and_proxy_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing URL or proxy key raises ModalJobsEnqueueError."""
    monkeypatch.delenv("VECINITA_MODAL_DATA_MGMT_URL", raising=False)
    monkeypatch.delenv("VECINITA_MODAL_PROXY_KEY", raising=False)
    with pytest.raises(ModalJobsEnqueueError, match="required"):
        ModalJobsEnqueueClient()

    monkeypatch.setenv("VECINITA_MODAL_DATA_MGMT_URL", "https://dm.example")
    with pytest.raises(ModalJobsEnqueueError, match="required"):
        ModalJobsEnqueueClient()


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
            client.enqueue_automation_catchup(
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
