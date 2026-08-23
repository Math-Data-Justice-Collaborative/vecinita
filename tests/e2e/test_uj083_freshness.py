"""UJ-081 / F76 — Freshness API e2e (stale list, enable, Refresh now, mark-checked).

[Corpus: feature-list.md §F76]
[Corpus: user-journeys.md §UJ-081]
[Spec: docs/test-plan.md §TC-256-TC-259 §TC-264]
[Spec: docs/acceptance-criteria.md §AC-FR1-FR5]
[Spec: docs/api-contract.md §EV-027 Freshness]
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from vecinita_internal_write_api.app import create_app as create_write_app
from vecinita_shared_schemas.freshness import freshness_enqueues_catchup
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    json_bool,
    json_str,
    json_str_optional,
    response_document_list_items,
    response_json_object,
)
from tests.unit.internal_write_api.conftest import StubJobsClient

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]

_API_KEY = "test-internal-key"


def _auth() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


def test_uj081_freshness_stale_disable_refresh_now_and_mark_checked(  # noqa: PLR0915  # UJ journey covers TC-256-259 end-to-end
    write_client: TestClient,
    seeded_document: UUID,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UJ-081: stale list, disable, Refresh now, mark-checked bump (TC-256-259)."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_FRESHNESS_STALE_DAYS", "30")
    monkeypatch.delenv("VECINITA_AUTOMATIONS_KILL_SWITCH", raising=False)

    stale_at = datetime.now(tz=UTC) - timedelta(days=31)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE documents
                SET last_checked_at = :checked, refresh_enabled = true
                WHERE id = :id
                """
            ),
            {"id": seeded_document, "checked": stale_at},
        )

    listing = write_client.get(
        "/internal/v1/documents",
        params={"page": 1, "page_size": 100, "stale": "true"},
        headers=_auth(),
    )
    assert listing.status_code == HTTPStatus.OK
    items = [as_json_object(item) for item in response_document_list_items(listing)]
    match = next(
        (item for item in items if json_str(item, "document_id") == str(seeded_document)),
        None,
    )
    assert match is not None
    assert json_bool(match, "stale") is True
    assert json_bool(match, "refresh_enabled") is True
    assert json_str_optional(match, "last_checked_at") is not None

    disable = write_client.patch(
        f"/internal/v1/documents/{seeded_document}",
        json={"refresh_enabled": False},
        headers=_auth(),
    )
    assert disable.status_code == HTTPStatus.OK
    disabled_body = response_json_object(disable)
    assert json_bool(disabled_body, "refresh_enabled") is False

    jobs = StubJobsClient()
    client_with_jobs = TestClient(create_write_app(jobs_client=jobs))  # type: ignore[arg-type]

    blocked = client_with_jobs.post(
        f"/internal/v1/documents/{seeded_document}/refresh",
        headers=_auth(),
    )
    assert blocked.status_code == HTTPStatus.CONFLICT
    assert jobs.enqueued_freshness == []

    enable = write_client.patch(
        f"/internal/v1/documents/{seeded_document}",
        json={"refresh_enabled": True},
        headers=_auth(),
    )
    assert enable.status_code == HTTPStatus.OK
    assert json_bool(response_json_object(enable), "refresh_enabled") is True

    refresh = client_with_jobs.post(
        f"/internal/v1/documents/{seeded_document}/refresh",
        headers=_auth(),
    )
    assert refresh.status_code == HTTPStatus.OK
    refresh_body = response_json_object(refresh)
    job_id = UUID(json_str(refresh_body, "job_id"))
    assert job_id
    assert len(jobs.enqueued_freshness) == 1
    enqueued_doc, force = jobs.enqueued_freshness[0]
    assert enqueued_doc == seeded_document
    assert force is True

    before = datetime.now(tz=UTC)
    marked = write_client.post(
        f"/internal/v1/documents/{seeded_document}/mark-checked",
        headers=_auth(),
    )
    assert marked.status_code == HTTPStatus.OK
    marked_body = response_json_object(marked)
    assert json_str(marked_body, "document_id") == str(seeded_document)
    checked_raw = json_str_optional(marked_body, "last_checked_at")
    assert checked_raw is not None
    checked_at = datetime.fromisoformat(checked_raw)
    assert checked_at.tzinfo is not None
    assert checked_at >= before - timedelta(seconds=5)

    listing_after = write_client.get(
        "/internal/v1/documents",
        params={"page": 1, "page_size": 100, "stale": "true"},
        headers=_auth(),
    )
    assert listing_after.status_code == HTTPStatus.OK
    after_items = [as_json_object(item) for item in response_document_list_items(listing_after)]
    still_stale = next(
        (item for item in after_items if json_str(item, "document_id") == str(seeded_document)),
        None,
    )
    assert still_stale is None


def test_uj081_freshness_does_not_enqueue_catchup_side_effect() -> None:
    """AC-FR5 / TC-264: freshness policy helper must not fire F75 catch-up."""
    assert freshness_enqueues_catchup() is False
