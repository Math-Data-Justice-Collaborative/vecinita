"""T129.7 — POST /internal/v1/finetune/promote + GET pin (F77 / TC-262 / TC-265).

[Corpus: feature-list.md §F77]
[Spec: docs/api-contract.md §EV-027 Fine-tune]
[Spec: docs/test-plan.md §TC-262 §TC-265]
[Spec: docs/acceptance-criteria.md §AC-FT6 §AC-FT9]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest
from vecinita_internal_write_api.finetune_promote import (
    FinetuneAdapterPinStore,
    apply_finetune_promote,
    get_finetune_adapter_pin_store,
)
from vecinita_shared_schemas.finetune import (
    decide_prod_adapter_pin,
    parse_finetune_adapter_id,
)
from vecinita_shared_schemas.finetune_promote import FinetunePromoteRequest

from tests.helpers.json_response import response_json_object
from tests.unit.internal_write_api.conftest import auth_headers

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_promote_sets_pin_then_rollback_clears_to_base(
    write_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-262/265: before promote prod pin is base; promote sets pin; rollback clears."""
    store = get_finetune_adapter_pin_store()
    store.clear()
    monkeypatch.delenv("VECINITA_FINETUNE_ADAPTER_ID", raising=False)

    before = write_client.get(
        "/internal/v1/finetune/adapter",
        headers=auth_headers(),
    )
    assert before.status_code == HTTPStatus.OK
    before_body = response_json_object(before)
    assert before_body == {"adapter_id": None, "base": True}
    assert parse_finetune_adapter_id() is None
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id=parse_finetune_adapter_id(),
            latest_adapter_id="adapter-latest-on-volume",
        )
        is None
    )

    promote = write_client.post(
        "/internal/v1/finetune/promote",
        headers=auth_headers(),
        json={"adapter_id": "  adapter-promoted-1  "},
    )
    assert promote.status_code == HTTPStatus.OK
    promote_body = response_json_object(promote)
    assert promote_body == {
        "promoted": True,
        "adapter_id": "adapter-promoted-1",
        "base": False,
        "auto_promote": False,
    }
    assert parse_finetune_adapter_id() == "adapter-promoted-1"
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id=parse_finetune_adapter_id(),
            latest_adapter_id="adapter-latest-on-volume",
        )
        == "adapter-promoted-1"
    )

    after_promote = write_client.get(
        "/internal/v1/finetune/adapter",
        headers=auth_headers(),
    )
    assert after_promote.status_code == HTTPStatus.OK
    assert response_json_object(after_promote) == {
        "adapter_id": "adapter-promoted-1",
        "base": False,
    }

    rollback = write_client.post(
        "/internal/v1/finetune/promote",
        headers=auth_headers(),
        json={"rollback": True},
    )
    assert rollback.status_code == HTTPStatus.OK
    rollback_body = response_json_object(rollback)
    assert rollback_body == {
        "promoted": False,
        "adapter_id": None,
        "base": True,
        "auto_promote": False,
    }
    assert parse_finetune_adapter_id() is None
    assert (
        decide_prod_adapter_pin(
            promoted_adapter_id=parse_finetune_adapter_id(),
            latest_adapter_id="adapter-latest-on-volume",
        )
        is None
    )

    after_rollback = write_client.get(
        "/internal/v1/finetune/adapter",
        headers=auth_headers(),
    )
    assert after_rollback.status_code == HTTPStatus.OK
    assert response_json_object(after_rollback) == {
        "adapter_id": None,
        "base": True,
    }


def test_promote_rejects_empty_adapter_id(write_client: TestClient) -> None:
    """Promote without rollback requires a non-empty adapter_id."""
    store = get_finetune_adapter_pin_store()
    store.clear()

    resp = write_client.post(
        "/internal/v1/finetune/promote",
        headers=auth_headers(),
        json={"adapter_id": "   "},
    )
    assert resp.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_pin_store_seeds_from_env_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """First get seeds from VECINITA_FINETUNE_ADAPTER_ID; second get is cache hit."""
    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_ID", "adapter-from-env")
    store = FinetuneAdapterPinStore()
    assert store.get() == "adapter-from-env"
    monkeypatch.setenv("VECINITA_FINETUNE_ADAPTER_ID", "should-not-reread")
    assert store.get() == "adapter-from-env"


def test_apply_promote_rejects_missing_adapter_via_construct() -> None:
    """Defensive path: apply_finetune_promote without adapter_id raises ValueError."""
    store = get_finetune_adapter_pin_store()
    store.clear()
    req = FinetunePromoteRequest.model_construct(adapter_id=None, rollback=False)
    with pytest.raises(ValueError, match="adapter_id is required"):
        apply_finetune_promote(req)
