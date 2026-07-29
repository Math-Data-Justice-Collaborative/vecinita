"""Job stores for Modal ASGI — in-memory for tests, shared dict for production."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import TYPE_CHECKING, NotRequired, TypedDict
from uuid import UUID, uuid4

from vecinita_shared_schemas.data_management import Job

if TYPE_CHECKING:
    from collections.abc import MutableMapping


@dataclass
class JobRecord:
    """Internal job state before API schema mapping."""

    job_id: UUID
    status: str
    urls: list[str]
    job_type: str = "ingest"
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    options: dict[str, object] = field(default_factory=dict)
    initiated_by_user_id: UUID | None = None
    initiated_by_role: str | None = None
    modal_call_id: str | None = None
    dashboard_url: str | None = None
    eval_run_id: UUID | None = None


class JobPayload(TypedDict):
    """Serialized job record stored in Modal Dict or memory."""

    job_id: str
    status: str
    urls: list[str]
    job_type: str
    error_code: str | None
    error_message: str | None
    created_at: str
    updated_at: str
    options: dict[str, object]
    initiated_by_user_id: NotRequired[str]
    initiated_by_role: NotRequired[str]
    modal_call_id: NotRequired[str | None]
    dashboard_url: NotRequired[str | None]
    eval_run_id: NotRequired[str | None]
    document_id: NotRequired[str | None]


def _document_id_from_options(options: dict[str, object]) -> str | None:
    raw = options.get("document_id")
    return str(raw) if raw is not None else None


def _eval_run_id_from_record(record: JobRecord) -> str | None:
    if record.eval_run_id is not None:
        return str(record.eval_run_id)
    raw = record.options.get("eval_run_id")
    return str(raw) if raw is not None else None


class JobStore:
    """Persistence interface for job lifecycle."""

    def create_job(
        self,
        urls: list[str],
        options: dict[str, object] | None = None,
        *,
        job_type: str = "ingest",
        initiated_by_user_id: UUID | None = None,
        initiated_by_role: str | None = None,
    ) -> JobRecord:
        """Create a pending job record."""
        raise NotImplementedError

    def get_job(self, job_id: UUID) -> JobRecord | None:
        """Return a job by id, or None when missing."""
        raise NotImplementedError

    def update_job(  # noqa: PLR0913  # status + error + Modal/eval metadata fields
        self,
        job_id: UUID,
        *,
        status: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        modal_call_id: str | None = None,
        dashboard_url: str | None = None,
        eval_run_id: UUID | None = None,
    ) -> JobRecord:
        """Update job status and optional metadata fields."""
        raise NotImplementedError

    def delete_job(self, job_id: UUID) -> bool:
        """Remove a job record. Return True when deleted, False when missing."""
        raise NotImplementedError

    def list_jobs(self) -> list[JobRecord]:
        """Return all jobs, newest first."""
        raise NotImplementedError


def _apply_updates(  # noqa: PLR0913  # mirrors update_job keyword surface
    record: JobRecord,
    *,
    status: str | None,
    error_code: str | None,
    error_message: str | None,
    modal_call_id: str | None,
    dashboard_url: str | None,
    eval_run_id: UUID | None,
) -> None:
    if status is not None:
        record.status = status
    if error_code is not None:
        record.error_code = error_code
    if error_message is not None:
        record.error_message = error_message
    if modal_call_id is not None:
        record.modal_call_id = modal_call_id
    if dashboard_url is not None:
        record.dashboard_url = dashboard_url
    if eval_run_id is not None:
        record.eval_run_id = eval_run_id
    record.updated_at = datetime.now(UTC)


def _record_to_payload(record: JobRecord) -> JobPayload:
    payload: JobPayload = {
        "job_id": str(record.job_id),
        "status": record.status,
        "urls": record.urls,
        "job_type": record.job_type,
        "error_code": record.error_code,
        "error_message": record.error_message,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
        "options": record.options,
        "modal_call_id": record.modal_call_id,
        "dashboard_url": record.dashboard_url,
        "eval_run_id": _eval_run_id_from_record(record),
        "document_id": _document_id_from_options(record.options),
    }
    if record.initiated_by_user_id is not None:
        payload["initiated_by_user_id"] = str(record.initiated_by_user_id)
    if record.initiated_by_role is not None:
        payload["initiated_by_role"] = record.initiated_by_role
    return payload


def _payload_to_record(payload: JobPayload) -> JobRecord:
    initiated_raw = payload.get("initiated_by_user_id")
    eval_raw = payload.get("eval_run_id")
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
        initiated_by_user_id=UUID(str(initiated_raw)) if initiated_raw else None,
        initiated_by_role=payload.get("initiated_by_role"),
        modal_call_id=payload.get("modal_call_id"),
        dashboard_url=payload.get("dashboard_url"),
        eval_run_id=UUID(str(eval_raw)) if eval_raw else None,
    )


class DictJobStore(JobStore):
    """Job store backed by a shared mapping (e.g. modal.Dict) visible across Modal workers."""

    def __init__(self, backing: MutableMapping[str, JobPayload]) -> None:
        """Wrap a shared mapping visible across Modal workers."""
        self._jobs = backing

    def create_job(
        self,
        urls: list[str],
        options: dict[str, object] | None = None,
        *,
        job_type: str = "ingest",
        initiated_by_user_id: UUID | None = None,
        initiated_by_role: str | None = None,
    ) -> JobRecord:
        """Persist a new pending job in the shared mapping."""
        opts = options or {}
        eval_raw = opts.get("eval_run_id")
        record = JobRecord(
            job_id=uuid4(),
            status="pending",
            urls=urls,
            job_type=job_type,
            options=opts,
            initiated_by_user_id=initiated_by_user_id,
            initiated_by_role=initiated_by_role,
            eval_run_id=UUID(str(eval_raw)) if eval_raw else None,
        )
        self._jobs[str(record.job_id)] = _record_to_payload(record)
        return record

    def get_job(self, job_id: UUID) -> JobRecord | None:
        """Load a job from the shared mapping."""
        payload = self._jobs.get(str(job_id))
        if payload is None:
            return None
        return _payload_to_record(payload)

    def update_job(  # noqa: PLR0913  # status + error + Modal/eval metadata fields
        self,
        job_id: UUID,
        *,
        status: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        modal_call_id: str | None = None,
        dashboard_url: str | None = None,
        eval_run_id: UUID | None = None,
    ) -> JobRecord:
        """Apply status or metadata updates to a shared-mapping job."""
        key = str(job_id)
        payload = self._jobs.get(key)
        if payload is None:
            raise KeyError(job_id)
        record = _payload_to_record(payload)
        _apply_updates(
            record,
            status=status,
            error_code=error_code,
            error_message=error_message,
            modal_call_id=modal_call_id,
            dashboard_url=dashboard_url,
            eval_run_id=eval_run_id,
        )
        self._jobs[key] = _record_to_payload(record)
        return record

    def delete_job(self, job_id: UUID) -> bool:
        """Delete a job from the shared mapping."""
        return self._jobs.pop(str(job_id), None) is not None

    def list_jobs(self) -> list[JobRecord]:
        """Return all jobs from the shared mapping, newest first."""
        records = [_payload_to_record(payload) for payload in self._jobs.values()]
        records.sort(key=lambda record: record.created_at, reverse=True)
        return records


class InMemoryJobStore(JobStore):
    """Thread-safe in-process job store for local tests and single-worker runs."""

    def __init__(self) -> None:
        """Create an empty in-process job store."""
        self._jobs: dict[UUID, JobRecord] = {}
        self._lock = Lock()

    def create_job(
        self,
        urls: list[str],
        options: dict[str, object] | None = None,
        *,
        job_type: str = "ingest",
        initiated_by_user_id: UUID | None = None,
        initiated_by_role: str | None = None,
    ) -> JobRecord:
        """Create a pending job in memory."""
        opts = options or {}
        eval_raw = opts.get("eval_run_id")
        record = JobRecord(
            job_id=uuid4(),
            status="pending",
            urls=urls,
            job_type=job_type,
            options=opts,
            initiated_by_user_id=initiated_by_user_id,
            initiated_by_role=initiated_by_role,
            eval_run_id=UUID(str(eval_raw)) if eval_raw else None,
        )
        with self._lock:
            self._jobs[record.job_id] = record
        return record

    def get_job(self, job_id: UUID) -> JobRecord | None:
        """Return a job from memory."""
        with self._lock:
            return self._jobs.get(job_id)

    def update_job(  # noqa: PLR0913  # status + error + Modal/eval metadata fields
        self,
        job_id: UUID,
        *,
        status: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        modal_call_id: str | None = None,
        dashboard_url: str | None = None,
        eval_run_id: UUID | None = None,
    ) -> JobRecord:
        """Update a job record held in memory."""
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None:
                raise KeyError(job_id)
            _apply_updates(
                record,
                status=status,
                error_code=error_code,
                error_message=error_message,
                modal_call_id=modal_call_id,
                dashboard_url=dashboard_url,
                eval_run_id=eval_run_id,
            )
            return record

    def delete_job(self, job_id: UUID) -> bool:
        """Delete a job from memory."""
        with self._lock:
            return self._jobs.pop(job_id, None) is not None

    def list_jobs(self) -> list[JobRecord]:
        """Return all in-memory jobs, newest first."""
        with self._lock:
            records = list(self._jobs.values())
        records.sort(key=lambda record: record.created_at, reverse=True)
        return records


def job_record_to_schema(record: JobRecord) -> Job:
    """Map a store record to the public Job API model.

    Round-trips through ``Job.model_validate`` so Pydantic coerces the record's
    loose ``str`` / ``list[str]`` fields into the schema's ``Literal`` / ``HttpUrl``
    types and validates them, instead of suppressing the type mismatch.
    """
    return Job.model_validate(_record_to_payload(record))
