"""T127.2/T127.4 — Automations write-API routes (config GET/PATCH + runs list).

[Corpus: feature-list.md §F75]
[Spec: docs/api-contract.md §EV-027 Automations]
[Spec: docs/test-plan.md §TC-252 TC-255]
[Spec: docs/acceptance-criteria.md §AC-AU1 AC-AU5]
"""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from vecinita_internal_write_api.automations import (
    _row_datetime,  # pyright: ignore[reportPrivateUsage]
    _row_datetime_optional,  # pyright: ignore[reportPrivateUsage]
    _run_from_row,  # pyright: ignore[reportPrivateUsage]
)
from vecinita_shared_schemas.automations import (
    DEFAULT_AUTOMATIONS_MAX_CONCURRENT,
    AutomationRunListResponse,
    AutomationsConfigPatchRequest,
    AutomationsConfigResponse,
)

from tests.helpers.json_response import response_json_object
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

_PAGE_SIZE = 20


def test_get_automations_config_returns_contract_shape(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /internal/v1/automations/config returns enable + kill-switch + cap."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    monkeypatch.setenv(
        "VECINITA_AUTOMATIONS_MAX_CONCURRENT",
        str(DEFAULT_AUTOMATIONS_MAX_CONCURRENT),
    )

    response = write_client.get(
        "/internal/v1/automations/config",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = AutomationsConfigResponse.model_validate(response_json_object(response))
    assert body.kill_switch is False
    assert body.max_concurrent == DEFAULT_AUTOMATIONS_MAX_CONCURRENT
    assert isinstance(body.enabled, bool)


def test_patch_automations_config_toggles_enabled(
    write_client: TestClient,
) -> None:
    """PATCH /internal/v1/automations/config enable/disable (AC-AU1 / TC-252)."""
    response = write_client.patch(
        "/internal/v1/automations/config",
        headers=auth_headers(),
        json=AutomationsConfigPatchRequest(enabled=True).model_dump(),
    )
    assert response.status_code == HTTPStatus.OK
    body = AutomationsConfigResponse.model_validate(response_json_object(response))
    assert body.enabled is True


def test_list_automations_runs_returns_paginated_history(
    write_client: TestClient,
) -> None:
    """GET /internal/v1/automations/runs lists history (TC-255 / AC-AU5)."""
    response = write_client.get(
        "/internal/v1/automations/runs",
        headers=auth_headers(),
        params={"page": 1, "page_size": _PAGE_SIZE},
    )
    assert response.status_code == HTTPStatus.OK
    body = AutomationRunListResponse.model_validate(response_json_object(response))
    assert body.page == 1
    assert body.page_size == _PAGE_SIZE
    assert body.total_count >= 0
    assert isinstance(body.items, list)


def test_automation_row_datetime_helpers_cover_type_branches() -> None:
    """Cover datetime coercion helpers used by automation_runs mapping (TP3)."""
    now = datetime.now(UTC)
    assert _row_datetime({"started_at": now}, "started_at") == now
    with pytest.raises(TypeError, match="Expected datetime"):
        _row_datetime({"started_at": "not-a-datetime"}, "started_at")
    assert _row_datetime_optional({"finished_at": None}, "finished_at") is None
    assert _row_datetime_optional({"finished_at": now}, "finished_at") == now

    run_id = uuid4()
    row = {
        "id": run_id,
        "job_type": "automation_catchup",
        "status": "completed",
        "started_at": now,
        "finished_at": None,
        "error": None,
        "document_id": None,
        "revision": None,
        "created_at": now,
        "updated_at": now,
    }
    run = _run_from_row(row)
    assert run.id == run_id
    assert run.finished_at is None
    assert run.started_at == now
