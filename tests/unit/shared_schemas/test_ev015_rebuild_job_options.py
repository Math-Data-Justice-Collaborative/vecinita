"""T88.1 — JobOptions rebuild validation (modes, force, dry_run, document_ids).

TC-161 / TC-162 / TC-166 / RD-189-192.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError
from vecinita_shared_schemas.data_management import CreateJobRequest, JobOptions
from vecinita_shared_schemas.json_types import as_json_object


@pytest.mark.parametrize("mode", ["reembed", "rechunk", "rescrape"])
def test_rebuild_accepts_all_modes(mode: str) -> None:
    """TC-162: reembed / rechunk / rescrape are valid rebuild modes (RD-189)."""
    options = JobOptions.model_validate({"job_type": "rebuild", "mode": mode})
    payload = as_json_object(options.model_dump(mode="python"))
    assert payload.get("job_type") == "rebuild"
    assert payload.get("mode") == mode


def test_rebuild_requires_mode() -> None:
    """TC-161: mode is required when job_type is rebuild."""
    with pytest.raises(ValidationError) as exc_info:
        _ = JobOptions.model_validate({"job_type": "rebuild"})
    assert any(
        err.get("type") == "value_error" and "mode" in str(err.get("msg", "")).lower()
        for err in exc_info.value.errors()
    ), exc_info.value.errors()


def test_rebuild_rejects_unknown_mode() -> None:
    """Invalid rebuild mode is rejected at the schema boundary."""
    with pytest.raises(ValidationError):
        _ = JobOptions.model_validate({"job_type": "rebuild", "mode": "reindex"})


def test_rebuild_force_and_dry_run_defaults_and_flags() -> None:
    """TC-162 / RD-191: force and dry_run are optional bools (default false)."""
    defaults = JobOptions.model_validate({"job_type": "rebuild", "mode": "rechunk"})
    default_payload = as_json_object(defaults.model_dump(mode="python"))
    assert default_payload.get("force") is False
    assert default_payload.get("dry_run") is False

    flagged = JobOptions.model_validate(
        {
            "job_type": "rebuild",
            "mode": "reembed",
            "force": True,
            "dry_run": True,
        }
    )
    flagged_payload = as_json_object(flagged.model_dump(mode="python"))
    assert flagged_payload.get("force") is True
    assert flagged_payload.get("dry_run") is True


def test_rebuild_document_ids_optional_scope() -> None:
    """TC-166 / RD-192: optional document_ids scopes rebuild; omit = whole corpus."""
    whole = JobOptions.model_validate({"job_type": "rebuild", "mode": "rechunk"})
    whole_payload = as_json_object(whole.model_dump(mode="python"))
    assert whole_payload.get("document_ids") is None

    doc_id = uuid4()
    scoped = JobOptions.model_validate(
        {
            "job_type": "rebuild",
            "mode": "reembed",
            "document_ids": [str(doc_id)],
            "force": True,
        }
    )
    scoped_payload = as_json_object(scoped.model_dump(mode="python"))
    assert scoped_payload.get("document_ids") == [doc_id]


def test_create_job_rebuild_allows_empty_urls() -> None:
    """TC-161: rebuild enqueue may omit urls (store-backed default)."""
    model = CreateJobRequest.model_validate(
        {
            "urls": [],
            "options": {
                "job_type": "rebuild",
                "mode": "rechunk",
                "force": True,
                "dry_run": False,
            },
        }
    )
    assert model.options is not None
    payload = as_json_object(model.options.model_dump(mode="python"))
    assert payload.get("job_type") == "rebuild"
    assert payload.get("mode") == "rechunk"
    assert payload.get("force") is True
