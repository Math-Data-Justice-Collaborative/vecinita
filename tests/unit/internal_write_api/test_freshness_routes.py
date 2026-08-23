"""T128.3 — write-API freshness PATCH / stale list / Refresh now enqueue (F76).

[Corpus: feature-list.md §F76]
[Spec: docs/api-contract.md §EV-027 Freshness]
[Spec: docs/test-plan.md §TC-256-TC-259]
[Spec: docs/acceptance-criteria.md §AC-FR1-FR4]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP7]
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import text
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    json_bool,
    json_str,
    json_str_optional,
    response_document_list_items,
    response_json_object,
)
from tests.unit.internal_write_api.conftest import auth_headers, upsert_document_via_api

if TYPE_CHECKING:
    import pytest
    from fastapi.testclient import TestClient
    from sqlalchemy.engine import Engine

    from tests.unit.internal_write_api.conftest import StubJobsClient


def test_patch_refresh_enabled_persists_and_returns_fields(
    write_client: TestClient,
    engine: Engine,
) -> None:
    """TC-259 / AC-FR4: PATCH refresh_enabled; response includes freshness fields."""
    document_id = upsert_document_via_api(write_client)

    response = write_client.patch(
        f"/internal/v1/documents/{document_id}",
        json={"refresh_enabled": False},
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "document_id") == document_id
    assert json_bool(body, "refresh_enabled") is False
    assert "last_checked_at" in body

    with engine.connect() as conn:
        row = (
            conn.execute(
                text("SELECT refresh_enabled, last_checked_at FROM documents WHERE id = :id"),
                {"id": document_id},
            )
            .mappings()
            .one()
        )
    assert row["refresh_enabled"] is False
    assert row["last_checked_at"] is None


def test_list_documents_stale_filter_returns_old_last_checked(
    write_client: TestClient,
    engine: Engine,
) -> None:
    """TC-256 / TC-258: GET documents?stale=true filters by last_checked_at threshold."""
    document_id = upsert_document_via_api(write_client)
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
            {"id": document_id, "checked": stale_at},
        )

    listing = write_client.get(
        "/internal/v1/documents",
        params={"page": 1, "page_size": 100, "stale": "true"},
        headers=auth_headers(),
    )
    assert listing.status_code == HTTPStatus.OK
    items = [as_json_object(item) for item in response_document_list_items(listing)]
    match = next((item for item in items if json_str(item, "document_id") == document_id), None)
    assert match is not None
    assert json_bool(match, "refresh_enabled") is True
    assert json_str_optional(match, "last_checked_at") is not None
    assert json_bool(match, "stale") is True


def test_refresh_now_enqueues_freshness_job(
    write_client_with_jobs: tuple[TestClient, StubJobsClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-259: Refresh now → enqueue freshness_refresh (force bypasses stale)."""
    client, jobs = write_client_with_jobs
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.delenv("VECINITA_AUTOMATIONS_KILL_SWITCH", raising=False)
    document_id = upsert_document_via_api(client)

    response = client.post(
        f"/internal/v1/documents/{document_id}/refresh",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert "job_id" in body
    assert UUID(json_str(body, "job_id"))
    assert len(jobs.enqueued_freshness) == 1
    assert jobs.enqueued_freshness[0][0] == UUID(document_id)
    assert jobs.enqueued_freshness[0][1] is True  # force=True


def test_refresh_now_skips_when_refresh_disabled(
    write_client_with_jobs: tuple[TestClient, StubJobsClient],
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-259: per-source refresh_enabled=false → skip enqueue."""
    client, jobs = write_client_with_jobs
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    document_id = upsert_document_via_api(client)
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE documents SET refresh_enabled = false WHERE id = :id"),
            {"id": document_id},
        )

    response = client.post(
        f"/internal/v1/documents/{document_id}/refresh",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert jobs.enqueued_freshness == []


def test_refresh_now_conflict_when_freshness_disabled(
    write_client_with_jobs: tuple[TestClient, StubJobsClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Master freshness disable → Refresh now returns conflict."""
    client, jobs = write_client_with_jobs
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "false")
    monkeypatch.delenv("VECINITA_AUTOMATIONS_KILL_SWITCH", raising=False)
    document_id = upsert_document_via_api(client)

    response = client.post(
        f"/internal/v1/documents/{document_id}/refresh",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert jobs.enqueued_freshness == []


def test_refresh_now_conflict_when_kill_switch(
    write_client_with_jobs: tuple[TestClient, StubJobsClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Shared kill-switch → Refresh now returns conflict."""
    client, jobs = write_client_with_jobs
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    document_id = upsert_document_via_api(client)

    response = client.post(
        f"/internal/v1/documents/{document_id}/refresh",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.CONFLICT
    assert jobs.enqueued_freshness == []


def test_refresh_now_404_when_document_missing(
    write_client_with_jobs: tuple[TestClient, StubJobsClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refresh now on unknown document → 404."""
    client, jobs = write_client_with_jobs
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    missing = uuid.uuid4()

    response = client.post(
        f"/internal/v1/documents/{missing}/refresh",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert jobs.enqueued_freshness == []


def test_mark_document_checked_bumps_last_checked(
    write_client: TestClient,
    engine: Engine,
) -> None:
    """T128.4 / TC-257: POST mark-checked sets last_checked_at."""
    document_id = upsert_document_via_api(write_client)
    response = write_client.post(
        f"/internal/v1/documents/{document_id}/mark-checked",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.OK
    body = response_json_object(response)
    assert json_str(body, "document_id") == document_id
    assert json_str_optional(body, "last_checked_at") is not None

    with engine.connect() as conn:
        row = (
            conn.execute(
                text("SELECT last_checked_at FROM documents WHERE id = :id"),
                {"id": document_id},
            )
            .mappings()
            .one()
        )
    assert row["last_checked_at"] is not None


def test_mark_document_checked_404_when_missing(
    write_client: TestClient,
) -> None:
    """mark-checked on unknown document → 404."""
    response = write_client.post(
        f"/internal/v1/documents/{uuid.uuid4()}/mark-checked",
        headers=auth_headers(),
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_list_documents_includes_freshness_fields_by_default(
    write_client: TestClient,
) -> None:
    """TC-258: admin list exposes refresh_enabled / last_checked / stale."""
    document_id = upsert_document_via_api(
        write_client,
        url=f"https://freshness-list-{uuid.uuid4().hex[:10]}.example.com/",
    )
    listing = write_client.get(
        "/internal/v1/documents",
        params={"page": 1, "page_size": 100},
        headers=auth_headers(),
    )
    assert listing.status_code == HTTPStatus.OK
    items = [as_json_object(item) for item in response_document_list_items(listing)]
    match = next((item for item in items if json_str(item, "document_id") == document_id), None)
    assert match is not None
    assert json_bool(match, "refresh_enabled") is True
    assert "last_checked_at" in match
    assert json_bool(match, "stale") is True  # never checked → stale


def test_list_documents_stale_and_missing_body_combined(
    write_client: TestClient,
    engine: Engine,
) -> None:
    """Branch coverage: stale=true with missing_body filter combination."""
    document_id = upsert_document_via_api(
        write_client,
        url=f"https://freshness-combo-{uuid.uuid4().hex[:10]}.example.com/",
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE documents
                SET body_text = NULL, last_checked_at = NULL, refresh_enabled = true
                WHERE id = :id
                """
            ),
            {"id": document_id},
        )
    listing = write_client.get(
        "/internal/v1/documents",
        params={"page": 1, "page_size": 100, "stale": True, "missing_body": True},
        headers=auth_headers(),
    )
    assert listing.status_code == HTTPStatus.OK
    items = [as_json_object(item) for item in response_document_list_items(listing)]
    assert any(json_str(item, "document_id") == document_id for item in items)
