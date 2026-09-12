"""T127.1 — F75 catch-up enqueue policy (kill-switch, idempotency, skip-complete).

[Corpus: feature-list.md §F75]
[Spec: docs/acceptance-criteria.md §AC-AU1-AU3]
[Spec: docs/test-plan.md §TC-252-TC-254]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/config-spec.md §VECINITA_AUTOMATIONS_*]
"""

from __future__ import annotations

from dataclasses import replace
from uuid import UUID

import httpx
import pytest
from vecinita_embedding_client import EmbeddingClientError
from vecinita_ingest.scrape import ScrapeFetchError
from vecinita_shared_schemas.automations import (
    DEFAULT_AUTOMATION_JOB_MAX_RETRIES,
    DEFAULT_AUTOMATIONS_MAX_CONCURRENT,
    CatchupEnqueueDecision,
    CatchupEnqueueRequest,
    CatchupResidualListResponse,
    CatchupResidualTarget,
    EmbedStatus,
    catchup_idempotency_key,
    decide_catchup_enqueue,
    is_automations_enabled,
    is_automations_kill_switch_on,
    is_transient_automation_failure,
    parse_automation_job_max_retries,
    parse_automations_max_concurrent,
)

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
_EXPECTED_MAX_RETRIES_DEFAULT = 2
_MAX_RETRIES_CLAMP = 5

_BASE_REQUEST = CatchupEnqueueRequest(
    enabled=True,
    kill_switch=False,
    embed_status="missing",
    idempotency_key=f"{DOC_ID}:0",
    seen_keys=frozenset(),
    running_count=0,
    max_concurrent=DEFAULT_AUTOMATIONS_MAX_CONCURRENT,
)


def test_catchup_idempotency_key_joins_document_id_and_revision() -> None:
    """Idempotent key is document_id + revision (RD-335 / EV027-M1)."""
    assert catchup_idempotency_key(document_id=DOC_ID, revision=3) == (f"{DOC_ID}:3")
    assert catchup_idempotency_key(document_id=str(DOC_ID), revision="7") == (f"{DOC_ID}:7")


def test_kill_switch_env_true_blocks_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-253 / AC-AU2: kill-switch on → no enqueue even if automations enabled."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")

    assert is_automations_enabled() is True
    assert is_automations_kill_switch_on() is True
    assert (
        decide_catchup_enqueue(
            replace(
                _BASE_REQUEST,
                kill_switch=True,
                embed_status="missing",
                idempotency_key=f"{DOC_ID}:1",
            ),
        )
        == "skip_kill_switch"
    )


def test_automations_disabled_skips_enqueue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-252 / AC-AU1: master enable false → no new automation jobs."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "false")
    monkeypatch.delenv("VECINITA_AUTOMATIONS_KILL_SWITCH", raising=False)

    assert is_automations_enabled() is False
    assert is_automations_kill_switch_on() is False
    assert (
        decide_catchup_enqueue(
            replace(
                _BASE_REQUEST,
                enabled=False,
                embed_status="failed",
                idempotency_key=f"{DOC_ID}:2",
            ),
        )
        == "skip_disabled"
    )


@pytest.mark.parametrize(
    ("embed_status", "expected"),
    [
        ("complete", "skip_complete"),
        ("missing", "enqueue"),
        ("partial", "enqueue"),
        ("failed", "enqueue"),
    ],
)
def test_catchup_skips_complete_embeds_only(
    embed_status: EmbedStatus,
    expected: CatchupEnqueueDecision,
) -> None:
    """TC-254 / AC-AU3 / RD-334: catch-up only for failed/partial/missing."""
    assert (
        decide_catchup_enqueue(
            replace(_BASE_REQUEST, embed_status=embed_status, idempotency_key=f"{DOC_ID}:4"),
        )
        == expected
    )


