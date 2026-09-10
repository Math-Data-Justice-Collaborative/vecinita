"""BUG-2026-05-22: Modal data-mgmt ASGI must import when mounted at /root/data_management_app.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Protocol, cast


class _MountedDataMgmtModule(Protocol):
    _REPO_ROOT: object


def test_data_management_app_imports_when_modal_mounts_at_root(tmp_path: Path) -> None:
    """Modal copies the deploy module to /root/data_management_app.py — parents[2] must not crash."""
    repo_root = Path(__file__).resolve().parents[2]
    source = repo_root / "infra" / "modal" / "data_management_app.py"
    repo_paths = repo_root / "infra" / "modal" / "repo_paths.py"
    mounted = tmp_path / "data_management_app.py"
    mounted_repo_paths = tmp_path / "infra" / "modal" / "repo_paths.py"
    _ = (tmp_path / "infra" / "modal").mkdir(parents=True, exist_ok=True)
    _ = (tmp_path / "infra" / "__init__.py").write_text("", encoding="utf-8")
    _ = (tmp_path / "infra" / "modal" / "__init__.py").write_text("", encoding="utf-8")
    _ = mounted.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    _ = mounted_repo_paths.write_text(repo_paths.read_text(encoding="utf-8"), encoding="utf-8")

    spec = importlib.util.spec_from_file_location("data_management_app_mounted", mounted)
    assert spec
    assert spec.loader
    raw_module = importlib.util.module_from_spec(spec)
    old_infra = sys.modules.pop("infra", None)
    old_modal = sys.modules.pop("infra.modal", None)
    old_repo_paths = sys.modules.pop("infra.modal.repo_paths", None)
    sys.path.insert(0, str(tmp_path))
    try:
        spec.loader.exec_module(raw_module)
        module = cast("_MountedDataMgmtModule", raw_module)
    finally:
        sys.path.remove(str(tmp_path))
        if old_infra is not None:
            sys.modules["infra"] = old_infra
        if old_modal is not None:
            sys.modules["infra.modal"] = old_modal
        if old_repo_paths is not None:
            sys.modules["infra.modal.repo_paths"] = old_repo_paths

    repo_root: object = module._REPO_ROOT  # noqa: SLF001 # deploy script private attr under test  # pyright: ignore[reportPrivateUsage]
    assert Path("/opt/vecinita") == Path(str(repo_root))
