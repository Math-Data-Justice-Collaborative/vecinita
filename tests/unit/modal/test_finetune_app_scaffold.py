"""T129.3 — Modal FT app scaffold contract (F77 / ADR-053 / TP4).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/sessions/S030-corpus-automations/reports/tech-plan-delta.md §TP4]
[Spec: docs/dependency-inventory.md]
[Spec: docs/staging-secrets-matrix.md §EV-027]
"""

from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path
from typing import Final

import pytest
from infra.modal.finetune_pins import FINETUNE_IMAGE_PIPS

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
_APP_PATH: Final[Path] = _REPO_ROOT / "infra" / "modal" / "finetune_app.py"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _import_finetune_app() -> object:
    """Load finetune Modal app module; missing file is the red phase (T129.3)."""
    if not _APP_PATH.is_file():
        pytest.fail(
            "infra/modal/finetune_app.py missing (T129.3 / TP4 / ADR-053): " +
            "scaffold vecinita-llm-finetune + volume llm-finetune-adapters"
        )
    try:
        return importlib.import_module("infra.modal.finetune_app")
    except ModuleNotFoundError as exc:
        pytest.fail(f"infra.modal.finetune_app import failed (T129.3 / TP4): {exc}")


def _pip_install_string_args(source: str) -> list[str]:
    """Collect string literals passed to ``.pip_install(...)`` in Modal image defs."""
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "pip_install"
        ):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    found.append(arg.value)
                elif (
                    isinstance(arg, ast.Starred)
                    and isinstance(arg.value, ast.Name)
                    and arg.value.id == "FINETUNE_IMAGE_PIPS"
                ):
                    found.extend(FINETUNE_IMAGE_PIPS)
    return found


def test_finetune_app_module_exists() -> None:
    """Scaffold file must exist at TP4 path (not antibody src/finetune/)."""
    assert _APP_PATH.is_file(), "expected infra/modal/finetune_app.py (T129.3 / TP4 / ADR-053)"


def test_finetune_app_name_and_adapter_volume() -> None:
    """App name and adapters volume match ADR-053 / TP4."""
    mod = _import_finetune_app()
    assert getattr(mod, "APP_NAME", None) == "vecinita-llm-finetune"
    assert getattr(mod, "VOLUME_NAME", None) == "llm-finetune-adapters"
    assert getattr(mod, "BASE_VOLUME_NAME", None) == "llm-models"


def test_finetune_app_wires_finetune_image_pips() -> None:
    """Image must pip_install(*FINETUNE_IMAGE_PIPS) from finetune_pins (S030-D33)."""
    source = _APP_PATH.read_text(encoding="utf-8")
    assert "from infra.modal.finetune_pins import" in source or (
        "from infra.modal import finetune_pins" in source
    )
    assert "FINETUNE_IMAGE_PIPS" in source
    pip_args = _pip_install_string_args(source)
    for pin in FINETUNE_IMAGE_PIPS:
        assert pin in pip_args, (
            f"{pin} missing from finetune_app pip_install " +
            f"(got {pip_args!r}; must use *FINETUNE_IMAGE_PIPS)"
        )
    assert "bitsandbytes" not in " ".join(pip_args)


def test_finetune_app_docstring_lists_required_secrets() -> None:
    """Module docstring must list Modal secret keys (modal-service-client-init)."""
    mod = _import_finetune_app()
    doc = (mod.__doc__ or "").lower()
    assert "vecinita-llm-finetune" in doc
    assert "vecinita_internal_write_url" in doc
    assert "vecinita_internal_api_key" in doc
    assert "vecinita_automations_kill_switch" in doc
    assert "staging-secrets-matrix" in doc
    assert "src/finetune" in doc


def test_finetune_app_exposes_modal_app_and_volumes() -> None:
    """Scaffold must bind modal.App + adapter/base Volume.from_name."""
    mod = _import_finetune_app()
    assert getattr(mod, "app", None) is not None
    assert getattr(mod, "adapter_volume", None) is not None
    assert getattr(mod, "base_volume", None) is not None
    source = _APP_PATH.read_text(encoding="utf-8")
    assert "Volume.from_name(VOLUME_NAME" in source or (
        'from_name("llm-finetune-adapters"' in source
    )
    assert "create_if_missing=True" in source
