"""T129.5 — run_finetune_train_job: caps + real train invoker (F77 / TC-263).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/test-plan.md §TC-260 §TC-263]
[Spec: docs/acceptance-criteria.md §AC-FT1 §AC-FT2 §AC-FT7]
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from types import ModuleType
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from vecinita_data_management_backend.finetune_train import (
    resolve_default_train_invoker,
    run_finetune_train_job,
)
from vecinita_data_management_backend.store import InMemoryJobStore

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


_CHUNK_OPTS: Mapping[str, object] = {
    "approved": True,
    "chunks": [
        {
            "chunk_id": "c1",
            "text": "Food banks in Providence list hours on Fridays.",
            "title": "Food",
        },
    ],
}


def test_run_finetune_train_job_wrong_type_raises() -> None:
    """Reject non-finetune job types at the worker boundary."""
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com"], job_type="ingest")
    with pytest.raises(ValueError, match="finetune_train"):
        run_finetune_train_job(record.job_id, store=store)


def test_run_finetune_train_job_missing_job_raises() -> None:
    """Missing job id raises KeyError."""
    store = InMemoryJobStore()
    with pytest.raises(KeyError):
        run_finetune_train_job(uuid4(), store=store)


def test_run_finetune_train_job_skip_pending_approve() -> None:
    """TC-260: without approve, train does not start."""
    store = InMemoryJobStore()
    record = store.create_job(
        urls=[],
        job_type="finetune_train",
        options={"approved": False, "chunks": _CHUNK_OPTS["chunks"]},
    )
    run_finetune_train_job(record.job_id, store=store)
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.metrics == {"finetune_outcome": "skip_pending_approve"}


def test_run_finetune_train_job_skip_kill_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-263: kill-switch blocks GPU start after approve."""
    monkeypatch.setenv("VECINITA_AUTOMATIONS_KILL_SWITCH", "true")
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="finetune_train", options=dict(_CHUNK_OPTS))
    run_finetune_train_job(record.job_id, store=store)
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.metrics == {"finetune_outcome": "skip_kill_switch"}


def test_run_finetune_train_job_skip_at_capacity(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-263: concurrent FT cap blocks a second start."""
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_CONCURRENT", "1")
    store = InMemoryJobStore()
    running = store.create_job(urls=[], job_type="finetune_train", options={"approved": True})
    store.update_job(running.job_id, status="running")
    pending = store.create_job(urls=[], job_type="finetune_train", options=dict(_CHUNK_OPTS))
    run_finetune_train_job(pending.job_id, store=store)
    updated = store.get_job(pending.job_id)
    assert updated is not None
    assert updated.metrics == {"finetune_outcome": "skip_at_capacity"}


def test_run_finetune_train_job_skip_daily_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-263: daily run cap blocks further starts."""
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", "1")
    store = InMemoryJobStore()
    prior = store.create_job(urls=[], job_type="finetune_train", options={"approved": True})
    store.update_job(prior.job_id, status="completed")
    assert prior.updated_at.astimezone(UTC).date() == datetime.now(UTC).date()
    pending = store.create_job(urls=[], job_type="finetune_train", options=dict(_CHUNK_OPTS))
    run_finetune_train_job(pending.job_id, store=store)
    updated = store.get_job(pending.job_id)
    assert updated is not None
    assert updated.metrics == {"finetune_outcome": "skip_daily_cap"}


def test_run_finetune_train_job_invokes_train_and_records_adapter() -> None:
    """T129.5: on start, call train invoker and persist adapter_id (not stub_ready)."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="finetune_train", options=dict(_CHUNK_OPTS))
    payloads: list[dict[str, object]] = []

    def _invoker(payload: dict[str, object]) -> dict[str, object]:
        payloads.append(payload)
        return {
            "adapter_id": "adapter-test-1",
            "adapter_path": "/adapters/adapter-test-1",
            "pair_count": 1,
            "base_model_id": "qwen2.5:1.5b-instruct",
            "status": "completed",
        }

    run_finetune_train_job(record.job_id, store=store, train_invoker=_invoker)
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.metrics == {
        "finetune_outcome": "trained",
        "adapter_id": "adapter-test-1",
        "adapter_path": "/adapters/adapter-test-1",
        "pair_count": 1,
        "base_model_id": "qwen2.5:1.5b-instruct",
    }
    assert len(payloads) == 1
    assert payloads[0]["job_id"] == str(record.job_id)


def test_run_finetune_train_job_marks_failed_when_invoker_raises() -> None:
    """Train invoker failure marks the job failed with train_failed outcome."""
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="finetune_train", options=dict(_CHUNK_OPTS))

    def _boom(_payload: dict[str, object]) -> dict[str, object]:
        msg = "GPU OOM"
        raise RuntimeError(msg)

    with pytest.raises(RuntimeError, match="GPU OOM"):
        run_finetune_train_job(record.job_id, store=store, train_invoker=_boom)
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_message == "GPU OOM"
    assert updated.metrics == {"finetune_outcome": "train_failed"}


def test_daily_cap_ignores_yesterday_starts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Runs from a prior UTC day do not count toward today's cap."""
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", "1")
    store = InMemoryJobStore()
    old = store.create_job(urls=[], job_type="finetune_train", options={"approved": True})
    store.update_job(old.job_id, status="completed")
    yesterday = datetime.now(UTC) - timedelta(days=1)
    mutated = store.get_job(old.job_id)
    assert mutated is not None
    mutated.updated_at = yesterday

    pending = store.create_job(urls=[], job_type="finetune_train", options=dict(_CHUNK_OPTS))

    def _invoker(_payload: dict[str, object]) -> dict[str, object]:
        return {
            "adapter_id": "adapter-ok",
            "adapter_path": "/adapters/adapter-ok",
            "pair_count": 1,
            "base_model_id": "qwen2.5:1.5b-instruct",
            "status": "completed",
        }

    run_finetune_train_job(pending.job_id, store=store, train_invoker=_invoker)
    updated = store.get_job(pending.job_id)
    assert updated is not None
    assert updated.metrics is not None
    assert updated.metrics["finetune_outcome"] == "trained"


def test_daily_cap_ignores_non_finetune_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Daily counter skips non-finetune job types when scanning the store."""
    monkeypatch.setenv("VECINITA_FINETUNE_MAX_RUNS_PER_DAY", "1")
    store = InMemoryJobStore()
    store.create_job(urls=["https://example.com"], job_type="ingest")
    pending = store.create_job(urls=[], job_type="finetune_train", options=dict(_CHUNK_OPTS))

    def _invoker(_payload: dict[str, object]) -> dict[str, object]:
        return {
            "adapter_id": "adapter-mix",
            "adapter_path": "/adapters/adapter-mix",
            "pair_count": 1,
            "base_model_id": "qwen2.5:1.5b-instruct",
            "status": "completed",
        }

    run_finetune_train_job(pending.job_id, store=store, train_invoker=_invoker)
    updated = store.get_job(pending.job_id)
    assert updated is not None
    assert updated.metrics is not None
    assert updated.metrics["finetune_outcome"] == "trained"


def test_default_train_invoker_writes_local_adapter(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Default invoker runs train core locally (no Modal) into adapters dir."""
    monkeypatch.delenv("VECINITA_FINETUNE_USE_MODAL", raising=False)
    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTERS_DIR", str(tmp_path / "adapters"))
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="finetune_train", options=dict(_CHUNK_OPTS))
    run_finetune_train_job(record.job_id, store=store)
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.status == "completed"
    assert updated.metrics is not None
    assert updated.metrics["finetune_outcome"] == "trained"
    adapter_id = str(updated.metrics["adapter_id"])
    assert (tmp_path / "adapters" / adapter_id / "run_metadata.json").is_file()


