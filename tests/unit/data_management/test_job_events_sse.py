"""T82.2 / TC-148 - GET /jobs/events SSE framing + reconnect (EV-012)."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, reset_auth_config_for_tests
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")


@pytest.fixture(autouse=True)
def _disable_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    """Allow route tests without a live Supabase JWKS."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")


def _client_with_principal(store: InMemoryJobStore, principal: AuthPrincipal) -> TestClient:
    app = create_app(store=store, require_proxy_auth=False)
    app.dependency_overrides[get_principal] = lambda: principal
    return TestClient(app)


def _parse_sse_blocks(raw: str) -> list[tuple[str | None, str | None, JsonObject | None]]:
    """Parse SSE blocks into (id, event, data_json) tuples."""
    blocks: list[tuple[str | None, str | None, JsonObject | None]] = []
    event_id: str | None = None
    event_name: str | None = None
    data_lines: list[str] = []
    for line in raw.splitlines():
        if line == "":
            if event_id is not None or event_name is not None or data_lines:
                data_obj: JsonObject | None = None
                if data_lines:
                    data_obj = as_json_object(cast("object", json.loads("\n".join(data_lines))))
                blocks.append((event_id, event_name, data_obj))
            event_id = None
            event_name = None
            data_lines = []
            continue
        if line.startswith(":"):
            continue
        if line.startswith("id:"):
            event_id = line.removeprefix("id:").lstrip()
        elif line.startswith("event:"):
            event_name = line.removeprefix("event:").lstrip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").lstrip())
    if event_id is not None or event_name is not None or data_lines:
        data_obj = None
        if data_lines:
            data_obj = as_json_object(cast("object", json.loads("\n".join(data_lines))))
        blocks.append((event_id, event_name, data_obj))
    return blocks


def test_jobs_events_returns_event_stream_content_type() -> None:
    """GET /jobs/events returns text/event-stream (TC-148 / TP-S013-01)."""
    store = InMemoryJobStore()
    client = _client_with_principal(store, _ADMIN)

    with client.stream("GET", "/jobs/events") as response:
        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"].startswith("text/event-stream")


def test_jobs_events_emits_sse_framed_job_snapshot() -> None:
    """Stream emits id/event/data framed Job JSON for existing jobs (TC-148)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/a"])
    store.update_job(record.job_id, status="running")
    client = _client_with_principal(store, _ADMIN)

    with client.stream("GET", "/jobs/events") as response:
        assert response.status_code == HTTPStatus.OK
        chunks: list[str] = []
        for chunk in response.iter_text():
            chunks.append(chunk)
            raw = "".join(chunks)
            blocks = _parse_sse_blocks(raw)
            job_blocks = [b for b in blocks if b[1] == "job" and b[2] is not None]
            if job_blocks:
                break
        else:
            pytest.fail("timed out waiting for job SSE event")

    raw = "".join(chunks)
    blocks = _parse_sse_blocks(raw)
    job_blocks = [
        (eid, name, data) for eid, name, data in blocks if name == "job" and data is not None
    ]
    assert job_blocks
    event_id, _name, data = job_blocks[0]
    assert event_id is not None and event_id != ""
    assert data is not None
    assert data.get("job_id") == str(record.job_id)
    assert data.get("status") == "running"


def test_jobs_events_reconnect_skips_seen_ids() -> None:
    """Last-Event-ID reconnect omits already-delivered event ids (TC-148)."""
    store = InMemoryJobStore()
    first = store.create_job(urls=["https://example.com/a"])
    store.update_job(first.job_id, status="running")
    client = _client_with_principal(store, _ADMIN)

    with client.stream("GET", "/jobs/events") as response:
        chunks: list[str] = []
        for chunk in response.iter_text():
            chunks.append(chunk)
            blocks = _parse_sse_blocks("".join(chunks))
            job_blocks = [b for b in blocks if b[1] == "job" and b[0]]
            if job_blocks:
                break
        else:
            pytest.fail("timed out waiting for initial job SSE event")

    first_blocks = [b for b in _parse_sse_blocks("".join(chunks)) if b[1] == "job" and b[0]]
    last_id = first_blocks[-1][0]
    assert last_id is not None

    second = store.create_job(urls=["https://example.com/b"])
    store.update_job(second.job_id, status="pending")

    with client.stream("GET", "/jobs/events", headers={"Last-Event-ID": last_id}) as response:
        assert response.status_code == HTTPStatus.OK
        chunks2: list[str] = []
        for chunk in response.iter_text():
            chunks2.append(chunk)
            blocks = _parse_sse_blocks("".join(chunks2))
            job_blocks = [b for b in blocks if b[1] == "job" and b[2] is not None]
            if any(
                b[2] is not None and b[2].get("job_id") == str(second.job_id) for b in job_blocks
            ):
                break
        else:
            pytest.fail("timed out waiting for post-reconnect job SSE event")

    replay = _parse_sse_blocks("".join(chunks2))
    job_replay = [(eid, data) for eid, name, data in replay if name == "job" and data is not None]
    assert all(eid != last_id for eid, _data in job_replay)
    assert all(data.get("job_id") != str(first.job_id) for _eid, data in job_replay)
    assert any(data.get("job_id") == str(second.job_id) for _eid, data in job_replay)
