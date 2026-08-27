"""UJ-080 / F75 — Automations enable/disable + run history API e2e.

[Corpus: feature-list.md §F75]
[Corpus: user-journeys.md §UJ-080]
[Spec: docs/test-plan.md §TC-252, TC-255]
[Spec: docs/acceptance-criteria.md §AC-AU1, AC-AU5]
[Spec: docs/api-contract.md §EV-027 Automations]
"""

from __future__ import annotations

import os
import uuid
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from sqlalchemy import text
from vecinita_shared_schemas.automations import (
    DEFAULT_AUTOMATIONS_MAX_CONCURRENT,
    AutomationRun,
    AutomationRunCreateRequest,
    AutomationRunListResponse,
    AutomationsConfigPatchRequest,
    AutomationsConfigResponse,
)
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one

from tests.helpers.json_response import response_json_object

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]

_API_KEY = "test-internal-key"
_PAGE_SIZE = 20


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture
def seeded_automation_run(engine: Engine) -> Iterator[UUID]:
    """Insert one automation_runs row; delete after test."""
    run_id = uuid.uuid4()
    with engine.begin() as conn:
        _ = conn.execute(
            text(
                """
                INSERT INTO automation_runs (
                    id, job_type, status, started_at, finished_at, error, revision
                )
                VALUES (
                    :id,
                    'automation_catchup',
                    'completed',
                    now() - interval '2 minutes',
                    now() - interval '1 minute',
                    NULL,
                    :revision
                )
                """
            ),
            {"id": run_id, "revision": f"uj080-{run_id.hex[:8]}"},
        )
    yield run_id
    with engine.begin() as conn:
        _ = conn.execute(text("DELETE FROM automation_runs WHERE id = :id"), {"id": run_id})


@pytest.fixture
def reset_automations_enabled(engine: Engine) -> Iterator[None]:
    """Restore automation_settings.enabled to false after the journey."""
    with engine.begin() as conn:
        prior = sqlalchemy_scalar_one(
            conn.execute(text("SELECT enabled FROM automation_settings WHERE id = 1"))
        )
    yield
    with engine.begin() as conn:
        _ = conn.execute(
            text(
                """
                UPDATE automation_settings
                SET enabled = :enabled, updated_at = now()
                WHERE id = 1
                """
            ),
            {"enabled": bool(prior)},
        )


def test_uj080_automations_enable_history_disable(
    write_client: TestClient,
    seeded_automation_run: UUID,
    reset_automations_enabled: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UJ-080: GET config → enable → list run history → disable (TC-252 / TC-255)."""
    _ = reset_automations_enabled
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    monkeypatch.setenv(
        "VECINITA_AUTOMATIONS_MAX_CONCURRENT",
        str(DEFAULT_AUTOMATIONS_MAX_CONCURRENT),
    )

    get_cfg = write_client.get("/internal/v1/automations/config", headers=_auth())
    assert get_cfg.status_code == HTTPStatus.OK
    cfg0 = AutomationsConfigResponse.model_validate(response_json_object(get_cfg))
    assert cfg0.kill_switch is False
    assert cfg0.max_concurrent == DEFAULT_AUTOMATIONS_MAX_CONCURRENT
    assert isinstance(cfg0.enabled, bool)

    enable = write_client.patch(
        "/internal/v1/automations/config",
        headers=_auth(),
        json=AutomationsConfigPatchRequest(enabled=True).model_dump(),
    )
    assert enable.status_code == HTTPStatus.OK
    cfg_on = AutomationsConfigResponse.model_validate(response_json_object(enable))
    assert cfg_on.enabled is True
    assert cfg_on.kill_switch is False

    runs = write_client.get(
        "/internal/v1/automations/runs",
        headers=_auth(),
        params={"page": 1, "page_size": _PAGE_SIZE},
    )
    assert runs.status_code == HTTPStatus.OK
    history = AutomationRunListResponse.model_validate(response_json_object(runs))
    assert history.page == 1
    assert history.page_size == _PAGE_SIZE
    assert history.total_count >= 1
    match = next((item for item in history.items if item.id == seeded_automation_run), None)
    assert match is not None
    assert match.job_type == "automation_catchup"
    assert match.status == "completed"
    assert match.error is None
    assert match.started_at is not None
    assert match.finished_at is not None

    disable = write_client.patch(
        "/internal/v1/automations/config",
        headers=_auth(),
        json=AutomationsConfigPatchRequest(enabled=False).model_dump(),
    )
    assert disable.status_code == HTTPStatus.OK
    cfg_off = AutomationsConfigResponse.model_validate(response_json_object(disable))
    assert cfg_off.enabled is False

    confirm = write_client.get("/internal/v1/automations/config", headers=_auth())
    assert confirm.status_code == HTTPStatus.OK
    cfg_final = AutomationsConfigResponse.model_validate(response_json_object(confirm))
    assert cfg_final.enabled is False


def test_uj082_post_automation_run_then_list(write_client: TestClient) -> None:
    """TC-289: POST run history then GET lists it (write-read parity / AC-AU5)."""
    document_id = uuid.uuid4()
    create = write_client.post(
        "/internal/v1/automations/runs",
        headers=_auth(),
        json=AutomationRunCreateRequest(
            job_type="automation_catchup",
            status="skipped",
            document_id=document_id,
            revision="e2e-1",
        ).model_dump(mode="json"),
    )
    assert create.status_code == HTTPStatus.CREATED
    created = AutomationRun.model_validate(response_json_object(create))
    assert created.job_type == "automation_catchup"
    assert created.status == "skipped"
    assert created.document_id == document_id
    assert created.revision == "e2e-1"
    assert created.error is None
    assert created.started_at is not None
    assert created.finished_at is not None

    listing = write_client.get(
        "/internal/v1/automations/runs",
        headers=_auth(),
        params={"page": 1, "page_size": _PAGE_SIZE},
    )
    assert listing.status_code == HTTPStatus.OK
    history = AutomationRunListResponse.model_validate(response_json_object(listing))
    match = next((item for item in history.items if item.id == created.id), None)
    assert match is not None
    assert match.job_type == created.job_type
    assert match.status == created.status
    assert match.document_id == created.document_id
    assert match.revision == created.revision
