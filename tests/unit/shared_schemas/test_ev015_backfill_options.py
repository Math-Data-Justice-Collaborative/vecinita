"""T87.2 — Backfill prefer rescrape; from_chunks requires ack (TP-S017-08 / ADR-040 §5)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.data_management import CreateJobRequest, JobOptions
from vecinita_shared_schemas.json_types import as_json_object


def test_backfill_defaults_to_rescrape_source() -> None:
    """Backfill job options default source is rescrape (TP-S017-08)."""
    options = JobOptions.model_validate(
        {
            "job_type": "rebuild",
            "mode": "rescrape",
            "backfill": True,
        }
    )
    payload = as_json_object(options.model_dump(mode="python"))
    assert payload.get("backfill") is True
    assert payload.get("backfill_source") == "rescrape"


def test_backfill_from_chunks_requires_ack_flag() -> None:
    """Reconstruct-from-chunks backfill is rejected without operator ack."""
    with pytest.raises(ValidationError) as exc_info:
        _ = JobOptions.model_validate(
            {
                "job_type": "rebuild",
                "mode": "rechunk",
                "backfill": True,
                "backfill_source": "from_chunks",
                "ack_reconstruct_from_chunks": False,
            }
        )
    # Must be the ack business rule (value_error), not merely unknown-field rejection.
    assert any(
        err.get("type") == "value_error"
        and "ack_reconstruct_from_chunks" in str(err.get("msg", ""))
        for err in exc_info.value.errors()
    ), exc_info.value.errors()


def test_backfill_from_chunks_accepted_with_ack() -> None:
    """from_chunks backfill is allowed when operator ack is true."""
    options = JobOptions.model_validate(
        {
            "job_type": "rebuild",
            "mode": "rechunk",
            "backfill": True,
            "backfill_source": "from_chunks",
            "ack_reconstruct_from_chunks": True,
            "document_ids": [str(uuid4())],
        }
    )
    payload = as_json_object(options.model_dump(mode="python"))
    assert payload.get("backfill_source") == "from_chunks"
    assert payload.get("ack_reconstruct_from_chunks") is True


def test_create_job_accepts_backfill_rescrape_without_urls() -> None:
    """Backfill/rebuild enqueue may omit urls (store or scoped document_ids)."""
    model = CreateJobRequest.model_validate(
        {
            "urls": [],
            "options": {
                "job_type": "rebuild",
                "mode": "rescrape",
                "backfill": True,
                "document_ids": [str(uuid4())],
            },
        }
    )
    assert model.options is not None
    payload = as_json_object(model.options.model_dump(mode="python"))
    assert payload.get("job_type") == "rebuild"
    assert payload.get("backfill") is True
