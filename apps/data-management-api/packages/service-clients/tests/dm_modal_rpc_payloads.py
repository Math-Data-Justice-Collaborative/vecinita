"""Stable JSON shapes for DM ``service_clients`` ↔ Modal SDK sync message pacts (tests only)."""

from __future__ import annotations

# Normalized request/response envelopes documented alongside ``modal_invoker`` helpers.
DM_MODAL_RPC_REQUESTS: dict[str, dict] = {
    "dm_modal_embedding_single": {
        "op": "embedding_embed_query",
        "text": "dm pact text",
        "model_version": None,
    },
    "dm_modal_model_predict": {
        "op": "model_predict",
        "text": "dm pact classify",
        "model_version": "v-pact",
    },
    "dm_modal_scraper_health": {
        "op": "scraper_health",
    },
}

DM_MODAL_RPC_RESPONSES: dict[str, dict] = {
    "dm_modal_embedding_single": {
        "embedding": [0.1, -0.1, 0.2],
        "model_version": "dm-emb-v1",
    },
    "dm_modal_model_predict": {
        "label": "pact_label",
        "score": 0.88,
        "model_version": "v-pact",
    },
    "dm_modal_scraper_health": {
        "status": "ok",
        "service": "vecinita-scraper",
        "source": "modal",
    },
}
