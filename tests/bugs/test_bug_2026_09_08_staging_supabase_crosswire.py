"""Guard staging secret syncs from pushing prod Supabase auth into staging apps."""

from __future__ import annotations

from pathlib import Path

import pytest
from deploy.do_apps import validate_supabase_url_for_target

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_bug_2026_09_08_staging_supabase_crosswire_rejects_prod_url_for_staging() -> None:
    """Staging app secret sync must fail closed when SUPABASE_URL points at prod.

    [Corpus: staging]
    [Corpus: feature-list.md §F34]
    [Spec: docs/api-contract.md §Authentication]
    """
    with pytest.raises(SystemExit, match=r"staging.*SUPABASE_URL.*prod Supabase project"):
        validate_supabase_url_for_target(
            "vecinita-staging-write-api",
            "https://cfuvghdsuwactfeamtym.supabase.co",
        )


def test_bug_2026_09_08_staging_supabase_crosswire_allows_non_prod_url_for_staging() -> None:
    """A branch-backed staging Supabase URL remains valid for staging-targeted secret sync."""
    validate_supabase_url_for_target(
        "vecinita-staging-write-api",
        "https://stagingbranchref.supabase.co",
    )


def test_bug_2026_09_08_staging_supabase_crosswire_rejects_retired_staging_project_url() -> None:
    """Staging sync must reject the retired standalone staging Supabase project too."""
    with pytest.raises(
        SystemExit,
        match=r"staging.*SUPABASE_URL.*retired standalone staging Supabase project",
    ):
        validate_supabase_url_for_target(
            "vecinita-staging-write-api",
            "https://camkatfbjguwvymfgdme.supabase.co",
        )
