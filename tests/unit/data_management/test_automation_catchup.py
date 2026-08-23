"""T127.5 — F75 Modal DM automation_catchup worker + kill-switch/concurrency.

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/config-spec.md §VECINITA_AUTOMATIONS_*]
[Spec: docs/acceptance-criteria.md §AC-AU1-AU3]
[Spec: docs/test-plan.md §TC-252-TC-254]
"""

from __future__ import annotations

from uuid import UUID

import pytest
from vecinita_data_management_backend.automation_catchup import (
    count_running_automation_catchup,
    run_automation_catchup_job,
)
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.automations import DEFAULT_AUTOMATIONS_MAX_CONCURRENT
from vecinita_shared_schemas.data_management import CreateJobRequest

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


class _StubEmbedClient:
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 384 for _ in texts]


class _StubWriteClient:
    def with_audit_actor(
        self,
        actor_id: UUID | None,
        actor_role: str | None,
    ) -> _StubWriteClient:
        _ = (actor_id, actor_role)
        return self

    def post_audit_event(self, event: object) -> None:
        _ = event


def _catchup_options(
    *,
    embed_status: str = "missing",
    revision: str = "1",
    document_id: UUID = DOC_ID,
) -> dict[str, object]:
    return {
        "document_id": str(document_id),
        "revision": revision,
        "embed_status": embed_status,
    }


def test_count_running_automation_catchup_excludes_other_types() -> None:
    """Concurrency cap counts only running automation_catchup jobs."""
    store = InMemoryJobStore()
    running = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(revision="1"),
    )
    store.update_job(running.job_id, status="running")
    other = store.create_job(urls=["https://example.com"], job_type="ingest")
    store.update_job(other.job_id, status="running")
    pending = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(revision="2"),
    )
    assert pending.status == "pending"
    assert count_running_automation_catchup(store) == 1
    assert count_running_automation_catchup(store, exclude_job_id=running.job_id) == 0


def test_catchup_worker_kill_switch_skips_reembed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-AU2 / TC-253: kill-switch on → worker completes without re-embed."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(embed_status="missing"),
    )
    called: list[UUID] = []

    run_automation_catchup_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_catchup=called.append,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.error_code is None
    assert final.metrics == {
        "catchup_outcome": "skipped_kill_switch",
        "documents_processed": 0,
    }
    assert called == []


def test_catchup_worker_disabled_skips_reembed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-AU1 / TC-252: automations disabled → no re-embed."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "false")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(embed_status="failed"),
    )
    called: list[UUID] = []

    run_automation_catchup_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_catchup=called.append,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {
        "catchup_outcome": "skipped_disabled",
        "documents_processed": 0,
    }
    assert called == []


def test_catchup_worker_complete_embed_skips_reembed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-AU3 / TC-254 / RD-334: complete embeds are not re-embedded."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(embed_status="complete"),
    )
    called: list[UUID] = []

    run_automation_catchup_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_catchup=called.append,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {
        "catchup_outcome": "skipped_complete",
        "documents_processed": 0,
    }
    assert called == []


def test_catchup_worker_at_capacity_skips_reembed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AC-AU2: at MAX_CONCURRENT → skip without re-embed."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    monkeypatch.setenv(
        "VECINITA_AUTOMATIONS_MAX_CONCURRENT",
        str(DEFAULT_AUTOMATIONS_MAX_CONCURRENT),
    )
    store = InMemoryJobStore()
    for index in range(DEFAULT_AUTOMATIONS_MAX_CONCURRENT):
        peer = store.create_job(
            urls=[],
            job_type="automation_catchup",
            options=_catchup_options(revision=str(index), embed_status="partial"),
        )
        store.update_job(peer.job_id, status="running")

    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(revision="99", embed_status="missing"),
    )
    called: list[UUID] = []

    run_automation_catchup_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_catchup=called.append,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {
        "catchup_outcome": "skipped_at_capacity",
        "documents_processed": 0,
    }
    assert called == []


def test_catchup_worker_residual_calls_reembed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Residual missing/partial/failed → perform catch-up re-embed once."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(embed_status="partial", revision="7"),
    )
    called: list[UUID] = []

    run_automation_catchup_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
        perform_catchup=called.append,
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.error_code is None
    assert final.metrics == {
        "catchup_outcome": "reembedded",
        "documents_processed": 1,
    }
    assert called == [DOC_ID]


