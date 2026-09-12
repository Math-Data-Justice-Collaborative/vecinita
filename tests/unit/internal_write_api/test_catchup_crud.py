"""T127.6 — write-API CRUD catch-up enqueue hook (RD-335).

[Corpus: feature-list.md §F75]
[Spec: docs/decisions.md §RD-335]
[Spec: docs/api-contract.md §EV-027 Automations]
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from vecinita_internal_write_api.catchup_crud import (
    maybe_enqueue_catchup_after_document_change,
)
from vecinita_shared_schemas.automations import AutomationsConfigResponse

if TYPE_CHECKING:
    import pytest

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


def _enabled_config(_engine: object) -> AutomationsConfigResponse:
    return AutomationsConfigResponse(
        enabled=True,
        kill_switch=False,
        max_concurrent=2,
    )


def test_crud_hook_enqueues_when_missing_and_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Body-only upsert (missing embeds) → async catch-up enqueue."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    enqueued: list[tuple[UUID, str, str]] = []

    class _Client:
        def fetch_catchup_enqueue_gates(
            self,
            *,
            authorization: str | None = None,
        ) -> tuple[int, frozenset[str]]:
            _ = authorization
            return (0, frozenset())

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
        _enabled_config,
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
        def fetch_catchup_enqueue_gates(
            self,
            *,
            authorization: str | None = None,
        ) -> tuple[int, frozenset[str]]:
            _ = authorization
            return (0, frozenset())

        def enqueue_automation_catchup(self, *_a: object, **_k: object) -> UUID:
            nonlocal posted
            posted = True
            return uuid4()

    monkeypatch.setattr(
        "vecinita_internal_write_api.catchup_crud.get_automations_config",
        _enabled_config,
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


def test_crud_hook_uses_fetch_catchup_enqueue_gates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-342 / AC-AU9: CRUD hook uses Data Management pending/running gate state."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    monkeypatch.setattr(
        "vecinita_internal_write_api.catchup_crud.get_automations_config",
        _enabled_config,
    )

    class _Client:
        def fetch_catchup_enqueue_gates(
            self,
            *,
            authorization: str | None = None,
        ) -> tuple[int, frozenset[str]]:
            _ = authorization
            return (2, frozenset())

        def enqueue_automation_catchup(self, *_a: object, **_k: object) -> UUID:
            return uuid4()

    decision = maybe_enqueue_catchup_after_document_change(
        engine=object(),  # type: ignore[arg-type]
        jobs_client=_Client(),  # type: ignore[arg-type]
        document_id=DOC_ID,
        revision="abc",
        embed_status="missing",
    )
    assert decision == "skip_at_capacity"


def test_crud_hook_returns_enqueue_failed_on_post_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-343 / AC-AU10: CRUD enqueue failure is distinguishable from disabled skip."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    monkeypatch.setattr(
        "vecinita_internal_write_api.catchup_crud.get_automations_config",
        _enabled_config,
    )

    class _Client:
        def fetch_catchup_enqueue_gates(
            self,
            *,
            authorization: str | None = None,
        ) -> tuple[int, frozenset[str]]:
            _ = authorization
            return (0, frozenset())

        def enqueue_automation_catchup(self, *_a: object, **_k: object) -> UUID:
            msg = "modal unavailable"
            raise RuntimeError(msg)

    decision = maybe_enqueue_catchup_after_document_change(
        engine=object(),  # type: ignore[arg-type]
        jobs_client=_Client(),  # type: ignore[arg-type]
        document_id=DOC_ID,
        revision="abc",
        embed_status="missing",
    )
    assert decision == "enqueue_failed"


def test_crud_hook_skips_when_jobs_client_none() -> None:
    """None jobs client → skip_disabled without touching Modal."""
    decision = maybe_enqueue_catchup_after_document_change(
        engine=object(),  # type: ignore[arg-type]
        jobs_client=None,
        document_id=DOC_ID,
        revision="abc",
        embed_status="missing",
    )
    assert decision == "skip_disabled"
