"""S001 T4-T6: GPU snapshot prep for vecinita-llm (imports, enter split, snapshot flags)."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LLM_APP = REPO_ROOT / "infra" / "modal" / "llm_app.py"

SNAPSHOT_ENV_VARS = (
    "TORCHINDUCTOR_COMPILE_THREADS",
    "XFORMERS_ENABLE_TRITON",
)


def _llm_app_source() -> str:
    return LLM_APP.read_text(encoding="utf-8")


def _llm_service_class() -> ast.ClassDef:
    tree = ast.parse(_llm_app_source())
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "LlmService":
            return node
    raise AssertionError("LlmService not found")


def _method_named(cls: ast.ClassDef, name: str) -> ast.FunctionDef:
    for item in cls.body:
        if isinstance(item, ast.FunctionDef) and item.name == name:
            return item
    raise AssertionError(f"LlmService.{name} not found")


def _function_has_vllm_import(func: ast.FunctionDef) -> bool:
    for child in ast.walk(func):
        if isinstance(child, ast.ImportFrom) and child.module == "vllm":
            return True
    return False


def _enter_decorator_snap_value(func: ast.FunctionDef) -> bool | None:
    for dec in func.decorator_list:
        if not isinstance(dec, ast.Call):
            continue
        if not (
            isinstance(dec.func, ast.Attribute)
            and dec.func.attr == "enter"
            and isinstance(dec.func.value, ast.Name)
            and dec.func.value.id == "modal"
        ):
            continue
        for keyword in dec.keywords:
            if keyword.arg == "snap" and isinstance(keyword.value, ast.Constant):
                return bool(keyword.value.value)
    return None


def test_llm_image_imports_vllm_for_snapshot() -> None:
    source = _llm_app_source()
    assert "with image.imports():" in source
    assert "from vllm import LLM, SamplingParams" in source


def test_llm_image_sets_snapshot_mitigation_env_vars() -> None:
    source = _llm_app_source()
    for var in SNAPSHOT_ENV_VARS:
        assert var in source, f"missing snapshot env var {var}"


def test_llm_image_pins_vllm_with_sleep_mode() -> None:
    source = _llm_app_source()
    assert "vllm>=" in source
    assert '"enable_sleep_mode": True' in source or "'enable_sleep_mode': True" in source


def test_load_model_does_not_import_vllm_inline() -> None:
    load_model = _method_named(_llm_service_class(), "load_model")
    assert not _function_has_vllm_import(load_model)


def test_generate_text_does_not_import_sampling_params_inline() -> None:
    generate_text = _method_named(_llm_service_class(), "_generate_text")
    assert not _function_has_vllm_import(generate_text)


def test_llm_service_splits_enter_for_snapshot() -> None:
    cls = _llm_service_class()
    assert _enter_decorator_snap_value(_method_named(cls, "load_model")) is True
    assert _enter_decorator_snap_value(_method_named(cls, "restore_model")) is False


def test_load_model_sleeps_before_snapshot() -> None:
    load_model = _method_named(_llm_service_class(), "load_model")
    source = ast.unparse(load_model)
    assert ".sleep(level=1)" in source


def test_restore_model_wakes_after_snapshot() -> None:
    restore_model = _method_named(_llm_service_class(), "restore_model")
    source = ast.unparse(restore_model)
    assert ".wake_up()" in source


def test_llm_service_enables_gpu_memory_snapshot() -> None:
    source = _llm_app_source()
    assert "enable_memory_snapshot=True" in source
    assert '"enable_gpu_snapshot": True' in source
