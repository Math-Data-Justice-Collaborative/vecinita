"""T81.3 / RD-170: llm-client declares shared-schemas as a package dependency."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import cast

_LLM_CLIENT_PYPROJECT = (
    Path(__file__).resolve().parents[2] / "packages" / "llm-client" / "pyproject.toml"
)


def test_llm_client_declares_shared_schemas_dependency() -> None:
    """packages/llm-client must list vecinita-shared-schemas (TP-S010-20 / RD-170)."""
    raw = tomllib.loads(_LLM_CLIENT_PYPROJECT.read_text(encoding="utf-8"))
    project = cast("dict[str, object]", raw["project"])
    deps_obj = project["dependencies"]
    assert isinstance(deps_obj, list)
    deps = [item for item in cast("list[object]", deps_obj) if isinstance(item, str)]
    assert any(
        dep == "vecinita-shared-schemas" or dep.startswith("vecinita-shared-schemas")
        for dep in deps
    ), (
        "packages/llm-client/pyproject.toml must declare vecinita-shared-schemas "
        + "(LlmClient imports resolve_llm_http_config from shared-schemas)"
    )
