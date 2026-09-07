"""Local Postgres compose contract guards.

[Corpus: feature-list.md §F18]
[Corpus: system-spec]
[Spec: docs/adr/ADR-010-multi-app-digitalocean-topology.md]
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import yaml

if TYPE_CHECKING:
    from vecinita_shared_schemas.json_types import JsonObject

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPO_ROOT / "infra" / "docker-compose.yml"


def _load_compose() -> JsonObject:
    raw = cast("object", yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8")))
    assert isinstance(raw, dict)
    return cast("JsonObject", raw)


def test_local_postgres_service_keeps_loopback_bind() -> None:
    """Local Postgres should stay host-local for dev safety."""
    services = cast("dict[str, dict[str, object]]", _load_compose()["services"])
    postgres = services["postgres"]
    ports = cast("list[str]", postgres["ports"])
    assert "127.0.0.1:5432:5432" in ports


def test_local_postgres_service_does_not_drop_all_capabilities() -> None:
    """Local dev Postgres must start on Docker Desktop/macOS with its volume mounted."""
    services = cast("dict[str, dict[str, object]]", _load_compose()["services"])
    postgres = services["postgres"]
    cap_drop = cast("list[str] | None", postgres.get("cap_drop"))
    assert cap_drop is None or "ALL" not in cap_drop
