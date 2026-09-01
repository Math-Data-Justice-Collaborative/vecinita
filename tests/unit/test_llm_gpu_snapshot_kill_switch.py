"""TC-313-01 / EV-313: prod GPU snapshot kill-switch and playground invariant.

[Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md §Amendment EV-313]
[Spec: docs/test-plan.md §TC-313-01]
[Corpus: config]
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from unittest.mock import patch

from infra.modal.llm_app import (
    _gpu_snapshot_from_env,  # pyright: ignore[reportPrivateUsage]
)

REPO_ROOT = Path(__file__).resolve().parents[2]
LLM_APP = REPO_ROOT / "infra" / "modal" / "llm_app.py"
PLAYGROUND_APP = REPO_ROOT / "infra" / "modal" / "llm_playground_app.py"
LLM_CORE = REPO_ROOT / "infra" / "modal" / "llm_service_core.py"


def test_gpu_snapshot_defaults_false_when_env_unset() -> None:
    """Unset VECINITA_LLM_GPU_SNAPSHOT → False (TC-313-01)."""
    with patch.dict(os.environ, {}, clear=True):
        assert _gpu_snapshot_from_env() is False


def test_gpu_snapshot_false_for_falsey_values() -> None:
    """Falsey kill-switch values disable snapshots."""
    for value in ("0", "false", "False", "no", "off", ""):
        with patch.dict(os.environ, {"VECINITA_LLM_GPU_SNAPSHOT": value}, clear=True):
            assert _gpu_snapshot_from_env() is False


def test_gpu_snapshot_true_for_truthy_values() -> None:
    """Truthy kill-switch values enable snapshots."""
    for value in ("1", "true", "True", "yes", "on"):
        with patch.dict(os.environ, {"VECINITA_LLM_GPU_SNAPSHOT": value}, clear=True):
            assert _gpu_snapshot_from_env() is True


def test_prod_llm_app_wires_snapshot_from_kill_switch() -> None:
    """Prod LlmService enable_memory_snapshot must use the kill-switch helper."""
    source = LLM_APP.read_text(encoding="utf-8")
    assert "VECINITA_LLM_GPU_SNAPSHOT" in source
    assert "_gpu_snapshot_from_env" in source
    assert "enable_memory_snapshot=_PROD_GPU_SNAPSHOT" in source
    assert 'experimental_options={"enable_gpu_snapshot": True}' in source or (
        "enable_gpu_snapshot" in source and "_PROD_GPU_SNAPSHOT" in source
    )


def test_prod_snapshot_path_has_snap_true_false_and_sleep() -> None:
    """When snapshot path is present, source encodes snap lifecycle + Level-1 sleep."""
    source = LLM_APP.read_text(encoding="utf-8")
    assert "snap=True" in source
    assert "snap=False" in source
    assert "sleep" in source.lower()
    assert "wake" in source.lower()


def test_core_resolves_lora_after_snapshot_restore() -> None:
    """Base snapshot + post-restore LoRA bind (ADR-022 / #316)."""
    source = LLM_CORE.read_text(encoding="utf-8")
    assert "bind_lora_after_restore" in source or "_bind_lora_after_restore" in source
    assert "sleep" in source.lower() or "wake_up" in source


def test_playground_remains_snapshot_off() -> None:
    """Playground must stay enable_memory_snapshot=False (ADR-037 / EV-313-D4)."""
    source = PLAYGROUND_APP.read_text(encoding="utf-8")
    tree = ast.parse(source)
    found = False
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "LlmService":
            continue
        for dec in node.decorator_list:
            text = ast.unparse(dec)
            if "enable_memory_snapshot=False" in text:
                found = True
    assert found, "playground LlmService must set enable_memory_snapshot=False"


def test_prod_gpu_class_uses_gpu_secret_not_asgi_proxy_secret() -> None:
    """Defense-in-depth: GPU workers mount vecinita-llm-gpu, not ASGI proxy secret."""
    source = LLM_APP.read_text(encoding="utf-8")
    assert 'Secret.from_name("vecinita-llm-gpu")' in source
    assert "secrets=_LLM_GPU_SECRETS" in source
    # Class decorator must not wire ASGI secret onto GPU workers.
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "LlmService":
            continue
        for dec in node.decorator_list:
            text = ast.unparse(dec)
            assert "secrets=_LLM_ASGI_SECRETS" not in text
            assert "secrets=_LLM_GPU_SECRETS" in text


def test_kill_switch_docs_require_deploy_time_env() -> None:
    """Ops docs must say enable_memory_snapshot is fixed at modal deploy import."""
    source = LLM_APP.read_text(encoding="utf-8")
    assert "deploy" in source.lower()
    assert "Flip Secret + redeploy" not in source
    readme = (REPO_ROOT / "infra" / "modal" / "README.md").read_text(encoding="utf-8")
    assert "deploy-time" in readme.lower() or "modal deploy" in readme.lower()
    assert "VECINITA_LLM_GPU_SNAPSHOT" in readme
