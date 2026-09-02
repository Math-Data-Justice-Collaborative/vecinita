"""TC-317-01 / TC-317-02 — thin Modal CPU ASGI ingress (EV-317 / #317).

[Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md §Amendment EV-317]
[Corpus: ADR-004]
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LLM_APP = REPO / "infra" / "modal" / "llm_app.py"
LLM_ASGI = REPO / "infra" / "modal" / "llm_asgi.py"


_FORBIDDEN_ASGI_IMPORTS = (
    "vllm",
    "torch",
    "infra.modal.llm_service_core",
)


def test_llm_asgi_module_avoids_heavy_gpu_imports() -> None:
    """TC-317-01: thin ASGI module must not import vLLM / torch / LlmServiceCore."""
    assert LLM_ASGI.is_file(), "expected infra/modal/llm_asgi.py for thin ingress (EV-317)"
    source = LLM_ASGI.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".", maxsplit=1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", maxsplit=1)[0])
            if node.module.startswith("infra.modal"):
                imported.add(node.module)
    for forbidden in _FORBIDDEN_ASGI_IMPORTS:
        assert forbidden not in imported, (
            f"llm_asgi.py must not import {forbidden} at module level (AC-317-01)"
        )
        assert not any(name.startswith(f"{forbidden}.") for name in imported), (
            f"llm_asgi.py must not import submodule of {forbidden} (AC-317-01)"
        )
    assert "from vllm" not in source
    assert "import vllm" not in source
    assert "llm_service_core" not in source


def test_fastapi_app_function_has_no_gpu() -> None:
    """TC-317-02: ASGI Modal function must stay on CPU (no gpu=)."""
    source = LLM_APP.read_text(encoding="utf-8")
    idx = source.index("def fastapi_app")
    window = source[max(0, idx - 400) : idx]
    assert "@modal.asgi_app()" in window
    assert "gpu=" not in window, "ASGI function must not set gpu= (AC-317-02)"


def test_fastapi_app_delegates_to_thin_asgi_builder() -> None:
    """fastapi_app should build routes via llm_asgi (lazy thin surface)."""
    source = LLM_APP.read_text(encoding="utf-8")
    idx = source.index("def fastapi_app")
    body = source[idx : idx + 800]
    assert "llm_asgi" in body or "build_prod_asgi_app" in body
