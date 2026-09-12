"""EV-038 bounded transient retries for automation Modal jobs.

[Corpus: feature-list.md §F78-F79]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/test-plan.md §TC-344]
"""

from __future__ import annotations

from uuid import UUID

import pytest
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_embedding_client import EmbeddingClientError
from vecinita_ingest.scrape import ScrapeFetchError

DOC_ID = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
_EXPECTED_RETRY_ATTEMPTS = 2


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


def test_run_job_retries_transient_automation_catchup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-344 / AC-AU11: transient automation_catchup errors retry within the cap."""
    monkeypatch.setenv("VECINITA_AUTOMATION_JOB_MAX_RETRIES", "2")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="automation_catchup",
        options={"document_id": str(DOC_ID), "revision": "rev-1", "embed_status": "missing"},
    )
    attempts: list[UUID] = []

    def _flaky(job_id: UUID, **kwargs: object) -> None:
        store_obj = kwargs["store"]
        assert isinstance(store_obj, InMemoryJobStore)
        attempts.append(job_id)
        if len(attempts) == 1:
            _ = store_obj.update_job(
                job_id,
                status="failed",
                error_code="EmbeddingClientError",
                error_message="transport error",
            )
            msg = "/embed transport error: timeout"
            raise EmbeddingClientError(msg)
        _ = store_obj.update_job(
            job_id,
            status="completed",
            metrics={"catchup_outcome": "reembedded", "documents_processed": 1},
        )

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_automation_catchup_job",
        _flaky,
    )

    run_job(
        record.job_id,
        store=store,
        embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
        write_client=_StubWriteClient(),  # type: ignore[arg-type]
    )

    final = store.get_job(record.job_id)
    assert final is not None
    assert len(attempts) == _EXPECTED_RETRY_ATTEMPTS
    assert final.status == "completed"
    assert final.metrics == {"catchup_outcome": "reembedded", "documents_processed": 1}


def test_run_job_does_not_retry_waf_quarantine_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-344: hard WAF quarantine errors are not transient retry candidates."""
    monkeypatch.setenv("VECINITA_AUTOMATION_JOB_MAX_RETRIES", "2")
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="freshness_refresh",
        options={"document_id": str(DOC_ID), "refresh_enabled": True, "is_stale": True},
    )
    attempts: list[UUID] = []

    def _waf(job_id: UUID, **kwargs: object) -> None:
        attempts.append(job_id)
        store_obj = kwargs["store"]
        assert isinstance(store_obj, InMemoryJobStore)
        _ = store_obj.update_job(job_id, status="failed", error_code="ScrapeFetchError")
        msg = "blocked"
        raise ScrapeFetchError(msg, error_code="host_waf_blocked")

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_freshness_refresh_job",
        _waf,
    )

    with pytest.raises(ScrapeFetchError, match="blocked"):
        run_job(
            record.job_id,
            store=store,
            embed_client=_StubEmbedClient(),  # type: ignore[arg-type]
            write_client=_StubWriteClient(),  # type: ignore[arg-type]
        )

    assert attempts == [record.job_id]
