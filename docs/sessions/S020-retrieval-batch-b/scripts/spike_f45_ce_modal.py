"""Modal-only cross-encoder scorer for EV-017 F45 spike (no local package imports).

Ephemeral T4 app for ``BAAI/bge-reranker-v2-m3`` (RD-204, S020-D11/D15).
ChatRAG must not use the playground URL — this spike is standalone.
"""

from __future__ import annotations

import modal

CE_MODEL = "BAAI/bge-reranker-v2-m3"

app = modal.App("vecinita-spike-f45-rerank")
ce_volume = modal.Volume.from_name("spike-f45-rerank-models", create_if_missing=True)
ce_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0,<4",
        "torch>=2.2,<3",
        "transformers>=4.40,<5",
    )
)


@app.cls(
    image=ce_image,
    gpu="T4",
    volumes={"/models": ce_volume},
    timeout=900,
    scaledown_window=120,
)
class CrossEncoderRerank:
    """Cross-encoder scorer for F45 spike (Modal T4)."""

    @modal.enter()
    def load(self) -> None:
        """Load ``CE_MODEL`` onto the T4 and warm one pair (Modal enter hook)."""
        import os

        from sentence_transformers import CrossEncoder

        os.environ.setdefault("HF_HOME", "/models/hf")
        os.environ.setdefault("TRANSFORMERS_CACHE", "/models/hf")
        self._model = CrossEncoder(CE_MODEL, device="cuda")
        _ = self._model.predict([["warmup query", "warmup passage"]])
        ce_volume.commit()

    @modal.method()
    def score_batches(self, batches: list[dict[str, object]]) -> list[list[float]]:
        """Score each batch: ``{"query": str, "passages": list[str]}`` → scores."""
        out: list[list[float]] = []
        for batch in batches:
            query = str(batch["query"])
            passages_obj = batch["passages"]
            if not isinstance(passages_obj, list):
                msg = "batch['passages'] must be a list"
                raise TypeError(msg)
            passages = [str(p) for p in passages_obj]
            if not passages:
                out.append([])
                continue
            pairs = [[query, p] for p in passages]
            scores = self._model.predict(pairs)
            out.append([float(s) for s in scores])
        return out