def test_duplicate_idempotency_key_skips_enqueue() -> None:
    """TC-254: revision key dedupes — already seen → skip_duplicate."""
    key = catchup_idempotency_key(document_id=DOC_ID, revision=5)
    assert (
        decide_catchup_enqueue(
            replace(
                _BASE_REQUEST,
                embed_status="missing",
                idempotency_key=key,
                seen_keys=frozenset({key}),
            ),
        )
        == "skip_duplicate"
    )


def test_at_capacity_skips_enqueue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-AU2: concurrency cap blocks further enqueue."""
    cap = DEFAULT_AUTOMATIONS_MAX_CONCURRENT
    monkeypatch.setenv("VECINITA_AUTOMATIONS_MAX_CONCURRENT", str(cap))
    assert parse_automations_max_concurrent() == cap
    assert (
        decide_catchup_enqueue(
            replace(
                _BASE_REQUEST,
                embed_status="partial",
                idempotency_key=f"{DOC_ID}:6",
                running_count=cap,
                max_concurrent=cap,
            ),
        )
        == "skip_at_capacity"
    )


def test_kill_switch_default_false_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """config-spec default: VECINITA_AUTOMATIONS_KILL_SWITCH=false."""
    monkeypatch.delenv("VECINITA_AUTOMATIONS_KILL_SWITCH", raising=False)
    monkeypatch.delenv("VECINITA_AUTOMATIONS_ENABLED", raising=False)
    assert is_automations_kill_switch_on() is False
    assert is_automations_enabled() is False


def test_automation_job_max_retries_default_and_clamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-344 / AC-AU11: retries default to 2 and clamp to the documented 0..5 range."""
    monkeypatch.delenv("VECINITA_AUTOMATION_JOB_MAX_RETRIES", raising=False)
    assert DEFAULT_AUTOMATION_JOB_MAX_RETRIES == _EXPECTED_MAX_RETRIES_DEFAULT
    assert parse_automation_job_max_retries() == DEFAULT_AUTOMATION_JOB_MAX_RETRIES

    monkeypatch.setenv("VECINITA_AUTOMATION_JOB_MAX_RETRIES", "0")
    assert parse_automation_job_max_retries() == 0

    monkeypatch.setenv("VECINITA_AUTOMATION_JOB_MAX_RETRIES", "9")
    assert parse_automation_job_max_retries() == _MAX_RETRIES_CLAMP

    monkeypatch.setenv("VECINITA_AUTOMATION_JOB_MAX_RETRIES", "bad")
    assert parse_automation_job_max_retries() == DEFAULT_AUTOMATION_JOB_MAX_RETRIES


def test_transient_automation_failure_classifier() -> None:
    """TC-344: transient embed/transport errors retry; WAF and kill-switch blocks do not."""
    assert is_transient_automation_failure(EmbeddingClientError("/embed transport error: boom"))
    assert is_transient_automation_failure(EmbeddingClientError("/embed failed: 503 busy"))
    assert is_transient_automation_failure(httpx.ConnectError("network down"))
    assert is_transient_automation_failure(
        httpx.HTTPStatusError(
            "bad gateway",
            request=httpx.Request("GET", "https://embed.example"),
            response=httpx.Response(502),
        )
    )
    assert not is_transient_automation_failure(EmbeddingClientError("dimension mismatch"))
    assert not is_transient_automation_failure(
        ScrapeFetchError("blocked", error_code="host_waf_blocked")
    )
    assert not is_transient_automation_failure(ValueError("kill_switch enabled"))


def test_catchup_residual_list_response_schema() -> None:
    """TC-341: write-API residual scan returns document/revision/embed_status targets."""
    target = CatchupResidualTarget(
        document_id=DOC_ID,
        revision="hash-1",
        embed_status="partial",
    )
    response = CatchupResidualListResponse(items=[target], total=1)
    assert response.model_dump(mode="json") == {
        "items": [
            {
                "document_id": str(DOC_ID),
                "revision": "hash-1",
                "embed_status": "partial",
            }
        ],
        "total": 1,
    }
