"""BUG-2026-09-10: prod CORS origins must include prod FE hosts, not only staging.

[Corpus: staging] [Spec: docs/adr/ADR-054-distinct-staging-and-production.md]
"""

from __future__ import annotations

from vecinita_shared_schemas.cors import (
    cors_origins_contain_staging_hosts,
    parse_cors_origins,
    prod_cors_origins_cover_frontends,
)

_PROD_CHAT_FE = "https://vecinita-chat-rag-frontend-jnt8o.ondigitalocean.app"
_PROD_ADMIN_FE = "https://vecinita-admin-frontend-ef4ob.ondigitalocean.app"
_STAGING_CHAT_FE = "https://vecinita-staging-chat-fe-epvwo.ondigitalocean.app"


def test_prod_cors_staging_only_origins_fail_guard() -> None:
    """Staging-only CORS list must not pass the prod FE coverage guard."""
    origins = parse_cors_origins(_STAGING_CHAT_FE)
    assert (
        prod_cors_origins_cover_frontends(
            origins,
            frontend_origins=(_PROD_CHAT_FE, _PROD_ADMIN_FE),
        )
        is False
    )


def test_prod_cors_with_prod_frontends_passes_guard() -> None:
    """Prod FE origins in CORS list satisfy the coverage guard."""
    raw = f"{_PROD_ADMIN_FE},{_PROD_CHAT_FE}"
    origins = parse_cors_origins(raw)
    assert (
        prod_cors_origins_cover_frontends(
            origins,
            frontend_origins=(_PROD_CHAT_FE, _PROD_ADMIN_FE),
        )
        is True
    )


def test_prod_cors_coverage_missing_admin_fails() -> None:
    """Chat-only CORS list is incomplete for prod."""
    origins = parse_cors_origins(_PROD_CHAT_FE)
    assert (
        prod_cors_origins_cover_frontends(
            origins,
            frontend_origins=(_PROD_CHAT_FE, _PROD_ADMIN_FE),
        )
        is False
    )


def test_prod_cors_coverage_empty_fails() -> None:
    """Empty CORS list fails the prod FE coverage guard."""
    assert (
        prod_cors_origins_cover_frontends(
            parse_cors_origins(""),
            frontend_origins=(_PROD_CHAT_FE, _PROD_ADMIN_FE),
        )
        is False
    )


def test_cors_origins_contain_staging_hosts_detects_staging() -> None:
    """Staging FE hosts are flagged for prod CORS exclusion."""
    assert cors_origins_contain_staging_hosts([_STAGING_CHAT_FE]) is True
    assert cors_origins_contain_staging_hosts([_PROD_CHAT_FE, _PROD_ADMIN_FE]) is False
    assert cors_origins_contain_staging_hosts([_PROD_CHAT_FE, _STAGING_CHAT_FE]) is True
