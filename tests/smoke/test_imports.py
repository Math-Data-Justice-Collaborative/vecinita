"""Smoke-import all workspace Python packages (M1 / T1.4)."""

from __future__ import annotations

import importlib
from typing import Final

import pytest

WORKSPACE_PACKAGES: Final[tuple[str, ...]] = (
    "vecinita_rag",
    "vecinita_ingest",
    "vecinita_embedding_client",
    "vecinita_llm_client",
    "vecinita_tagging",
    "vecinita_shared_schemas",
    "vecinita_chat_rag_backend",
    "vecinita_data_management_backend",
    "vecinita_database",
    "vecinita_internal_write_api",
)


@pytest.mark.parametrize("module_name", WORKSPACE_PACKAGES)
def test_import_workspace_package(module_name: str) -> None:
    module = importlib.import_module(module_name)
    version: object = getattr(module, "__version__", None)
    assert version == "0.1.0"
