"""Shared Pydantic models and cross-cutting helpers (ADR-011).

Exports are resolved lazily via ``__getattr__`` so Modal LLM images can import
``playground_hf_registry`` without installing PyJWT / auth stack (T80.7).
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
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
    from vecinita_shared_schemas.data_management import (
        CreateJobRequest,
        CreateJobResponse,
        Job,
    )
    from vecinita_shared_schemas.internal_write import (
        BatchUpsertRequest,
        BatchUpsertResponse,
        DocumentListPage,
        DocumentSummary,
    )
    from vecinita_shared_schemas.observability import configure_logging, log_request_event
    from vecinita_shared_schemas.validation import (
        FORBIDDEN_IDENTITY_FIELDS,
        find_identity_fields,
        validate_ask_request,
    )

__version__ = "0.1.0"

# name -> (submodule, attribute)
_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "FORBIDDEN_IDENTITY_FIELDS": (
        "vecinita_shared_schemas.validation",
        "FORBIDDEN_IDENTITY_FIELDS",
    ),
    "AskRequest": ("vecinita_shared_schemas.chat_rag", "AskRequest"),
    "AskResponse": ("vecinita_shared_schemas.chat_rag", "AskResponse"),
    "AuthConfig": ("vecinita_shared_schemas.auth", "AuthConfig"),
    "AuthContext": ("vecinita_shared_schemas.auth", "AuthContext"),
    "AuthPrincipal": ("vecinita_shared_schemas.auth", "AuthPrincipal"),
    "BatchUpsertRequest": ("vecinita_shared_schemas.internal_write", "BatchUpsertRequest"),
    "BatchUpsertResponse": ("vecinita_shared_schemas.internal_write", "BatchUpsertResponse"),
    "CreateJobRequest": ("vecinita_shared_schemas.data_management", "CreateJobRequest"),
    "CreateJobResponse": ("vecinita_shared_schemas.data_management", "CreateJobResponse"),
    "DocumentBrowseDetail": ("vecinita_shared_schemas.chat_rag", "DocumentBrowseDetail"),
    "DocumentBrowseItem": ("vecinita_shared_schemas.chat_rag", "DocumentBrowseItem"),
    "DocumentBrowsePage": ("vecinita_shared_schemas.chat_rag", "DocumentBrowsePage"),
    "DocumentListPage": ("vecinita_shared_schemas.internal_write", "DocumentListPage"),
    "DocumentSummary": ("vecinita_shared_schemas.internal_write", "DocumentSummary"),
    "HealthResponse": ("vecinita_shared_schemas.chat_rag", "HealthResponse"),
    "Job": ("vecinita_shared_schemas.data_management", "Job"),
    "Source": ("vecinita_shared_schemas.chat_rag", "Source"),
    "TagFacet": ("vecinita_shared_schemas.chat_rag", "TagFacet"),
    "TagListResponse": ("vecinita_shared_schemas.chat_rag", "TagListResponse"),
    "TagSummary": ("vecinita_shared_schemas.chat_rag", "TagSummary"),
    "configure_logging": ("vecinita_shared_schemas.observability", "configure_logging"),
    "find_identity_fields": ("vecinita_shared_schemas.validation", "find_identity_fields"),
    "get_auth_config": ("vecinita_shared_schemas.auth", "get_auth_config"),
    "get_principal": ("vecinita_shared_schemas.auth", "get_principal"),
    "log_request_event": ("vecinita_shared_schemas.observability", "log_request_event"),
    "require_admin_write": ("vecinita_shared_schemas.auth", "require_admin_write"),
    "require_authenticated": ("vecinita_shared_schemas.auth", "require_authenticated"),
    "require_role": ("vecinita_shared_schemas.auth", "require_role"),
    "reset_auth_config_for_tests": (
        "vecinita_shared_schemas.auth",
        "reset_auth_config_for_tests",
    ),
    "resolve_operator_or_service": (
        "vecinita_shared_schemas.auth",
        "resolve_operator_or_service",
    ),
    "validate_ask_request": ("vecinita_shared_schemas.validation", "validate_ask_request"),
    "verify_supabase_jwt": ("vecinita_shared_schemas.auth", "verify_supabase_jwt"),
}

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
    "DocumentListPage",
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


def __getattr__(name: str) -> object:
    """Resolve public exports on first access (avoids auth/jwt on submodule imports)."""
    target = _LAZY_EXPORTS.get(name)
    if target is None:
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)
    module_name, attr = target
    # module_name is from the fixed _LAZY_EXPORTS map (not user input).
    # nosemgrep: python.lang.security.audit.non-literal-import.non-literal-import
    value = cast("object", getattr(import_module(module_name), attr))
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted({*globals().keys(), *__all__})
