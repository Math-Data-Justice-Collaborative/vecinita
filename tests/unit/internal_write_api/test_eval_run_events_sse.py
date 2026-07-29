"""T83.2 / TP-S013-04 — GET /internal/v1/eval/runs/{run_id}/events SSE (EV-012)."""

from __future__ import annotations

import importlib
import json
from http import HTTPStatus
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_internal_write_api.eval_events import EvalRunEventBroker
from vecinita_shared_schemas.json_types import JsonObject, as_json_object

from tests.eval.conftest import eval_embed_fn
from tests.helpers.eval_judge import MockEvalJudge
from tests.unit.internal_write_api.conftest import StubJobsClient, auth_headers

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import FastAPI

_RUN_ID = UUID("55555555-5555-4555-8555-555555555555")
_ATTR_FORMAT = "format_sse_eval_event"
_ATTR_BROKER = "EvalRunEventBroker"
_ATTR_PUBLISH = "publish"
_ATTR_EVENTS_AFTER = "events_after"
_ATTR_EVENT_ID = "event_id"
_ATTR_PAYLOAD = "payload_json"


@pytest.fixture
def eval_sse_broker() -> EvalRunEventBroker:
    """Shared broker for injecting into create_app + seeding publishes."""
    return EvalRunEventBroker()


@pytest.fixture
def eval_sse_app(internal_api_env: None, eval_sse_broker: EvalRunEventBroker) -> FastAPI:
    """FastAPI app for eval SSE route registration checks."""
    _ = internal_api_env
    from vecinita_internal_write_api.app import create_app  # noqa: PLC0415

    return create_app(
        eval_embed_fn=eval_embed_fn,
        eval_judge=MockEvalJudge(),
        jobs_client=StubJobsClient(),  # type: ignore[arg-type]
        eval_event_broker=eval_sse_broker,
        sse_poll_interval_s=0.01,
        sse_max_cycles=3,
        eval_sse_sync_db=False,
    )


@pytest.fixture
def eval_sse_client(eval_sse_app: FastAPI) -> TestClient:
    """TestClient for eval SSE routes with Modal jobs stub."""
    return TestClient(eval_sse_app)


def _flush_sse_block(
    blocks: list[tuple[str | None, str | None, JsonObject | None]],
    event_id: str | None,
    event_name: str | None,
    data_lines: list[str],
) -> None:
    if event_id is None and event_name is None and not data_lines:
        return
    data_obj: JsonObject | None = None
    if data_lines:
        data_obj = as_json_object(cast("object", json.loads("\n".join(data_lines))))
    blocks.append((event_id, event_name, data_obj))


def _parse_sse_blocks(raw: str) -> list[tuple[str | None, str | None, JsonObject | None]]:
    """Parse SSE blocks into (id, event, data_json) tuples."""
    blocks: list[tuple[str | None, str | None, JsonObject | None]] = []
    event_id: str | None = None
    event_name: str | None = None
    data_lines: list[str] = []
    for line in raw.splitlines():
        if line == "":
            _flush_sse_block(blocks, event_id, event_name, data_lines)
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
    _flush_sse_block(blocks, event_id, event_name, data_lines)
    return blocks


def _load_eval_events() -> object:
    """Import eval_events module."""
    return importlib.import_module("vecinita_internal_write_api.eval_events")


def _broker(mod: object) -> object:
    broker_cls = cast("type[object]", getattr(mod, _ATTR_BROKER))
    return broker_cls()


def test_eval_run_events_route_is_registered(eval_sse_app: FastAPI) -> None:
    """Eval progress SSE path is registered on the write API (TP-S013-04)."""
    from fastapi.routing import APIRoute  # noqa: PLC0415

    paths = {route.path for route in eval_sse_app.routes if isinstance(route, APIRoute)}
    assert "/internal/v1/eval/runs/{run_id}/events" in paths


def test_format_sse_eval_event_uses_eval_run_event_name() -> None:
    """SSE frames use event: eval_run with monotonic id (TP-S013-04)."""
    mod = _load_eval_events()
    format_sse_eval_event = cast("Callable[..., str]", getattr(mod, _ATTR_FORMAT))
    payload = json.dumps({"run_id": str(_RUN_ID), "status": "running"}, separators=(",", ":"))
    frame = format_sse_eval_event(event_id="1", payload_json=payload)
    assert "id: 1\n" in frame
    assert "event: eval_run\n" in frame
    assert f'"run_id":"{_RUN_ID}"' in frame or f'"run_id": "{_RUN_ID}"' in frame
    assert frame.endswith("\n\n")


def test_eval_run_event_broker_reconnect_skips_seen_ids() -> None:
    """Last-Event-ID reconnect omits already-delivered event ids (TP-S013-04)."""
    mod = _load_eval_events()
    broker = _broker(mod)
    publish = cast("Callable[..., None]", getattr(broker, _ATTR_PUBLISH))
    events_after = cast("Callable[..., list[object]]", getattr(broker, _ATTR_EVENTS_AFTER))

    publish(run_id=_RUN_ID, status="pending")
    first = events_after(None)
    assert first
    last_id = cast("str", getattr(first[-1], _ATTR_EVENT_ID))

    publish(run_id=_RUN_ID, status="running")
    replay = events_after(last_id)
    assert all(getattr(event, _ATTR_EVENT_ID) != last_id for event in replay)
    assert any(
        '"status":"running"' in cast("str", getattr(event, _ATTR_PAYLOAD)) for event in replay
    )


def test_eval_run_events_returns_event_stream_content_type(
    eval_sse_client: TestClient,
    eval_sse_broker: EvalRunEventBroker,
) -> None:
    """GET …/events returns text/event-stream when the run exists (TP-S013-04)."""
    eval_sse_broker.publish(run_id=_RUN_ID, status="pending")

    with eval_sse_client.stream(
        "GET",
        f"/internal/v1/eval/runs/{_RUN_ID}/events",
        headers=auth_headers(),
    ) as response:
        assert response.status_code == HTTPStatus.OK
        assert response.headers["content-type"].startswith("text/event-stream")


def test_eval_run_events_emits_sse_framed_progress(
    eval_sse_client: TestClient,
    eval_sse_broker: EvalRunEventBroker,
) -> None:
    """HTTP stream emits id/event/data framed eval_run JSON (TP-S013-04)."""
    eval_sse_broker.publish(run_id=_RUN_ID, status="running")

    with eval_sse_client.stream(
        "GET",
        f"/internal/v1/eval/runs/{_RUN_ID}/events",
        headers=auth_headers(),
    ) as response:
        assert response.status_code == HTTPStatus.OK
        chunks: list[str] = []
        for chunk in response.iter_text():
            chunks.append(chunk)
            blocks = _parse_sse_blocks("".join(chunks))
            progress = [b for b in blocks if b[1] == "eval_run" and b[2] is not None]
            if progress:
                break
        else:
            pytest.fail("timed out waiting for eval_run SSE event")

    blocks = _parse_sse_blocks("".join(chunks))
    progress = [(eid, data) for eid, name, data in blocks if name == "eval_run" and data]
    assert progress
    event_id, data = progress[0]
    assert event_id
    assert data.get("run_id") == str(_RUN_ID)
    assert data.get("status") == "running"


def test_eval_run_events_unknown_run_returns_404(eval_sse_client: TestClient) -> None:
    """Missing run_id yields 404 on the events stream (TP-S013-04)."""
    response = eval_sse_client.get(
        f"/internal/v1/eval/runs/{uuid4()}/events",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
