"""TC-319-01 / EV-319: prod LLM scaledown_window is import-time env config.

[Corpus: config]
[Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md]
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from _pytest.monkeypatch import MonkeyPatch

_REPO = Path(__file__).resolve().parents[3]
_LLM_APP = Path(__file__).resolve().parents[3] / "infra" / "modal" / "llm_app.py"
_ENV_NAME = "VECINITA_LLM_SCALEDOWN_WINDOW"


def _identity_decorator(*_args: object, **_kwargs: object) -> Callable[[object], object]:
    def _decorate(target: object) -> object:
        return target

    return _decorate


class _StubApp:
    def __init__(self, _name: str) -> None:
        pass

    def function(self, *_args: object, **_kwargs: object) -> Callable[[object], object]:
        return _identity_decorator()

    def cls(self, *_args: object, **_kwargs: object) -> Callable[[object], object]:
        return _identity_decorator()


class _StubImage:
    @classmethod
    def debian_slim(cls, *_args: object, **_kwargs: object) -> _StubImage:
        return cls()

    def pip_install(self, *_args: object, **_kwargs: object) -> _StubImage:
        return self

    def env(self, *_args: object, **_kwargs: object) -> _StubImage:
        return self

    def add_local_dir(self, *_args: object, **_kwargs: object) -> _StubImage:
        return self

    def imports(self) -> object:
        return nullcontext()


class _StubVolume:
    @classmethod
    def from_name(cls, *_args: object, **_kwargs: object) -> _StubVolume:
        return cls()

    def commit(self) -> None:
        pass


class _StubDict:
    @classmethod
    def from_name(cls, *_args: object, **_kwargs: object) -> dict[str, object]:
        return {}


class _StubSecret:
    @classmethod
    def from_name(cls, *_args: object, **_kwargs: object) -> object:
        return object()


class _StubLLM:
    pass


class _StubSamplingParams:
    def __init__(self, *_args: object, **_kwargs: object) -> None:
        pass


def _install_import_stubs(monkeypatch: MonkeyPatch) -> None:
    modal = ModuleType("modal")
    modal.App = _StubApp
    modal.Image = _StubImage
    modal.Volume = _StubVolume
    modal.Dict = _StubDict
    modal.Secret = _StubSecret
    modal.enter = _identity_decorator
    modal.exit = _identity_decorator
    modal.method = _identity_decorator
    modal.asgi_app = _identity_decorator
    monkeypatch.setitem(sys.modules, "modal", modal)

    vllm = ModuleType("vllm")
    vllm.LLM = _StubLLM
    vllm.SamplingParams = _StubSamplingParams
    monkeypatch.setitem(sys.modules, "vllm", vllm)


def _import_llm_app(monkeypatch: MonkeyPatch, raw: str | None) -> ModuleType:
    if raw is None:
        monkeypatch.delenv(_ENV_NAME, raising=False)
    else:
        monkeypatch.setenv(_ENV_NAME, raw)
    _install_import_stubs(monkeypatch)
    monkeypatch.syspath_prepend(str(_REPO))
    sys.modules.pop("infra.modal.llm_app", None)
    spec = importlib.util.spec_from_file_location("infra.modal.llm_app", _LLM_APP)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "infra.modal.llm_app", module)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, 300),
        ("120", 120),
    ],
)
def test_scaledown_window_from_env_accepts_default_and_valid_candidate(
    monkeypatch: MonkeyPatch,
    raw: str | None,
    expected: int,
) -> None:
    """TC-319-01: unset defaults to 300; deploy-time candidate 120 is accepted."""
    module = _import_llm_app(monkeypatch, raw)
    helper = vars(module)["_scaledown_window_from_env"]
    assert callable(helper)
    assert helper() == expected
    assert vars(module)["_PROD_SCALEDOWN_WINDOW"] == expected


@pytest.mark.parametrize("raw", ["59", "601", "not-an-int"])
def test_scaledown_window_from_env_rejects_invalid_values(
    monkeypatch: MonkeyPatch,
    raw: str,
) -> None:
    """TC-319-01: invalid deploy-time scaledown config fails closed."""
    with pytest.raises(ValueError, match=_ENV_NAME):
        _import_llm_app(monkeypatch, raw)


def test_llm_service_uses_import_time_scaledown_window_constant() -> None:
    """TC-319-01: Modal class decorator uses the parsed prod scaledown window."""
    source = _LLM_APP.read_text(encoding="utf-8")
    tree = ast.parse(source)
    service = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "LlmService"
    )
    app_cls = next(
        dec
        for dec in service.decorator_list
        if isinstance(dec, ast.Call)
        and isinstance(dec.func, ast.Attribute)
        and dec.func.attr == "cls"
    )
    keywords = {keyword.arg: keyword.value for keyword in app_cls.keywords}
    assert isinstance(keywords["scaledown_window"], ast.Name)
    assert keywords["scaledown_window"].id == "_PROD_SCALEDOWN_WINDOW"
    assert "min_containers" not in keywords
    assert "buffer_containers" not in keywords
