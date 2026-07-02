"""Guard against destructive corpus resets on remote Managed Postgres (DO staging).

BUG-2026-07-01: seed_eval_corpus() TRUNCATE against staging DATABASE_URL wiped ~40
ingested documents. Only localhost/CI Postgres may be reset by test helpers.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "postgres"})
_BLOCKED_HOST_SUFFIXES = (
    ".ondigitalocean.com",
    ".db.ondigitalocean.com",
    ".supabase.co",
    ".supabase.com",
)


def corpus_database_host(database_url: str) -> str:
    """Return the hostname from a SQLAlchemy/psycopg database URL."""
    parsed = urlparse(database_url.replace("postgresql+psycopg://", "postgresql://", 1))
    return parsed.hostname or ""


def is_local_corpus_database(database_url: str) -> bool:
    """True when the URL targets local/CI Postgres (safe for TRUNCATE in tests)."""
    host = corpus_database_host(database_url).lower()
    if not host:
        return False
    if host in _LOCAL_HOSTS:
        return True
    return host.endswith(".local")


def is_blocked_managed_corpus_host(host: str) -> bool:
    """True for DigitalOcean Managed Postgres and Supabase auth DB hosts."""
    lowered = host.lower()
    return any(lowered.endswith(suffix) for suffix in _BLOCKED_HOST_SUFFIXES)


def assert_corpus_reset_allowed(database_url: str) -> None:
    """Refuse TRUNCATE/reset helpers on staging/production Managed Postgres.

    Override (operators only, never in pytest): set VECINITA_ALLOW_CORPUS_RESET=1
    together with VECINITA_CORPUS_RESET_ACK=staging-wipe-confirmed.
    """
    host = corpus_database_host(database_url)
    if is_local_corpus_database(database_url):
        return
    if is_blocked_managed_corpus_host(host):
        if (
            os.environ.get("VECINITA_ALLOW_CORPUS_RESET") == "1"
            and os.environ.get("VECINITA_CORPUS_RESET_ACK") == "staging-wipe-confirmed"
        ):
            return
        msg = (
            f"Refusing corpus TRUNCATE on managed Postgres host {host!r}. "
            "Test helpers (seed_eval_corpus, reset_corpus_tables) may only run against "
            "local/CI Postgres. Restore from DO backups instead — see "
            "scripts/infra/do_verify_staging_backups.sh and docs/staging-runbook.md "
            "§Corpus protection."
        )
        raise RuntimeError(msg)
    if os.environ.get("VECINITA_ALLOW_CORPUS_RESET") == "1":
        return
    msg = (
        f"Refusing corpus TRUNCATE on non-local database host {host!r}. "
        "Use localhost for tests or set VECINITA_ALLOW_CORPUS_RESET=1 for intentional "
        "remote maintenance."
    )
    raise RuntimeError(msg)
