"""Regression: package __init__ must not eager-import auth (LLM Modal image has no PyJWT).

T80.7 / ADR-037: Modal mounts ``vecinita_shared_schemas`` into the vLLM image for
``playground_hf_registry`` only. Eager ``from .auth import …`` in ``__init__.py``
crash-loops ASGI with ``ModuleNotFoundError: No module named 'jwt'``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
import vecinita_shared_schemas as schemas
from vecinita_shared_schemas.playground_hf_registry import resolve_hf_repo

_INIT = (
    Path(__file__).resolve().parents[3]
    / "packages"
    / "shared-schemas"
    / "vecinita_shared_schemas"
    / "__init__.py"
)


def _is_type_checking_guard(node: ast.AST) -> bool:
    """True when ``if TYPE_CHECKING:`` wraps a block (type-checker only)."""
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Name)
        and node.test.id == "TYPE_CHECKING"
    )


def test_shared_schemas_init_has_no_eager_auth_import() -> None:
    """AST-guard: runtime top-level imports must not pull auth (and thus PyJWT)."""
    source = _INIT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if _is_type_checking_guard(node):
            continue
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod == "auth" or mod.endswith(".auth") or mod == "vecinita_shared_schemas.auth":
                names = ", ".join(a.name for a in node.names)
                msg = f"eager auth import forbidden in package __init__: {mod} ({names})"
                pytest.fail(msg)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "auth" in alias.name.split("."):
                    pytest.fail(f"eager auth import forbidden: {alias.name}")


def test_playground_hf_registry_importable_without_package_auth() -> None:
    """Submodule import must succeed even when package __init__ is lazy."""
    assert resolve_hf_repo("qwen2.5:1.5b-instruct") == "Qwen/Qwen2.5-1.5B-Instruct"


def test_lazy_getattr_resolves_public_exports() -> None:
    """``from vecinita_shared_schemas import X`` must resolve via ``__getattr__``."""
    # Touch several modules so __getattr__ branches hit auth + non-auth paths.
    assert schemas.AuthConfig is not None
    assert schemas.AskRequest is not None
    assert schemas.Job is not None
    assert schemas.BatchUpsertRequest is not None
    assert callable(schemas.configure_logging)
    assert callable(schemas.validate_ask_request)
    assert "AuthConfig" in dir(schemas)


def test_lazy_getattr_unknown_name_raises_attribute_error() -> None:
    """Unknown package attributes must raise AttributeError (not KeyError)."""
    with pytest.raises(AttributeError, match="has no attribute"):
        _ = schemas.definitely_not_an_export_xyz
