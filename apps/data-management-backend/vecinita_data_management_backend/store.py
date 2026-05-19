"""In-memory job store for Modal ASGI (v1; durable jobs via DO in future)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from uuid import UUID, uuid4

from vecinita_shared_schemas.data_management import Job


@dataclass
class JobRecord:
    job_id: UUID
    status: str
    urls: list[str]
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    options: dict[str, object] = field(default_factory=dict)


class JobStore:
    def create_job(self, urls: list[str], options: dict[str, object] | None = None) -> JobRecord:
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


class InMemoryJobStore(JobStore):
    def __init__(self) -> None:
        self._jobs: dict[UUID, JobRecord] = {}
        self._lock = Lock()

    def create_job(self, urls: list[str], options: dict[str, object] | None = None) -> JobRecord:
        record = JobRecord(
            job_id=uuid4(),
            status="pending",
            urls=urls,
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


def job_record_to_schema(record: JobRecord) -> Job:
    return Job(
        job_id=record.job_id,
        status=record.status,  # type: ignore[arg-type]
        urls=record.urls,  # type: ignore[arg-type]
        error_code=record.error_code,
        error_message=record.error_message,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
