"""T129.8 — llm_app / playground mount llm-finetune-adapters for LoRA serve (F77).

[Corpus: feature-list.md §F77]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/adr/ADR-037-unified-vecinita-llm-modal-app.md]
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LLM_APP = _REPO / "infra" / "modal" / "llm_app.py"
_PLAYGROUND_APP = _REPO / "infra" / "modal" / "llm_playground_app.py"


def _cls_volumes_source(path: Path, class_name: str = "LlmService") -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            text = ast.get_source_segment(source, dec) or ""
            if "volumes=" in text:
                return text
    pytest.fail(f"{class_name} volumes= decorator not found in {path}")


def test_prod_llm_service_mounts_finetune_adapters_volume() -> None:
    """Prod LlmService must mount llm-finetune-adapters at /adapters (ADR-053)."""
    text = _cls_volumes_source(_LLM_APP)
    assert "/adapters" in text
    assert "adapters_volume" in text or "llm-finetune-adapters" in text
    source = _LLM_APP.read_text(encoding="utf-8")
    assert "decide_serve_adapter_id" in source
    assert '_adapter_load_for_role("prod")' in source


def test_playground_llm_service_mounts_finetune_adapters_volume() -> None:
    """Playground LlmService mounts adapters for pre-promote candidates."""
    text = _cls_volumes_source(_PLAYGROUND_APP)
    assert "/adapters" in text
    source = _PLAYGROUND_APP.read_text(encoding="utf-8")
    assert '_adapter_load_for_role("playground")' in source
