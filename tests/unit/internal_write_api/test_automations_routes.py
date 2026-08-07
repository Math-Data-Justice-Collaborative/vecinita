"""T127.2 — Automations write-API routes (config GET/PATCH + runs list) — expect red until T127.4.

[Corpus: feature-list.md §F75]
[Spec: docs/api-contract.md §EV-027 Automations]
[Spec: docs/test-plan.md §TC-252 TC-255]
[Spec: docs/acceptance-criteria.md §AC-AU1 AC-AU5]
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from vecinita_shared_schemas.automations import (
    AutomationRunListResponse,
    AutomationsConfigPatchRequest,
    AutomationsConfigResponse,
)

from tests.helpers.json_response import response_json_object
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    import pytest
    from fastapi.testclient import TestClient

_PAGE_SIZE = 20


def test_get_automations_config_returns_contract_shape(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /internal/v1/automations/config returns enable + kill-switch + cap."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_MAX_CONCURRENT", "2")

    response = write_client.get(
        "/internal/v1/automations/config",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = AutomationsConfigResponse.model_validate(response_json_object(response))
    assert body == AutomationsConfigResponse(
        enabled=True,
        kill_switch=False,
        max_concurrent=2,
    )


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
