"""Local Postgres compose contract for CI-style bootstrap."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPO_ROOT / "infra" / "docker-compose.yml"


def test_local_postgres_does_not_drop_required_init_privileges() -> None:
    """The local Postgres service must boot under Docker Desktop for CI-style tests."""
    text = COMPOSE_PATH.read_text(encoding="utf-8")

    assert "container_name: vecinita-postgres" in text
    assert "cap_drop:" not in text
    assert "no-new-privileges:true" not in text
