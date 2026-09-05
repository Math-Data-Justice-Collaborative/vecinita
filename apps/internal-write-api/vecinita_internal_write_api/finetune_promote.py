"""F77 finetune adapter pin store + promote/rollback (T129.7 / TC-262 / TC-265).

Persists the human-promoted pin for the write-API process and mirrors it onto
``VECINITA_FINETUNE_ADAPTER_ID`` so ``parse_finetune_adapter_id`` / prod load
helpers stay consistent. Durable DO secret sync stays a deploy-stage concern
(AskQuestion before live prod promote — TP9).

[Corpus: feature-list.md §F77]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/config-spec.md §VECINITA_FINETUNE_ADAPTER_ID]
[Spec: docs/test-plan.md §TC-262 §TC-265]
[Spec: docs/acceptance-criteria.md §AC-FT6 §AC-FT9]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
"""

from __future__ import annotations

import os
from threading import Lock

from vecinita_shared_schemas.finetune import (
    FINETUNE_ADAPTER_ID_ENV,
    decide_adapter_pin_after_promote,
    decide_adapter_pin_after_rollback,
    parse_finetune_adapter_id,
)
from vecinita_shared_schemas.finetune_promote import (
    FinetuneAdapterPinResponse,
    FinetunePromoteRequest,
    FinetunePromoteResponse,
)


class FinetuneAdapterPinStore:
    """Thread-safe promoted adapter pin (in-process + env mirror)."""

    def __init__(self) -> None:
        """Create an empty pin store (reads env on first ``get`` if unset)."""
        self._lock = Lock()
        self._initialized = False
        self._adapter_id: str | None = None

    def _ensure_seeded(self) -> None:
        if self._initialized:
            return
        self._adapter_id = parse_finetune_adapter_id()
        self._initialized = True

    def get(self) -> str | None:
        """Return the current promoted pin, or None for base."""
        with self._lock:
            self._ensure_seeded()
            return self._adapter_id

    def promote(self, adapter_id: str) -> str:
        """Set the human-promoted pin and mirror onto env."""
        pin = decide_adapter_pin_after_promote(adapter_id)
        with self._lock:
            self._adapter_id = pin
            self._initialized = True
            os.environ[FINETUNE_ADAPTER_ID_ENV] = pin
        return pin

    def rollback(self) -> None:
        """Clear the promoted pin → prod serves base (TC-265 / AC-FT9)."""
        decide_adapter_pin_after_rollback()
        with self._lock:
            self._adapter_id = None
            self._initialized = True
            os.environ[FINETUNE_ADAPTER_ID_ENV] = ""

    def clear(self) -> None:
        """Reset store + env (tests)."""
        with self._lock:
            self._adapter_id = None
            self._initialized = True
            _ = os.environ.pop(FINETUNE_ADAPTER_ID_ENV, None)


_STORE = FinetuneAdapterPinStore()


def get_finetune_adapter_pin_store() -> FinetuneAdapterPinStore:
    """Process-wide FT adapter pin store."""
    return _STORE


def apply_finetune_promote(request: FinetunePromoteRequest) -> FinetunePromoteResponse:
    """Apply human promote or clear-pin rollback (never auto-promotes)."""
    store = get_finetune_adapter_pin_store()
    if request.rollback:
        store.rollback()
        return FinetunePromoteResponse(
            promoted=False,
            adapter_id=None,
            base=True,
            auto_promote=False,
        )
    adapter_id = request.adapter_id
    if adapter_id is None:
        msg = "adapter_id is required unless rollback is true"
        raise ValueError(msg)
    pin = store.promote(adapter_id)
    return FinetunePromoteResponse(
        promoted=True,
        adapter_id=pin,
        base=False,
        auto_promote=False,
    )


def get_finetune_adapter_pin() -> FinetuneAdapterPinResponse:
    """Current prod pin for GET parity (TC-262)."""
    pin = get_finetune_adapter_pin_store().get()
    return FinetuneAdapterPinResponse(adapter_id=pin, base=pin is None)