def test_run_job_dispatches_automation_catchup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run_job routes job_type=automation_catchup to the catch-up worker."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(embed_status="missing"),
    )
    dispatched: list[UUID] = []

    def _fake_catchup(job_id: UUID, **kwargs: object) -> None:
        store_obj = kwargs["store"]
        assert isinstance(store_obj, InMemoryJobStore)
        dispatched.append(job_id)
        store_obj.update_job(
            job_id,
            status="completed",
            metrics={"catchup_outcome": "reembedded", "documents_processed": 1},
        )

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_automation_catchup_job",
        _fake_catchup,
    )

    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
    )

    assert dispatched == [record.job_id]
    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"


def test_create_job_request_accepts_automation_catchup() -> None:
    """POST /jobs schema accepts job_type=automation_catchup with document_id."""
    body = CreateJobRequest.model_validate(
        {
            "urls": [],
            "options": {
                "job_type": "automation_catchup",
                "document_id": str(DOC_ID),
                "revision": "3",
                "embed_status": "missing",
            },
        }
    )
    assert body.options is not None
    assert body.options.job_type == "automation_catchup"
    assert body.options.document_id == DOC_ID
    assert body.options.revision == "3"
    assert body.options.embed_status == "missing"


def test_create_job_request_requires_document_id_for_catchup() -> None:
    """automation_catchup without document_id is rejected at the API schema."""
    with pytest.raises(ValueError, match="document_id"):
        CreateJobRequest.model_validate(
            {
                "urls": [],
                "options": {"job_type": "automation_catchup", "revision": "1"},
            }
        )


def test_catchup_missing_job_raises_key_error() -> None:
    """Unknown job_id → KeyError before any catch-up work."""
    store = InMemoryJobStore()
    with pytest.raises(KeyError):
        run_automation_catchup_job(
            UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"),
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
        )


def test_catchup_wrong_job_type_raises() -> None:
    """Non-catch-up job_type → ValueError."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com"], job_type="ingest")
    with pytest.raises(ValueError, match="not an automation_catchup"):
        run_automation_catchup_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
        )


def test_catchup_options_validation_errors() -> None:
    """Missing/invalid options raise ValueError with clear messages."""
    store = InMemoryJobStore()
    cases: list[tuple[dict[str, object], str]] = [
        ({"revision": "1", "embed_status": "missing"}, "document_id"),
        ({"document_id": str(DOC_ID), "embed_status": "missing"}, "revision"),
        (
            {"document_id": str(DOC_ID), "revision": "1", "embed_status": "bogus"},
            "embed_status",
        ),
        (
            {"document_id": str(DOC_ID), "revision": "1", "embed_status": "   "},
            "embed_status",
        ),
    ]
    for options, match in cases:
        record = store.create_job(
            urls=[],
            job_type="automation_catchup",
            options=options,
        )
        with pytest.raises(ValueError, match=match):
            run_automation_catchup_job(
                record.job_id,
                store=store,
                embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
                write_client=_StubWriteClient(),  # type: ignore[arg-type]
            )


def test_catchup_default_perform_calls_reembed_documents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When perform_catchup is omitted, reembed_documents runs for the document."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(embed_status="missing"),
    )
    called: list[list[UUID]] = []

    def _fake_reembed(
        document_ids: list[UUID],
        *,
        write_client: object,
        embed_client: object,
        fetch_document: object = None,
    ) -> None:
        _ = (write_client, embed_client, fetch_document)
        called.append(list(document_ids))

    monkeypatch.setattr(
        "vecinita_data_management_backend.automation_catchup.reembed_documents",
        _fake_reembed,
    )

    run_automation_catchup_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
    )

    assert called == [[DOC_ID]]
    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {
        "catchup_outcome": "reembedded",
        "documents_processed": 1,
    }


def test_catchup_perform_failure_marks_job_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Exceptions during re-embed mark the job failed and re-raise."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options=_catchup_options(embed_status="failed"),
    )

    def _boom(_document_id: UUID) -> None:
        msg = "embed boom"
        raise RuntimeError(msg)

    with pytest.raises(RuntimeError, match="embed boom"):
        run_automation_catchup_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
            perform_catchup=_boom,
        )

    final = store.get_job(record.job_id)
    assert final is not None
    assert final.status == "failed"
    assert final.error_code == "RuntimeError"
    assert final.error_message == "embed boom"
    assert final.metrics == {
        "catchup_outcome": "failed",
        "documents_processed": 0,
    }
