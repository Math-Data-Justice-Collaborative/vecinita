"""Modal multi-model embedder for EV-016 #159 spike (E0/E1/E2).

Uses sentence-transformers (not FastEmbed) because FastEmbed 0.4–0.6 does not
ship ``intfloat/multilingual-e5-small`` (E1). Spike-only; prod stays FastEmbed
``BAAI/bge-small-en-v1.5``.
"""

from __future__ import annotations

import modal

app = modal.App("vecinita-spike-embed-models")
volume = modal.Volume.from_name("spike-embed-models", create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0,<4",
        "torch>=2.2,<3",
        "numpy>=1.26,<3",
    )
)

MODELS = {
    "E0": "BAAI/bge-small-en-v1.5",
    "E1": "intfloat/multilingual-e5-small",
    "E2": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
}


def _prepare_texts(cell_id: str, texts: list[str], *, for_query: bool) -> list[str]:
    """Apply e5 query/passage prefixes for E1 only."""
    if cell_id != "E1":
        return texts
    prefix = "query: " if for_query else "passage: "
    return [prefix + text for text in texts]


@app.cls(
    image=image,
    volumes={"/models": volume},
    timeout=1800,
    scaledown_window=120,
    cpu=2.0,
    memory=8192,
)
class MultiEmbedSpike:
    """Embed texts with E0/E1/E2 (384-d sentence-transformers)."""

    @modal.enter()
    def load(self) -> None:
        import os

        from sentence_transformers import SentenceTransformer

        os.environ.setdefault("HF_HOME", "/models/hf")
        os.environ.setdefault("TRANSFORMERS_CACHE", "/models/hf")
        self._models: dict[str, SentenceTransformer] = {}
        for cell_id, name in MODELS.items():
            model = SentenceTransformer(name, cache_folder="/models/hf")
            _ = model.encode(["warmup"], normalize_embeddings=True)
            self._models[cell_id] = model
        volume.commit()

    @modal.method()
    def embed_batch(
        self,
        cell_id: str,
        texts: list[str],
        *,
        for_query: bool = False,
    ) -> list[list[float]]:
        """Embed ``texts``. Set ``for_query=True`` for E1 query prefixes."""
        if cell_id not in self._models:
            msg = f"unknown cell_id {cell_id!r}; expected one of {sorted(self._models)}"
            raise ValueError(msg)
        model = self._models[cell_id]
        prepared = _prepare_texts(cell_id, texts, for_query=for_query)
        vectors = model.encode(prepared, normalize_embeddings=True, show_progress_bar=False)
        return [vector.tolist() for vector in vectors]
