"""T129.4 coverage — finetune_train stub worker + run_job dispatch (F77 / TC-260/263).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/test-plan.md §TC-260 §TC-263]
"""

from __future__ import annotations

from http import HTTPStatus
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from vecinita_data_management_backend.app import create_app
from vecinita_data_management_backend.finetune_train import run_finetune_train_job
from vecinita_data_management_backend.jobs import run_job
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.auth import AuthPrincipal, get_principal, reset_auth_config_for_tests

from tests.helpers.json_response import json_str, response_json_object

_ADMIN = AuthPrincipal(sub=UUID("11111111-1111-4111-8111-111111111111"), role="admin")


@pytest.fixture(autouse=True)
def _disable_auth_required(monkeypatch: pytest.MonkeyPatch) -> None:  # pyright: ignore[reportUnusedFunction]
    """Reset FT env + auth for isolated unit tests."""
    reset_auth_config_for_tests()
    monkeypatch.setenv("VECINITA_AUTH_REQUIRED", "false")
    monkeypatch.delenv("VECINITA_AUTOMATIONS_KILL_SWITCH", raising=False)
    monkeypatch.delenv("VECINITA_FINETUNE_MAX_CONCURRENT", raising=False)
    monkeypatch.delenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", raising=False)


def _ft_job(
    store: InMemoryJobStore,
    *,
    approved: bool = True,
    status: str = "pending",
) -> UUID:
    record = store.create_job(
        urls=[],
        job_type="finetune_train",
        options={"approved": approved},
    )
    if status != "pending":
        store.update_job(record.job_id, status=status)
    return record.job_id


class _StubWrite:
    def with_audit_actor(self, *_a: object, **_k: object) -> _StubWrite:
        return self

    def post_audit_event(self, *_a: object, **_k: object) -> None:
        return None


def test_run_finetune_train_job_missing_raises() -> None:
    """Missing job id raises KeyError."""
    store = InMemoryJobStore()
    with pytest.raises(KeyError):
        run_finetune_train_job(uuid4(), store=store)


def test_run_finetune_train_job_wrong_type_raises() -> None:
    """Non-finetune job_type is rejected."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com"], job_type="ingest")
    with pytest.raises(ValueError, match="job_type"):
        run_finetune_train_job(record.job_id, store=store)


def test_run_finetune_train_skips_when_not_approved() -> None:
    """TC-260: unapproved train completes with skip_pending_approve."""
    store = InMemoryJobStore()
    job_id = _ft_job(store, approved=False)
    run_finetune_train_job(job_id, store=store)
    final = store.get_job(job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {"finetune_outcome": "skip_pending_approve"}


def test_run_finetune_train_skips_on_kill_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-263: kill-switch blocks train start."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    store = InMemoryJobStore()
    job_id = _ft_job(store, approved=True)
    run_finetune_train_job(job_id, store=store)
    final = store.get_job(job_id)
    assert final is not None
    assert final.metrics == {"finetune_outcome": "skip_kill_switch"}


def test_run_finetune_train_skips_at_concurrency_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-263: concurrency cap blocks a second running train."""
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_CONCURRENT", "1")
    store = InMemoryJobStore()
    running = store.create_job(
        urls=[],
        job_type="finetune_train",
        options={"approved": True},
    )
    store.update_job(running.job_id, status="running")
    job_id = _ft_job(store, approved=True)
    run_finetune_train_job(job_id, store=store)
    final = store.get_job(job_id)
    assert final is not None
    assert final.metrics == {"finetune_outcome": "skip_at_capacity"}