def test_resolve_default_train_invoker_modal_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """VECINITA_FINETUNE_USE_MODAL selects Modal Function invoker."""
    monkeypatch.setenv("VECINITA_FINETUNE_USE_MODAL", "1")
    invoker = resolve_default_train_invoker()
    assert invoker.__name__ == "_modal_train_invoker"
    monkeypatch.setenv("VECINITA_FINETUNE_USE_MODAL", "0")
    local = resolve_default_train_invoker()
    assert local.__name__ == "_default_train_invoker"


def test_modal_train_invoker_rejects_non_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Modal train_lora must return a JSON object."""

    class _Fn:
        @staticmethod
        def remote(_payload: dict[str, object]) -> list[str]:
            return ["not-a-dict"]

    fake = ModuleType("modal")

    class Function:
        @staticmethod
        def from_name(_app: str, _name: str) -> _Fn:
            return _Fn()

    fake.Function = Function  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "modal", fake)
    monkeypatch.setenv("VECINITA_FINETUNE_USE_MODAL", "1")
    invoker = resolve_default_train_invoker()

    with pytest.raises(TypeError, match="non-object"):
        invoker({"job_id": "x"})


def test_modal_train_invoker_returns_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path: Modal Function.remote returns adapter payload."""
    pair_count = 2

    class _Fn:
        @staticmethod
        def remote(payload: dict[str, object]) -> dict[str, object]:
            return {
                "adapter_id": f"adapter-{payload['job_id']}",
                "adapter_path": "/adapters/x",
                "pair_count": pair_count,
                "base_model_id": "qwen2.5:1.5b-instruct",
                "status": "completed",
            }

    fake = ModuleType("modal")

    class Function:
        @staticmethod
        def from_name(_app: str, _name: str) -> _Fn:
            return _Fn()

    fake.Function = Function  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "modal", fake)
    monkeypatch.setenv("VECINITA_FINETUNE_USE_MODAL", "1")
    invoker = resolve_default_train_invoker()

    result = invoker({"job_id": "abc"})
    assert result["adapter_id"] == "adapter-abc"
    assert result["pair_count"] == pair_count


def test_default_invoker_uses_tempdir_without_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When adapters dir env is unset, local invoker still completes train."""
    monkeypatch.delenv("VECINITA_FINETUNE_USE_MODAL", raising=False)
    monkeypatch.delenv("VECINITA_FINETUNE_ADAPTERS_DIR", raising=False)
    store = InMemoryJobStore()
    record = store.create_job(urls=[], job_type="finetune_train", options=dict(_CHUNK_OPTS))
    run_finetune_train_job(record.job_id, store=store)
    updated = store.get_job(record.job_id)
    assert updated is not None
    assert updated.metrics is not None
    assert updated.metrics["finetune_outcome"] == "trained"
    assert str(updated.metrics["adapter_id"]).startswith("adapter-")
