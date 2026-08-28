"""Modal apps that import infra.modal.* must mount infra into the image.

Live evidence: ModuleNotFoundError crash-loop on embedding + data-management
(HF-modal-crash-loops / BUG-2026-08-28).
"""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_MODAL = _REPO / "infra" / "modal"

# Apps that top-level-import infra.modal and crash without /root/infra on PYTHONPATH.
_APPS_NEEDING_INFRA_MOUNT = (
    "embedding_app.py",
    "data_management_app.py",
    "rerank_app.py",
)


def test_modal_apps_mount_infra_package_for_runtime_import() -> None:
    """Container import of infra.modal.* requires add_local_dir(infra → /root/infra)."""
    for name in _APPS_NEEDING_INFRA_MOUNT:
        source = (_MODAL / name).read_text(encoding="utf-8")
        assert "from infra.modal" in source, name
        assert 'remote_path="/root/infra"' in source, (
            f'{name} must .add_local_dir(..., remote_path="/root/infra") '
            "so runtime import infra.modal succeeds (BUG-2026-08-28 crash-loop)"
        )
        assert "PYTHONPATH" in source, f"{name} must set PYTHONPATH"
        assert "/root" in source, (
            f"{name} must put /root on PYTHONPATH so package infra is importable"
        )
