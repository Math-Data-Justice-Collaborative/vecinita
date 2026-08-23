"""T128.1 — F76 freshness policy (stale threshold, hash skip, last_checked, kill-switch).

[Corpus: feature-list.md §F76]
[Spec: docs/acceptance-criteria.md §AC-FR1-FR5]
[Spec: docs/test-plan.md §TC-256-TC-257 §TC-259 §TC-264]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/config-spec.md §VECINITA_FRESHNESS_*]
[Spec: docs/decisions.md §RD-337]
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from vecinita_shared_schemas.automations import is_automations_kill_switch_on
from vecinita_shared_schemas.freshness import (
    DEFAULT_FRESHNESS_STALE_DAYS,
    FreshnessEnqueueDecision,
    FreshnessEnqueueRequest,
    decide_freshness_enqueue,
    decide_hash_aware_refresh,
    freshness_enqueues_catchup,
    is_document_stale,
    is_freshness_enabled,
    parse_freshness_stale_days,
    should_bump_last_checked_after_refresh,
)

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
_NOW = datetime(2026, 8, 12, 12, 0, 0, tzinfo=UTC)

_BASE_REQUEST = FreshnessEnqueueRequest(
    freshness_enabled=True,
    kill_switch=False,
    refresh_enabled=True,
    is_stale=True,
    force=False,
    document_id=DOC_ID,
)


def test_stale_days_default_is_30(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-256 / AC-FR1 / RD-337: default stale threshold is 30 days."""
    monkeypatch.delenv("VECINITA_FRESHNESS_STALE_DAYS", raising=False)
    expected_default = 30
    assert expected_default == DEFAULT_FRESHNESS_STALE_DAYS
    assert parse_freshness_stale_days() == expected_default


def test_parse_freshness_stale_days_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """config-spec: VECINITA_FRESHNESS_STALE_DAYS overrides default."""
    override_days = 14
    monkeypatch.setenv("VECINITA_FRESHNESS_STALE_DAYS", str(override_days))
    assert parse_freshness_stale_days() == override_days


def test_document_31_days_old_is_stale_at_default_threshold() -> None:
    """TC-256: last_checked 31 days ago → stale / eligible for refresh."""
    last_checked = _NOW - timedelta(days=31)
    assert (
        is_document_stale(
            last_checked,
            now=_NOW,
            stale_days=DEFAULT_FRESHNESS_STALE_DAYS,
        )
        is True
    )


def test_document_within_threshold_is_not_stale() -> None:
    """TC-256 inverse: last_checked 10 days ago → not stale."""
    last_checked = _NOW - timedelta(days=10)
    assert (
        is_document_stale(
            last_checked,
            now=_NOW,
            stale_days=DEFAULT_FRESHNESS_STALE_DAYS,
        )
        is False
    )


def test_never_checked_document_is_stale() -> None:
    """URL sources with no last_checked_at are treated as stale."""
    assert (
        is_document_stale(
            None,
            now=_NOW,
            stale_days=DEFAULT_FRESHNESS_STALE_DAYS,
        )
        is True
    )


def test_kill_switch_blocks_freshness_enqueue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Shared kill-switch blocks freshness_refresh enqueue (T128.1 / AC-FR*)."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    assert is_automations_kill_switch_on() is True
    assert (
        decide_freshness_enqueue(
            replace(_BASE_REQUEST, kill_switch=True, is_stale=True),
        )
        == "skip_kill_switch"
    )


def test_freshness_disabled_skips_scheduled_enqueue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """VECINITA_FRESHNESS_ENABLED=false → scheduled path skips."""
    monkeypatch.setenv("VECINITA_FRESHNESS_ENABLED", "false")
    assert is_freshness_enabled() is False
    assert (
        decide_freshness_enqueue(
            replace(_BASE_REQUEST, freshness_enabled=False, force=False),
        )
        == "skip_disabled"
    )


def test_per_source_refresh_disabled_skips() -> None:
    """TC-259: refresh_enabled=false → skip that source."""
    assert (
        decide_freshness_enqueue(
            replace(_BASE_REQUEST, refresh_enabled=False, is_stale=True),
        )
        == "skip_refresh_disabled"
    )


def test_not_stale_skips_scheduled_but_force_enqueues() -> None:
    """Scheduled skips non-stale; Refresh now (force) still enqueues (TC-259)."""
    assert (
        decide_freshness_enqueue(
            replace(_BASE_REQUEST, is_stale=False, force=False),
        )
        == "skip_not_stale"
    )
    assert (
        decide_freshness_enqueue(
            replace(_BASE_REQUEST, is_stale=False, force=True),
        )
        == "enqueue"
    )


@pytest.mark.parametrize(
    ("stored_hash", "fetched_hash", "expected"),
    [
        ("abc", "abc", "skip_rechunk"),
        ("abc", "def", "rechunk"),
        (None, "def", "rechunk"),
    ],
)
def test_hash_aware_refresh_decision(
    stored_hash: str | None,
    fetched_hash: str,
    expected: str,
) -> None:
    """TC-257 / AC-FR2: unchanged hash skips rechunk; changed/missing → rechunk."""
    assert (
        decide_hash_aware_refresh(
            stored_hash=stored_hash,
            fetched_hash=fetched_hash,
        )
        == expected
    )


def test_last_checked_bumps_even_when_hash_unchanged() -> None:
    """TC-257 / AC-FR2 / RD-337: bump last_checked even when hash skip."""
    decision = decide_hash_aware_refresh(stored_hash="same", fetched_hash="same")
    assert decision == "skip_rechunk"
    assert should_bump_last_checked_after_refresh(decision) is True
    assert should_bump_last_checked_after_refresh("rechunk") is True


def test_freshness_does_not_enqueue_catchup_side_effect() -> None:
    """AC-FR5 / TC-264: freshness path must not fire F75 catch-up side effects."""
    assert freshness_enqueues_catchup() is False
    decision: FreshnessEnqueueDecision = decide_freshness_enqueue(_BASE_REQUEST)
    assert decision == "enqueue"
