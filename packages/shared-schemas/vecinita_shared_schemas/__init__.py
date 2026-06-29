"""Shared Pydantic models and cross-cutting helpers (ADR-011)."""

from vecinita_shared_schemas.auth import (
    AuthConfig,
    AuthContext,
    AuthPrincipal,
    get_auth_config,
    get_principal,
    require_admin_write,
    require_authenticated,
    require_role,
    reset_auth_config_for_tests,
    resolve_operator_or_service,
    verify_supabase_jwt,
)
from vecinita_shared_schemas.chat_rag import (
    AskRequest,
    AskResponse,
    DocumentBrowseDetail,
    DocumentBrowseItem,
    DocumentBrowsePage,
    HealthResponse,
    Source,
    TagFacet,
    TagListResponse,
    TagSummary,
)
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
    "AuthConfig",
    "AuthContext",
    "AuthPrincipal",
    "BatchUpsertRequest",
    "BatchUpsertResponse",
    "CreateJobRequest",
    "CreateJobResponse",
    "DocumentBrowseDetail",
    "DocumentBrowseItem",
    "DocumentBrowsePage",
    "DocumentSummary",
    "HealthResponse",
    "Job",
    "Source",
    "TagFacet",
    "TagListResponse",
    "TagSummary",
    "configure_logging",
    "find_identity_fields",
    "get_auth_config",
    "get_principal",
    "log_request_event",
    "require_admin_write",
    "require_authenticated",
    "require_role",
    "reset_auth_config_for_tests",
    "resolve_operator_or_service",
    "validate_ask_request",
    "verify_supabase_jwt",
]
