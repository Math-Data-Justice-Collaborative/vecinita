"""Security scan local-ignore contract."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ALL = REPO_ROOT / "scripts" / "security" / "run-all.sh"
KICS_EXCLUDES = REPO_ROOT / "config" / "security" / "kics-exclude-queries.txt"


def test_2ms_ignores_local_runtime_secret_files() -> None:
    """2ms should ignore local operator secret scratch files in working-tree scans."""
    text = RUN_ALL.read_text(encoding="utf-8")
    for pattern in (
        "--ignore-pattern '.env.staging'",
        "--ignore-pattern '.staging-db-url.local'",
        "--ignore-pattern '.staging-supabase-db-pass.local'",
        "--ignore-pattern '.staging-supabase-keys.local'",
        "--ignore-pattern '.staging-supabase-ref.local'",
    ):
        assert pattern in text


def test_kics_excludes_local_postgres_bootstrap_exception() -> None:
    """KICS should not hard-fail the local Docker Desktop Postgres bootstrap exception."""
    text = KICS_EXCLUDES.read_text(encoding="utf-8")
    for query_id in (
        "610e266e-6c12-4bca-9925-1ed0cd29742b",
        "ce76b7d0-9e77-464d-b86f-c5c48e03e22d",
    ):
        assert query_id in text


def test_sbom_license_fetch_timeout_defaults_to_30_seconds() -> None:
    """SBOM license fetch should fail closed quickly on transient ClearlyDefined stalls."""
    text = RUN_ALL.read_text(encoding="utf-8")
    assert '-lto "${SEC_SBOM_LICENSE_TIMEOUT_SEC:-30}"' in text
    assert '-lto "${SEC_SBOM_LICENSE_TIMEOUT_SEC:-300}"' not in text
