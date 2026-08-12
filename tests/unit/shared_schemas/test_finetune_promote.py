"""T129.7 — F77 promote / rollback request-response schemas (TC-262 / TC-265).

[Corpus: feature-list.md §F77]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/test-plan.md §TC-262 §TC-265]
[Spec: docs/acceptance-criteria.md §AC-FT6 §AC-FT9]
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.finetune_promote import (
    FinetuneAdapterPinResponse,
    FinetunePromoteRequest,
    FinetunePromoteResponse,
)


def test_promote_request_requires_adapter_id_when_not_rollback() -> None:
    """Human promote body must carry a non-empty adapter_id (RD-339)."""
    req = FinetunePromoteRequest(adapter_id="  adapter-v3  ")
    assert req.adapter_id == "adapter-v3"
    assert req.rollback is False

    with pytest.raises(ValidationError):
        FinetunePromoteRequest(adapter_id="   ")

    with pytest.raises(ValidationError):
        FinetunePromoteRequest()


def test_promote_request_rollback_clears_without_adapter_id() -> None:
    """AC-FT9 / TC-265: rollback=true clears pin; adapter_id optional."""
    req = FinetunePromoteRequest(rollback=True)
    assert req.rollback is True
    assert req.adapter_id is None


def test_promote_response_shape_and_no_auto_promote() -> None:
    """Promote response exposes pin state; auto_promote always false (RD-338)."""
    promoted = FinetunePromoteResponse(
        promoted=True,
        adapter_id="adapter-v3",
        base=False,
    )
    assert promoted.promoted is True
    assert promoted.adapter_id == "adapter-v3"
    assert promoted.base is False
    assert promoted.auto_promote is False

    rolled = FinetunePromoteResponse(
        promoted=False,
        adapter_id=None,
        base=True,
    )
    assert rolled.promoted is False
    assert rolled.adapter_id is None
    assert rolled.base is True
    assert rolled.auto_promote is False

    with pytest.raises(ValidationError):
        FinetunePromoteResponse(
            promoted=True,
            adapter_id="x",
            base=False,
            auto_promote=True,  # type: ignore[arg-type]
        )


def test_adapter_pin_get_response_base_or_promoted() -> None:
    """GET pin parity: None/empty → base; non-empty → promoted id (TC-262)."""
    base = FinetuneAdapterPinResponse(adapter_id=None, base=True)
    assert base.adapter_id is None
    assert base.base is True

    pinned = FinetuneAdapterPinResponse(adapter_id="adapter-v3", base=False)
    assert pinned.adapter_id == "adapter-v3"
    assert pinned.base is False
