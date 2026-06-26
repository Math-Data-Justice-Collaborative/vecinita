"""Job stores for Modal ASGI — in-memory for tests, shared dict for production."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import TypedDict
from uuid import UUID, uuid4

from vecinita_shared_schemas.data_management import Job


@dataclass
class JobRecord:
    """Internal ingest or retag job state before API schema mapping."""

    job_id: UUID
    status: str
    urls: list[str]
    job_type: str = "ingest"
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    options: dict[str, object] = field(default_factory=dict)


class JobPayload(TypedDict):
    job_id: str
    status: str
    urls: list[str]
    job_type: str
    error_code: str | None
    error_message: str | None
    created_at: str
    updated_at: str
    options: dict[str, object]


class JobStore:
    """Persistence interface for ingest job lifecycle."""

    def create_job(
        self,
        urls: list[str],
        options: dict[str, object] | None = None,
        *,
        job_type: str = "ingest",
    ) -> JobRecord:
        raise NotImplementedError

    def get_job(self, job_id: UUID) -> JobRecord | None:
        raise NotImplementedError

    def update_job(
        self,
        job_id: UUID,
        *,
        status: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> JobRecord:
        raise NotImplementedError

    def list_jobs(self) -> list[JobRecord]:
        """Return all jobs, newest first."""
        raise NotImplementedError


def _record_to_payload(record: JobRecord) -> JobPayload:
    return {
        "job_id": str(record.job_id),
        "status": record.status,
        "urls": record.urls,
        "job_type": record.job_type,
        "error_code": record.error_code,
        "error_message": record.error_message,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
        "options": record.options,
    }


def _payload_to_record(payload: JobPayload) -> JobRecord:
    return JobRecord(
        job_id=UUID(str(payload["job_id"])),
        status=str(payload["status"]),
        urls=[str(url) for url in payload["urls"]],
        job_type=str(payload.get("job_type") or "ingest"),
        error_code=payload.get("error_code"),
        error_message=payload.get("error_message"),
        created_at=datetime.fromisoformat(str(payload["created_at"])),
        updated_at=datetime.fromisoformat(str(payload["updated_at"])),
        options=dict(payload.get("options") or {}),
    )


class DictJobStore(JobStore):
    """Job store backed by a shared mapping (e.g. modal.Dict) visible across Modal workers."""

    def __init__(self, backing: MutableMapping[str, JobPayload]) -> None:
        self._jobs = backing

    def create_job(
        self,
        urls: list[str],
        options: dict[str, object] | None = None,
        *,
        job_type: str = "ingest",
    ) -> JobRecord:
        record = JobRecord(
            job_id=uuid4(),
            status="pending",
            urls=urls,
            job_type=job_type,
            options=options or {},
        )
        self._jobs[str(record.job_id)] = _record_to_payload(record)
        return record

    def get_job(self, job_id: UUID) -> JobRecord | None:
        payload = self._jobs.get(str(job_id))
        if payload is None:
            return None
        return _payload_to_record(payload)

    def update_job(
        self,
        job_id: UUID,
        *,
        status: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> JobRecord:
        key = str(job_id)
        payload = self._jobs.get(key)
        if payload is None:
            raise KeyError(job_id)
        record = _payload_to_record(payload)
        if status is not None:
            record.status = status
        if error_code is not None:
            record.error_code = error_code
        if error_message is not None:
            record.error_message = error_message
        record.updated_at = datetime.now(UTC)
        self._jobs[key] = _record_to_payload(record)
        return record

    def list_jobs(self) -> list[JobRecord]:
        records = [_payload_to_record(payload) for payload in self._jobs.values()]
        records.sort(key=lambda record: record.created_at, reverse=True)
        return records


class InMemoryJobStore(JobStore):
    """Thread-safe in-process job store for local tests and single-worker runs."""

    def __init__(self) -> None:
        self._jobs: dict[UUID, JobRecord] = {}
        self._lock = Lock()

    def create_job(
        self,
        urls: list[str],
        options: dict[str, object] | None = None,
        *,
        job_type: str = "ingest",
    ) -> JobRecord:
        record = JobRecord(
            job_id=uuid4(),
            status="pending",
            urls=urls,
            job_type=job_type,
            options=options or {},
        )
        with self._lock:
            self._jobs[record.job_id] = record
        return record

    def get_job(self, job_id: UUID) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(
        self,
        job_id: UUID,
        *,
        status: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> JobRecord:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(job_id)
            if status is not None:
                record.status = status
            if error_code is not None:
                record.error_code = error_code
            if error_message is not None:
                record.error_message = error_message
            record.updated_at = datetime.now(UTC)
            return record

    def list_jobs(self) -> list[JobRecord]:
        with self._lock:
            records = list(self._jobs.values())
        records.sort(key=lambda record: record.created_at, reverse=True)
        return records


def job_record_to_schema(record: JobRecord) -> Job:
    """Map a store record to the public Job API model."""
    return Job(
        job_id=record.job_id,
        status=record.status,  # type: ignore[arg-type]
        job_type=record.job_type,  # type: ignore[arg-type]
        urls=record.urls,  # type: ignore[arg-type]
        error_code=record.error_code,
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
