"""S001 T4-T6 / ADR-037: vecinita-llm image and LlmService lazy-load (no GPU snapshot)."""

from __future__ import annotations

import ast
from pathlib import Path

from infra.modal.llm_app import LLM_MAX_MODEL_LEN, max_model_len_for

REPO_ROOT = Path(__file__).resolve().parents[2]
LLM_APP = REPO_ROOT / "infra" / "modal" / "llm_app.py"

SNAPSHOT_ENV_VARS = (
    "TORCHINDUCTOR_COMPILE_THREADS",
    "XFORMERS_ENABLE_TRITON",
)


def _llm_app_source() -> str:
    """Read the Modal LLM app source as text."""
    return LLM_APP.read_text(encoding="utf-8")


def _llm_service_class() -> ast.ClassDef:
    """Return the LlmService class node parsed from the LLM app source."""
    tree = ast.parse(_llm_app_source())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "LlmService":
            return node
    msg = "LlmService not found"
    raise AssertionError(msg)


def _method_named(cls: ast.ClassDef, name: str) -> ast.FunctionDef:
    """Return the named method node from a class definition."""
    for item in cls.body:
        if isinstance(item, ast.FunctionDef) and item.name == name:
            return item
    msg = f"LlmService.{name} not found"
    raise AssertionError(msg)


def _function_has_vllm_import(func: ast.FunctionDef) -> bool:
    """Return whether the function body imports from the vllm module."""
    for child in ast.walk(func):
        if isinstance(child, ast.ImportFrom) and child.module == "vllm":
            return True
    return False


def test_llm_image_imports_vllm_for_snapshot() -> None:
    """LLM image imports vllm inside an image.imports() block."""
    source = _llm_app_source()
    assert "with image.imports():" in source
    assert "from vllm import LLM, SamplingParams" in source


def test_llm_image_sets_snapshot_mitigation_env_vars() -> None:
    """LLM image sets compile/triton mitigation environment variables."""
    source = _llm_app_source()
    for var in SNAPSHOT_ENV_VARS:
        assert var in source, f"missing env var {var}"


def test_llm_image_pins_vllm_with_sleep_mode() -> None:
    """LLM image pins vllm and enables sleep mode."""
    source = _llm_app_source()
    assert "vllm>=" in source
    assert '"enable_sleep_mode": True' in source or "'enable_sleep_mode': True" in source


def test_load_model_does_not_import_vllm_inline() -> None:
    """load_model avoids importing vllm inline."""
    load_model = _method_named(_llm_service_class(), "load_model")
    assert not _function_has_vllm_import(load_model)


def test_generate_text_does_not_import_sampling_params_inline() -> None:
    """_generate_text avoids importing SamplingParams inline."""
    generate_text = _method_named(_llm_service_class(), "_generate_text")
    assert not _function_has_vllm_import(generate_text)


def test_load_model_lazy_initializes_state() -> None:
    """ADR-037: load_model defers vLLM init until first request (model_id switching)."""
    load_model = _method_named(_llm_service_class(), "load_model")
    source = ast.unparse(load_model)
    assert "self._llm = None" in source
    assert "self._loaded_model_arg = None" in source


def test_llm_service_disables_gpu_memory_snapshot() -> None:
    """ADR-037: GPU snapshot breaks NCCL when switching model_id — snapshot disabled."""
    source = _llm_app_source()
    assert "enable_memory_snapshot=False" in source


def test_max_model_len_supports_golden_eval_prompts() -> None:
    """Context window must fit RAG golden-eval prompts (>1024 tokens)."""
    assert max_model_len_for("Qwen/Qwen3-8B-AWQ") >= LLM_MAX_MODEL_LEN
    assert max_model_len_for("Qwen/Qwen2.5-1.5B-Instruct") >= LLM_MAX_MODEL_LEN
