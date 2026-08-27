r"""TC-145 / RD-169 / TP-S010-25/27: prod pin vs playground reload; URL routing (Slice D).

Locks engine isolation for M80:
- ``vecinita-llm`` (prod) ignores request ``model_id`` for vLLM reload (pinned).
- ``vecinita-llm-playground`` is a separate Modal app on shared ``llm-models``.
- ``resolve_llm_http_config(purpose="playground")`` reads
  ``VECINITA_MODAL_LLM_PLAYGROUND_URL``; ChatRAG stays on prod URL only.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import sys
from pathlib import Path
from typing import Final, cast

import pytest
from vecinita_shared_schemas.llm_http import LlmHttpConfig, resolve_llm_http_config

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from infra.modal import llm_app  # noqa: E402
from infra.modal.llm_app import APP_NAME as PROD_APP_NAME  # noqa: E402
from infra.modal.llm_app import (  # noqa: E402
    DEFAULT_PLAYGROUND_MODEL_ID,
    MODEL_ID,
    _resolve_vllm_model_arg,  # pyright: ignore[reportPrivateUsage]  # pin contract under test
)
from infra.modal.llm_app import VOLUME_NAME as PROD_VOLUME_NAME  # noqa: E402

_PLAYGROUND_APP_PATH: Final[Path] = _REPO_ROOT / "infra" / "modal" / "llm_playground_app.py"
_CHAT_RAG_CONFIG: Final[Path] = (
    _REPO_ROOT / "apps" / "chat-rag-backend" / "vecinita_chat_rag_backend" / "config.py"
)
_ALT_PLAYGROUND_TAG: Final[str] = "qwen3:8b"
_ENV_PLAYGROUND: Final[str] = "VECINITA_MODAL_LLM_PLAYGROUND_URL"
_ENV_PROD: Final[str] = "VECINITA_MODAL_LLM_URL"


def _import_playground_app() -> object:
    """Load the playground Modal app module (T80.2). Missing module is the red phase."""
    if not _PLAYGROUND_APP_PATH.is_file():
        pytest.fail(
            "infra/modal/llm_playground_app.py missing "
            + "(T80.2 / TP-S010-25 / RD-169 / TC-145): "
            + "deploy vecinita-llm-playground as a second Modal app sharing llm-models"
        )
    try:
        return importlib.import_module("infra.modal.llm_playground_app")
    except ModuleNotFoundError as exc:
        pytest.fail(
            f"infra.modal.llm_playground_app import failed (T80.2 / TP-S010-25 / TC-145): {exc}"
        )


def test_prod_app_name_and_volume_constants() -> None:
    """Prod app remains vecinita-llm on the shared llm-models volume (TP-S010-28)."""
    assert PROD_APP_NAME == "vecinita-llm"
    assert PROD_VOLUME_NAME == "llm-models"
    assert MODEL_ID == "Qwen/Qwen2.5-1.5B-Instruct"
    assert DEFAULT_PLAYGROUND_MODEL_ID == "qwen2.5:1.5b-instruct"


def test_prod_disallows_model_reload_flag() -> None:
    """Prod pin: ALLOW_MODEL_RELOAD must be False so playground tags cannot stomp ChatRAG."""
    allow = getattr(llm_app, "ALLOW_MODEL_RELOAD", None)
    assert allow is False, (
        "infra.modal.llm_app.ALLOW_MODEL_RELOAD must be False "
        + "(T80.3 / RD-169 / TP-S010-25 / TC-145 / AC-E38): "
        + "prod class must ignore playground model_id reloads"
    )


def test_prod_resolve_vllm_model_arg_ignores_playground_tag() -> None:
    """Pinned prod engine always loads Qwen2.5-1.5B even when request carries another tag."""
    allow = getattr(llm_app, "ALLOW_MODEL_RELOAD", None)
    if allow is not False:
        pytest.fail(
            "ALLOW_MODEL_RELOAD is not False - cannot assert prod pin yet (T80.3 / RD-169 / TC-145)"
        )
    resolved = _resolve_vllm_model_arg(_ALT_PLAYGROUND_TAG)
    assert resolved == MODEL_ID, (
        f"prod _resolve_vllm_model_arg({_ALT_PLAYGROUND_TAG!r}) must return pinned "
        + f"{MODEL_ID!r}, got {resolved!r} (T80.3 / RD-169 / TC-145)"
    )
    assert _resolve_vllm_model_arg(None) == MODEL_ID
    assert _resolve_vllm_model_arg(DEFAULT_PLAYGROUND_MODEL_ID) == MODEL_ID


def test_playground_app_name_and_shared_volume() -> None:
    """Playground Modal app is a separate deployable sharing llm-models (TP-S010-25/28)."""
    playground = _import_playground_app()
    assert getattr(playground, "APP_NAME", None) == "vecinita-llm-playground", (
        "llm_playground_app.APP_NAME must be 'vecinita-llm-playground' (TP-S010-25)"
    )
    assert getattr(playground, "VOLUME_NAME", None) == PROD_VOLUME_NAME == "llm-models", (
        "playground must mount the same llm-models volume as prod (TP-S010-28)"
    )


def test_playground_app_allows_model_reload() -> None:
    """Playground app may reload vLLM on model_id (~60-120s); prod must not."""
    playground = _import_playground_app()
    allow = getattr(playground, "ALLOW_MODEL_RELOAD", None)
    assert allow is True, (
        "infra.modal.llm_playground_app.ALLOW_MODEL_RELOAD must be True "
        + "(T80.2 / RD-169 / TP-S010-25): sandbox eval/list-pull may switch model_id"
    )


def test_resolve_llm_http_config_accepts_purpose_parameter() -> None:
    """Shared resolver must expose purpose=prod|playground (TP-S010-20/27)."""
    params = inspect.signature(resolve_llm_http_config).parameters
    assert "purpose" in params, (
        "resolve_llm_http_config must accept purpose='prod'|'playground' "
        + "(T80.4 / TP-S010-27 / TC-145): route list/pull/eval via "
        + "VECINITA_MODAL_LLM_PLAYGROUND_URL"
    )


def test_resolve_llm_http_config_playground_prefers_playground_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """purpose=playground reads VECINITA_MODAL_LLM_PLAYGROUND_URL over prod URL."""
    if "purpose" not in inspect.signature(resolve_llm_http_config).parameters:
        pytest.fail("resolve_llm_http_config missing purpose= (T80.4 / TP-S010-27 / TC-145)")
    monkeypatch.setenv(_ENV_PLAYGROUND, "https://playground.example/")
    monkeypatch.setenv(_ENV_PROD, "https://prod.example/")
    config = cast(
        "LlmHttpConfig",
        resolve_llm_http_config(purpose="playground"),  # type: ignore[call-arg]
    )
    assert config.base_url == "https://playground.example"


def test_resolve_llm_http_config_prod_ignores_playground_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default/prod purpose must never pick the playground Modal URL (TP-S010-27)."""
    monkeypatch.setenv(_ENV_PLAYGROUND, "https://playground.example/")
    monkeypatch.setenv(_ENV_PROD, "https://prod.example/")
    config = resolve_llm_http_config()
    assert config.base_url == "https://prod.example"
    if "purpose" in inspect.signature(resolve_llm_http_config).parameters:
        prod = cast(
            "LlmHttpConfig",
            resolve_llm_http_config(purpose="prod"),  # type: ignore[call-arg]
        )
        assert prod.base_url == "https://prod.example"


def test_chat_rag_config_does_not_read_playground_url() -> None:
    """ChatRAG must only use VECINITA_MODAL_LLM_URL - never the playground app URL."""
    source = _CHAT_RAG_CONFIG.read_text(encoding="utf-8")
    assert _ENV_PLAYGROUND not in source, (
        "chat-rag config must not reference VECINITA_MODAL_LLM_PLAYGROUND_URL "
        + "(TP-S010-27 / ADR-037): ChatRAG stays on prod vecinita-llm"
    )
    tree = ast.parse(source)
    string_literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert _ENV_PLAYGROUND not in string_literals
