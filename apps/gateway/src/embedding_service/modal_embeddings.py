"""Embeddings via Modal ``Function.remote`` (no ``*.modal.run`` HTTP)."""

from __future__ import annotations

import os
from typing import cast

from langchain_core.embeddings import Embeddings

from src.services.modal.invoker import invoke_modal_embedding_batch, invoke_modal_embedding_single


class ModalSdkEmbeddings(Embeddings):
    """LangChain-compatible embeddings using deployed Modal functions."""

    def __init__(self, *, logical_url: str | None = None) -> None:
        app = os.getenv("MODAL_EMBEDDING_APP_NAME", "vecinita-embedding")
        self.base_url = logical_url or f"modal://{app}/embed_query"

    def validate_connection(self) -> str:
        """Cheap remote check: single-token embedding round-trip."""
        _ = self.embed_query("ok")
        return self.base_url

    def embed_query(self, text: str) -> list[float]:
        data = invoke_modal_embedding_single(text)
        vec = data.get("embedding")
        if not isinstance(vec, list):
            raise RuntimeError("Modal embed_query returned no embedding list")
        return cast(list[float], vec)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        data = invoke_modal_embedding_batch(texts)
        raw = data.get("embeddings")
        if not isinstance(raw, list):
            raise RuntimeError("Modal embed_batch returned no embeddings list")
        return cast(list[list[float]], raw)

    async def aembed_query(self, text: str) -> list[float]:
        return self.embed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.embed_documents(texts)
