"""T127.6 — F75 async catch-up enqueue triggers (job completion + CRUD).

[Corpus: feature-list.md §F75]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/decisions.md §RD-326 RD-335]
[Spec: docs/acceptance-criteria.md §AC-AU1-AU3]
[Spec: docs/test-plan.md §TC-252-TC-254]
"""

from __future__ import annotations

from uuid import UUID, uuid4

import httpx
import pytest
from vecinita_data_management_backend.catchup_triggers import targets_from_completed_job
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_internal_write_api.jobs_client import DataManagementJobsClient
from vecinita_shared_schemas.automations import (
    DEFAULT_AUTOMATIONS_MAX_CONCURRENT,
    CatchupEnqueueRequest,
    decide_catchup_enqueue,
    enqueue_catchup_targets,
)
from vecinita_shared_schemas.data_management import CreateJobRequest, JobOptions

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


def test_enqueue_automation_catchup_posts_job() -> None:
    """DataManagementJobsClient.enqueue_automation_catchup POSTs job_type + revision."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/jobs"
        body = CreateJobRequest.model_validate_json(request.content)
        assert body.options is not None
        assert body.options.job_type == "automation_catchup"
        assert body.options.document_id == DOC_ID
        assert body.options.revision == "42"
        assert body.options.embed_status == "missing"
        return httpx.Response(202, json={"job_id": str(uuid4()), "status": "pending"})

    transport = httpx.MockTransport(handler)
    client = DataManagementJobsClient(
        base_url="https://dm.example",
        proxy_key="proxy",
        http_client=httpx.Client(transport=transport, base_url="https://dm.example"),
    )
    job_id = client.enqueue_automation_catchup(
        DOC_ID,
        revision="42",
        embed_status="missing",
    )
    assert isinstance(job_id, UUID)


def test_enqueue_catchup_targets_respects_kill_switch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-253: kill-switch on → no Modal POST."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    posted: list[object] = []

    class _Client:
        def enqueue_automation_catchup(self, *args: object, **kwargs: object) -> UUID:
            posted.append((args, kwargs))
            return uuid4()

    results = enqueue_catchup_targets(
        _Client(),  # type: ignore[arg-type]
        targets=[(DOC_ID, "1", "missing")],
        enabled=True,
        kill_switch=True,
        running_count=0,
        max_concurrent=DEFAULT_AUTOMATIONS_MAX_CONCURRENT,
        seen_keys=frozenset(),
    )
    assert results == [("skip_kill_switch", None)]
    assert posted == []


def test_enqueue_catchup_targets_posts_when_residual() -> None:
    """Residual missing embed → enqueue decision + job id."""
    job_id = uuid4()

    class _Client:
        def enqueue_automation_catchup(
            self,
            document_id: UUID,
            *,
            revision: str,
            embed_status: str,
            authorization: str | None = None,
        ) -> UUID:
            assert document_id == DOC_ID
            assert revision == "9"
            assert embed_status == "partial"
            _ = authorization
            return job_id

    results = enqueue_catchup_targets(
        _Client(),  # type: ignore[arg-type]
        targets=[(DOC_ID, "9", "partial")],
        enabled=True,
        kill_switch=False,
        running_count=0,
        max_concurrent=DEFAULT_AUTOMATIONS_MAX_CONCURRENT,
        seen_keys=frozenset(),
    )
    assert results == [("enqueue", job_id)]


def test_targets_from_completed_job_skips_automation_catchup_jobs() -> None:
    """Do not re-enqueue catch-up from catch-up completion (no loop)."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options={
            "document_id": str(DOC_ID),
            "revision": "1",
            "embed_status": "missing",
        },
    )
    store.update_job(record.job_id, status="completed")
    final = store.get_job(record.job_id)
    assert final is not None
    assert targets_from_completed_job(final) == []


def test_targets_from_completed_job_retag_failed_is_residual() -> None:
    """Failed retag with document_id → catch-up target with embed_status=failed."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="retag",
        options={"document_id": str(DOC_ID)},
    )
    store.update_job(
        record.job_id,
        status="failed",
        error_code="RuntimeError",
        error_message="boom",
    )
    final = store.get_job(record.job_id)
    assert final is not None
    assert targets_from_completed_job(final) == [(DOC_ID, "0", "failed")]


def test_targets_from_completed_job_rebuild_partial_metrics() -> None:
    """Rebuild with urls_failed_embed > 0 → residual failed targets for document_ids."""
    store = InMemoryJobStore()
    doc_b = uuid4()
    record = store.create_job(
        urls=[],
        job_type="rebuild",
        options={
            "mode": "reembed",
            "document_ids": [str(DOC_ID), str(doc_b)],
        },
    )
    store.update_job(
        record.job_id,
        status="completed",
        metrics={"urls_failed_embed": 1},
    )
    final = store.get_job(record.job_id)
    assert final is not None
    targets = targets_from_completed_job(final)
    assert (DOC_ID, "0", "failed") in targets
    assert (doc_b, "0", "failed") in targets


def test_run_job_completion_enqueues_catchup_for_failed_retag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Job completion hook enqueues async catch-up for failed retag (RD-326)."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_ENABLED", "true")
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="retag",
        options={"document_id": str(DOC_ID)},
    )
    enqueued: list[tuple[UUID, str, str]] = []

    class _CapturingJobsClient:
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

    def _failing_retag(*_args: object, **_kwargs: object) -> None:
        store.update_job(
            record.job_id,
            status="failed",
            error_code="RuntimeError",
            error_message="tag boom",
        )
        msg = "tag boom"
        raise RuntimeError(msg)

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_retag_job",
        _failing_retag,
    )

    def _client_factory() -> _CapturingJobsClient:
        return _CapturingJobsClient()

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs._catchup_jobs_client",
        _client_factory,
    )

    with pytest.raises(RuntimeError, match="tag boom"):
        run_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
            tag_client=object(),  # type: ignore[arg-type]
        )

    assert enqueued == [(DOC_ID, "0", "failed")]


def test_decide_catchup_still_skips_complete_before_post() -> None:
    """CRUD path must consult policy: complete embeds never enqueue."""
    decision = decide_catchup_enqueue(
        CatchupEnqueueRequest(
            enabled=True,
            kill_switch=False,
            embed_status="complete",
            idempotency_key=f"{DOC_ID}:hash",
            seen_keys=frozenset(),
            running_count=0,
            max_concurrent=DEFAULT_AUTOMATIONS_MAX_CONCURRENT,
        )
    )
    assert decision == "skip_complete"
    # Schema still accepts the job shape for when residual work exists.
    body = CreateJobRequest(
        urls=[],
        options=JobOptions(
            job_type="automation_catchup",
            document_id=DOC_ID,
            revision="hash",
            embed_status="missing",
        ),
    )
    assert body.options is not None
    assert body.options.job_type == "automation_catchup"
