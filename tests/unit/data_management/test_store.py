"""Unit tests for vecinita_data_management_backend.store."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import cast
from uuid import uuid4

import pytest
from vecinita_data_management_backend.store import (
    DictJobStore,
    InMemoryJobStore,
    JobPayload,
    JobStore,
    job_record_to_schema,
)


def test_job_store_base_methods_raise_not_implemented() -> None:
    store = JobStore()

    with pytest.raises(NotImplementedError):
        store.create_job(urls=["https://example.com"])

    with pytest.raises(NotImplementedError):
        store.get_job(uuid4())

    with pytest.raises(NotImplementedError):
        store.update_job(uuid4(), status="failed")

    with pytest.raises(NotImplementedError):
        store.list_jobs()


def test_in_memory_list_jobs_sorted_newest_first() -> None:
    store = InMemoryJobStore()
    first = store.create_job(urls=["https://example.com/1"])
    second = store.create_job(urls=["https://example.com/2"])
    store.update_job(second.job_id, status="completed")

    jobs = store.list_jobs()

    assert {job.job_id for job in jobs} == {first.job_id, second.job_id}
    # Sorted descending by created_at (newest first).
    assert all(jobs[i].created_at >= jobs[i + 1].created_at for i in range(len(jobs) - 1))


def test_dict_list_jobs_sorted_newest_first() -> None:
    backing: dict[str, JobPayload] = {}
    store = DictJobStore(cast(MutableMapping[str, JobPayload], backing))
    first = store.create_job(urls=["https://example.com/a"])
    second = store.create_job(urls=["https://example.com/b"], job_type="retag")

    jobs = store.list_jobs()

    assert {job.job_id for job in jobs} == {first.job_id, second.job_id}
    assert all(jobs[i].created_at >= jobs[i + 1].created_at for i in range(len(jobs) - 1))
    retag = next(job for job in jobs if job.job_type == "retag")
    assert retag.job_id == second.job_id


def test_in_memory_job_store_lifecycle() -> None:
    store = InMemoryJobStore()
    record = store.create_job(
        urls=["https://example.com/a"],
        options={"chunk_size_tokens": 128},
        job_type="ingest",
    )

    fetched = store.get_job(record.job_id)
    assert fetched is not None
    assert fetched.urls == ["https://example.com/a"]
    assert fetched.options["chunk_size_tokens"] == 128

    updated = store.update_job(record.job_id, status="running", error_code="X")
    assert updated.status == "running"
    assert updated.error_code == "X"


def test_in_memory_update_job_raises_for_missing_id() -> None:
    store = InMemoryJobStore()

    with pytest.raises(KeyError):
        store.update_job(uuid4(), status="failed")


def test_dict_job_store_round_trip() -> None:
    backing: dict[str, JobPayload] = {}
    store = DictJobStore(cast(MutableMapping[str, JobPayload], backing))
    record = store.create_job(urls=["https://example.com/b"], job_type="retag")

    fetched = store.get_job(record.job_id)
    assert fetched is not None
    assert fetched.job_type == "retag"

    updated = store.update_job(
        record.job_id,
        status="completed",
        error_message="done",
    )
    assert updated.status == "completed"
    assert updated.error_message == "done"
    assert str(record.job_id) in backing


def test_dict_job_store_update_raises_for_missing_id() -> None:
    store = DictJobStore(cast(MutableMapping[str, JobPayload], {}))

    with pytest.raises(KeyError):
        store.update_job(uuid4(), status="failed")


def test_dict_job_store_get_job_returns_none_for_missing() -> None:
    store = DictJobStore(cast(MutableMapping[str, JobPayload], {}))

    assert store.get_job(uuid4()) is None


def test_dict_job_store_update_only_error_code() -> None:
    backing: dict[str, JobPayload] = {}
    store = DictJobStore(cast(MutableMapping[str, JobPayload], backing))
    record = store.create_job(urls=["https://example.com/f"])

    updated = store.update_job(record.job_id, error_code="Timeout")

    assert updated.error_code == "Timeout"
    assert updated.status == "pending"


def test_dict_job_store_update_only_status() -> None:
    backing: dict[str, JobPayload] = {}
    store = DictJobStore(cast(MutableMapping[str, JobPayload], backing))
    record = store.create_job(urls=["https://example.com/d"])

    updated = store.update_job(record.job_id, status="running")

    assert updated.status == "running"
    assert updated.error_code is None


def test_in_memory_update_only_error_message() -> None:
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/e"])

    updated = store.update_job(record.job_id, error_message="retry later")

    assert updated.error_message == "retry later"
    assert updated.status == "pending"


def test_job_record_to_schema_maps_fields() -> None:
    store = InMemoryJobStore()
    record = store.create_job(urls=["https://example.com/c"])

    schema = job_record_to_schema(record)

    assert schema.job_id == record.job_id
    assert schema.status == "pending"
    assert str(schema.urls[0]) == record.urls[0]
