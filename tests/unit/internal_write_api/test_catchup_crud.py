"""T127.6 — write-API CRUD catch-up enqueue hook (RD-335).

[Corpus: feature-list.md §F75]
[Spec: docs/decisions.md §RD-335]
[Spec: docs/api-contract.md §EV-027 Automations]
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from vecinita_internal_write_api.catchup_crud import (
    maybe_enqueue_catchup_after_document_change,
)
from vecinita_shared_schemas.automations import AutomationsConfigResponse

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


def test_crud_hook_enqueues_when_missing_and_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Body-only upsert (missing embeds) → async catch-up enqueue."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    enqueued: list[tuple[UUID, str, str]] = []

    class _Client:
        def enqueue_automation_catchup(
            self,
            document_id: UUID,
            *,
            revision: str,
            embed_status: str,
            authorization: str | None = None,
        ) -> UUID:
            _ = authorization
            enqueued.append((document_id, revision, embed_status))
            return uuid4()

    monkeypatch.setattr(
        "vecinita_internal_write_api.catchup_crud.get_automations_config",
        lambda _engine: AutomationsConfigResponse(
            enabled=True,
            kill_switch=False,
            max_concurrent=2,
        ),
    )

    decision = maybe_enqueue_catchup_after_document_change(
        engine=object(),  # type: ignore[arg-type]
        jobs_client=_Client(),  # type: ignore[arg-type]
        document_id=DOC_ID,
        revision="abc",
        embed_status="missing",
    )
    assert decision == "enqueue"
    assert enqueued == [(DOC_ID, "abc", "missing")]


def test_crud_hook_skips_complete_without_post(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Complete embeds → skip_complete; no Modal POST."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    posted = False

    class _Client:
        def enqueue_automation_catchup(self, *_a: object, **_k: object) -> UUID:
            nonlocal posted
            posted = True
            return uuid4()

    monkeypatch.setattr(
        "vecinita_internal_write_api.catchup_crud.get_automations_config",
        lambda _engine: AutomationsConfigResponse(
            enabled=True,
            kill_switch=False,
            max_concurrent=2,
        ),
    )

    decision = maybe_enqueue_catchup_after_document_change(
        engine=object(),  # type: ignore[arg-type]
        jobs_client=_Client(),  # type: ignore[arg-type]
        document_id=DOC_ID,
        revision="abc",
        embed_status="complete",
    )
    assert decision == "skip_complete"
    assert posted is False
