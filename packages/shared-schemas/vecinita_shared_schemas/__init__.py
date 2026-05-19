"""Shared Pydantic models and cross-cutting helpers (ADR-011)."""

from vecinita_shared_schemas.chat_rag import AskRequest, AskResponse, HealthResponse, Source
from vecinita_shared_schemas.data_management import CreateJobRequest, CreateJobResponse, Job
from vecinita_shared_schemas.internal_write import (
    BatchUpsertRequest,
    BatchUpsertResponse,
    DocumentSummary,
)
from vecinita_shared_schemas.observability import configure_logging, log_request_event
from vecinita_shared_schemas.validation import (
    FORBIDDEN_IDENTITY_FIELDS,
    find_identity_fields,
    validate_ask_request,
)

__version__ = "0.1.0"

__all__ = [
    "FORBIDDEN_IDENTITY_FIELDS",
    "AskRequest",
    "AskResponse",
    "BatchUpsertRequest",
    "BatchUpsertResponse",
    "CreateJobRequest",
    "CreateJobResponse",
    "DocumentSummary",
    "HealthResponse",
    "Job",
    "Source",
    "configure_logging",
    "find_identity_fields",
    "log_request_event",
    "validate_ask_request",
]