def test_run_finetune_train_skips_daily_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-263: daily run cap blocks further starts."""
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", "1")
    store = InMemoryJobStore()
    store.create_job(urls=["https://example.com/x"], job_type="ingest")
    prior = store.create_job(
        urls=[],
        job_type="finetune_train",
        options={"approved": True},
    )
    store.update_job(prior.job_id, status="completed", metrics={"finetune_outcome": "stub"})
    pending_other = store.create_job(
        urls=[],
        job_type="finetune_train",
        options={"approved": True},
    )
    assert pending_other.status == "pending"
    job_id = _ft_job(store, approved=True)
    run_finetune_train_job(job_id, store=store)
    final = store.get_job(job_id)
    assert final is not None
    assert final.metrics == {"finetune_outcome": "skip_daily_cap"}


def test_kill_switch_false_for_non_truthy_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kill-switch ignores non-truthy values so approved trains can stub-start."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "false")
    store = InMemoryJobStore()
    job_id = _ft_job(store, approved=True)
    run_finetune_train_job(job_id, store=store)
    final = store.get_job(job_id)
    assert final is not None
    assert final.metrics == {"finetune_outcome": "stub_ready_for_train"}


def test_run_finetune_train_stub_ready_when_allowed() -> None:
    """Allowed train marks stub_ready_for_train until T129.5 GPU worker."""
    store = InMemoryJobStore()
    job_id = _ft_job(store, approved=True)
    run_finetune_train_job(job_id, store=store)
    final = store.get_job(job_id)
    assert final is not None
    assert final.status == "completed"
    assert final.metrics == {"finetune_outcome": "stub_ready_for_train"}


def test_run_job_dispatches_finetune_train(monkeypatch: pytest.MonkeyPatch) -> None:
    """run_job routes job_type=finetune_train to the FT worker."""
    store = InMemoryJobStore()
    job_id = _ft_job(store, approved=True)
    called: list[UUID] = []

    def _fake(job_id: UUID, *, store: InMemoryJobStore) -> None:
        called.append(job_id)
        store.update_job(job_id, status="completed", metrics={"finetune_outcome": "stub"})

    monkeypatch.setattr(
        "vecinita_data_management_backend.jobs.run_finetune_train_job",
        _fake,
    )
    run_job(
        job_id,
        store=store,
        embed_client=object(),  # type: ignore[arg-type]
        write_client=_StubWrite(),  # type: ignore[arg-type]
    )
    assert called == [job_id]


def test_approve_non_pending_returns_409() -> None:
    """Approve rejects finetune jobs that are no longer pending."""
    store = InMemoryJobStore()
    job_id = _ft_job(store, approved=False, status="running")
    app = create_app(store=store, require_proxy_auth=False, pipeline_runner=None)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)
    response = client.post(f"/jobs/{job_id}/approve")
    assert response.status_code == HTTPStatus.CONFLICT


def test_approve_without_runner_still_sets_approved() -> None:
    """Approve without pipeline_runner still sets approved=true."""
    store = InMemoryJobStore()
    app = create_app(store=store, require_proxy_auth=False, pipeline_runner=None)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)
    create = client.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    job_id = UUID(json_str(response_json_object(create), "job_id"))
    response = client.post(f"/jobs/{job_id}/approve")
    assert response.status_code == HTTPStatus.OK
    assert response_json_object(response)["approved"] is True
    record = store.get_job(job_id)
    assert record is not None
    assert record.status == "pending"


def test_retry_finetune_train_requires_fresh_approve() -> None:
    """Retry resets approved and does not auto-start the runner."""
    store = InMemoryJobStore()
    started: list[UUID] = []

    def _runner(job_id: UUID) -> None:
        started.append(job_id)

    app = create_app(store=store, require_proxy_auth=False, pipeline_runner=_runner)
    app.dependency_overrides[get_principal] = lambda: _ADMIN
    client = TestClient(app)
    create = client.post("/jobs", json={"options": {"job_type": "finetune_train"}})
    job_id = UUID(json_str(response_json_object(create), "job_id"))
    store.update_job(job_id, status="failed", options_patch={"approved": True})

    retry = client.post(f"/jobs/{job_id}/retry")
    assert retry.status_code == HTTPStatus.ACCEPTED
    new_id = UUID(json_str(response_json_object(retry), "job_id"))
    new_record = store.get_job(new_id)
    assert new_record is not None
    assert new_record.job_type == "finetune_train"
    assert new_record.options.get("approved") is False
    assert new_id not in started
