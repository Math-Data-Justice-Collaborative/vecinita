"""Security gap fixes — load Supabase credentials for pre-commit / advisors.

Covers: pre-commit must load SUPABASE_ACCESS_TOKEN from .env before soft-skipping
advisors (F62 moved security-scan off pre-push); shared helper must parse-only
(never source) .env / prod.env.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HELPER = REPO_ROOT / "scripts" / "security" / "load_supabase_credentials.sh"
PRE_PUSH = REPO_ROOT / "scripts" / "ci" / "pre_push.sh"
PRE_COMMIT = REPO_ROOT / "scripts" / "ci" / "pre_commit.sh"
REMEDIATE = REPO_ROOT / "scripts" / "security" / "remediate-supabase-advisors.sh"
APPLY_AUTH = REPO_ROOT / "scripts" / "supabase" / "apply_auth_config_from_toml.sh"
CONFIG_TOML = REPO_ROOT / "supabase" / "config.toml"
STATIC_ANALYSIS_DOC = REPO_ROOT / "docs" / "security" / "static-analysis.md"
REMEDIATION_DOC = REPO_ROOT / "docs" / "security" / "static-analysis-remediation-2026-07-28.md"
ENV_EXAMPLE = REPO_ROOT / "supabase" / ".env.example"


def test_load_supabase_credentials_helper_exists() -> None:
    """Shared parse-only credential loader must exist for pre-commit parity."""
    assert HELPER.is_file(), f"missing helper: {HELPER}"


def test_load_supabase_credentials_reads_token_and_ref_from_env_file(
    tmp_path: Path,
) -> None:
    """Helper exports token + project ref from a parse-only .env file."""
    env_file = tmp_path / ".env"
    _ = env_file.write_text(
        "SUPABASE_ACCESS_TOKEN=sbp_test_token_abc\n" +
        "SUPABASE_PROJECT_REF=cfuvghdsuwactfeamtym\n" +
        "OTHER=ignore\n",
        encoding="utf-8",
    )
    result = subprocess.run(  # noqa: S603
        [
            "/bin/bash",
            str(HELPER),
            "--export",
            "--root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "SUPABASE_ACCESS_TOKEN": "", "SUPABASE_PROJECT_REF": ""},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "SUPABASE_ACCESS_TOKEN=sbp_test_token_abc" in result.stdout
    assert "SUPABASE_PROJECT_REF=cfuvghdsuwactfeamtym" in result.stdout


def test_load_supabase_credentials_falls_back_to_project_id_and_config_toml(
    tmp_path: Path,
) -> None:
    """PROJECT_ID and config.toml project_id fill ref when PROJECT_REF unset."""
    _ = (tmp_path / ".env").write_text(
        "SUPABASE_ACCESS_TOKEN=sbp_from_id\nSUPABASE_PROJECT_ID=projidfallback\n",
        encoding="utf-8",
    )
    result = subprocess.run(  # noqa: S603
        ["/bin/bash", str(HELPER), "--export", "--root", str(tmp_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "SUPABASE_ACCESS_TOKEN": "", "SUPABASE_PROJECT_REF": ""},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "SUPABASE_PROJECT_REF=projidfallback" in result.stdout


def test_load_supabase_credentials_prefers_existing_process_env(
    tmp_path: Path,
) -> None:
    """Already-exported process env wins over .env file values."""
    _ = (tmp_path / ".env").write_text(
        "SUPABASE_ACCESS_TOKEN=sbp_from_file\nSUPABASE_PROJECT_REF=from_file\n",
        encoding="utf-8",
    )
    result = subprocess.run(  # noqa: S603
        ["/bin/bash", str(HELPER), "--export", "--root", str(tmp_path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SUPABASE_ACCESS_TOKEN": "sbp_from_process",
            "SUPABASE_PROJECT_REF": "from_process",
        },
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert "SUPABASE_ACCESS_TOKEN=sbp_from_process" in result.stdout
    assert "SUPABASE_PROJECT_REF=from_process" in result.stdout


def test_pre_commit_loads_credentials_before_advisor_skip() -> None:
    """pre_commit must load .env credentials before deciding to skip advisors (F62)."""
    text = PRE_COMMIT.read_text(encoding="utf-8")
    assert "load_supabase_credentials.sh" in text
    skip_pos = text.index("SEC_SKIP_SUPABASE_ADVISORS=1")
    load_pos = text.index("load_supabase_credentials.sh")
    assert load_pos < skip_pos, "credentials must load before soft-skip"
    # Lean pre-push must not own security-scan / advisor credential loading.
    push = PRE_PUSH.read_text(encoding="utf-8")
    assert "load_supabase_credentials.sh" not in push
    assert "make security-scan" not in push


def test_lean_pre_push_has_no_security_scan() -> None:
    """F62 / TC-208: default pre-push is lint + test-fast only."""
    push = PRE_PUSH.read_text(encoding="utf-8")
    assert "make lint" in push
    assert "make test-fast" in push
    assert "make security-scan" not in push


def test_remediator_and_apply_auth_pin_auth_db_pool_percent() -> None:
    """Auth DB pool unit=percent must stay enforced outside config.toml (CLI gap)."""
    rem = REMEDIATE.read_text(encoding="utf-8")
    apply = APPLY_AUTH.read_text(encoding="utf-8")
    assert 'db_max_pool_size_unit": "percent"' in rem or '"db_max_pool_size_unit": "percent"' in rem
    assert "db_max_pool_size_unit" in apply
    assert "percent" in apply


def test_config_toml_documents_auth_pool_management_api_pin() -> None:
    """config.toml must document that pool unit is Management-API-enforced."""
    text = CONFIG_TOML.read_text(encoding="utf-8")
    assert "db_max_pool_size_unit" in text
    assert "percent" in text


def test_static_analysis_docs_cover_precommit_env_and_kics_medium() -> None:
    """Docs must describe .env pre-commit loading, OpenGrep GHA noise, KICS MEDIUM."""
    static = STATIC_ANALYSIS_DOC.read_text(encoding="utf-8")
    assert "pre-commit" in static.lower() or "pre_commit" in static
    assert "load_supabase_credentials" in static
    assert ".env" in static
    assert "MEDIUM" in static
    assert "OpenGrep" in static
    rem = REMEDIATION_DOC.read_text(encoding="utf-8")
    assert "SEC_SKIP_SUPABASE_ADVISORS=1" not in rem.split("Post-fix")[-1] or "PASS" in rem
    # Post-fix section should not claim advisors are skipped for missing token locally.
    assert "skipped locally (no `SUPABASE_ACCESS_TOKEN`)" not in rem


def test_supabase_env_example_documents_project_ref_alias() -> None:
    """supabase/.env.example documents SUPABASE_PROJECT_REF alongside PROJECT_ID."""
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "SUPABASE_PROJECT_REF" in text
    assert "cfuvghdsuwactfeamtym" in text


@pytest.mark.parametrize(
    ("path"),
    [HELPER, PRE_PUSH, PRE_COMMIT, REMEDIATE, APPLY_AUTH],
)
def test_gap_scripts_are_executable_or_bash(path: Path) -> None:
    """Gap-related scripts exist and are bash."""
    assert path.is_file()
    head = path.read_text(encoding="utf-8")[:80]
    assert head.startswith("#!/")
