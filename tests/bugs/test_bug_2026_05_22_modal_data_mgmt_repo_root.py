"""BUG-2026-05-22: Modal data-mgmt ASGI must import when mounted at /root/data_management_app.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def test_data_management_app_imports_when_modal_mounts_at_root(tmp_path: Path) -> None:
    """Modal copies the deploy module to /root/data_management_app.py — parents[2] must not crash."""
    source = (
        Path(__file__).resolve().parents[2]
        / "infra"
        / "modal"
        / "data_management_app.py"
    )
    mounted = tmp_path / "data_management_app.py"
    mounted.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("data_management_app_mounted", mounted)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module._REPO_ROOT == Path("/opt/vecinita")
