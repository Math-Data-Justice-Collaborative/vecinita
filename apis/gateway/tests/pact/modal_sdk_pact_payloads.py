"""Shared JSON envelopes for gateway ↔ Modal SDK sync message pacts (tests only)."""

from __future__ import annotations

# Consumer request bodies (what the gateway "sends" to the Modal SDK boundary).
MODAL_RPC_REQUESTS: dict[str, dict] = {
    "modal_rpc_embedding_single": {"kind": "invoke_modal_embedding_single", "text": "hello pact"},
    "modal_rpc_embedding_batch": {
        "kind": "invoke_modal_embedding_batch",
        "texts": ["a", "b"],
    },
    "modal_rpc_model_chat": {
        "kind": "invoke_modal_model_chat",
        "model": "gemma3",
        "messages": [{"role": "user", "content": "ping"}],
        "temperature": 0.2,
    },
    "modal_rpc_scraper_submit": {
        "kind": "invoke_modal_scrape_job_submit",
        "payload": {
            "url": "https://example.com/pact",
            "user_id": "u1",
            "metadata": {"correlation_id": "cid-pact"},
        },
    },
    "modal_rpc_scraper_get": {"kind": "invoke_modal_scrape_job_get", "job_id": "job-1"},
    "modal_rpc_scraper_list": {
        "kind": "invoke_modal_scrape_job_list",
        "user_id": "u1",
        "limit": 7,
    },
    "modal_rpc_scraper_cancel": {"kind": "invoke_modal_scrape_job_cancel", "job_id": "job-1"},
}

# Modal-side responses (what ``.remote()`` is expected to return for contract tests).
MODAL_RPC_RESPONSES: dict[str, dict] = {
    "modal_rpc_embedding_single": {
        "embedding": [0.1, 0.2, 0.3],
        "model": "m1",
        "dimension": 3,
    },
    "modal_rpc_embedding_batch": {
        "embeddings": [[0.1], [0.2]],
        "model": "m1",
        "dimension": 1,
    },
    "modal_rpc_model_chat": {"message": {"role": "assistant", "content": "pong"}},
    "modal_rpc_scraper_submit": {
        "ok": True,
        "data": {
            "job_id": "job-1",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00",
            "url": "https://example.com/pact",
        },
    },
    "modal_rpc_scraper_get": {
        "ok": True,
        "data": {
            "job_id": "job-1",
            "status": "completed",
            "created_at": "2024-01-01T00:00:00",
            "url": "https://example.com/pact",
        },
    },
    "modal_rpc_scraper_list": {
        "ok": True,
        "data": {"jobs": [{"job_id": "job-1", "status": "pending"}], "total": 1},
    },
    "modal_rpc_scraper_cancel": {
        "ok": True,
        "data": {
            "job_id": "job-1",
            "status": "cancelled",
            "created_at": "2024-01-01T00:00:00",
            "url": "https://example.com/pact",
        },
    },
}
