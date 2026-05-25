"""BUG-2026-05-25: Modal data-management image missing langdetect dependency.

The tagging package declares langdetect>=1.0.9 but the Modal image only pip_installs
fastapi, httpx, and pydantic. Container crashes on startup with ModuleNotFoundError.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

_MODAL_APP = Path(__file__).resolve().parents[2] / "infra" / "modal" / "data_management_app.py"
_TAGGING_PYPROJECT = Path(__file__).resolve().parents[2] / "packages" / "tagging" / "pyproject.toml"


def _extract_pip_install_args(source: str) -> list[str]:
    """Extract string arguments from .pip_install(...) calls in the Modal app source."""
    tree = ast.parse(source)
    pip_args: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "pip_install"
        ):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    pip_args.append(arg.value)
    return pip_args


def _extract_external_deps(pyproject_text: str) -> list[str]:
    """Extract non-workspace dependencies from a pyproject.toml dependencies list."""
    deps: list[str] = []
    in_deps = False
    for line in pyproject_text.splitlines():
        if line.strip().startswith("dependencies"):
            in_deps = True
            continue
        if in_deps:
            if line.strip() == "]":
                break
            match = re.search(r'"([^"]+)"', line)
            if match:
                dep_spec = match.group(1)
                pkg_name = re.split(r"[><=!~\[]", dep_spec)[0].strip()
                if not pkg_name.startswith("vecinita"):
                    deps.append(pkg_name)
    return deps


def test_modal_image_includes_langdetect() -> None:
    """Modal data-management image must pip_install langdetect (required by vecinita-tagging)."""
    source = _MODAL_APP.read_text(encoding="utf-8")
    pip_args = _extract_pip_install_args(source)
    pip_package_names = [re.split(r"[><=!~\[]", arg)[0].strip() for arg in pip_args]

    assert "langdetect" in pip_package_names, (
        f"langdetect not found in Modal image pip_install(). "
        f"Installed: {pip_args}. "
        f"packages/tagging requires langdetect>=1.0.9 but it is not in the container image."
    )


def test_modal_image_includes_all_tagging_external_deps() -> None:
    """All external (non-workspace) deps of vecinita-tagging must be in the Modal image."""
    source = _MODAL_APP.read_text(encoding="utf-8")
    pip_args = _extract_pip_install_args(source)
    pip_package_names = [re.split(r"[><=!~\[]", arg)[0].strip().lower() for arg in pip_args]

    pyproject_text = _TAGGING_PYPROJECT.read_text(encoding="utf-8")
    external_deps = _extract_external_deps(pyproject_text)

    missing = [dep for dep in external_deps if dep.lower() not in pip_package_names]
    assert not missing, (
        f"Modal data-management image is missing pip packages required by vecinita-tagging: "
        f"{missing}. These must be added to pip_install() in {_MODAL_APP.name}."
    )


def test_tagging_vocabulary_importable() -> None:
    """The import chain that crashes in Modal must work locally."""
    from vecinita_tagging import vocabulary

    assert hasattr(vocabulary, "load_seed_vocabulary")
    assert hasattr(vocabulary, "detect_document_language")
