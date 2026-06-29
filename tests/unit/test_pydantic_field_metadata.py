"""Guard: Vecinita Pydantic models must not emit UnsupportedFieldAttributeWarning."""

from __future__ import annotations

import importlib
import warnings

import pytest
from pydantic.warnings import UnsupportedFieldAttributeWarning

pytestmark = pytest.mark.unit

# Modules that define or re-export Pydantic BaseModel schemas owned by this repo.
_OWNED_SCHEMA_MODULES = (
    "vecinita_shared_schemas.chat_rag",
    "vecinita_shared_schemas.data_management",
    "vecinita_shared_schemas.internal_write",
    "vecinita_shared_schemas.validation",
)


@pytest.mark.parametrize("module_name", _OWNED_SCHEMA_MODULES)
def test_owned_schema_modules_emit_no_field_metadata_warnings(module_name: str) -> None:
    """Importing each owned schema module emits no field metadata warnings."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UnsupportedFieldAttributeWarning)
        importlib.import_module(module_name)

    ours = [w for w in caught if issubclass(w.category, UnsupportedFieldAttributeWarning)]
    assert not ours, f"{module_name} triggered UnsupportedFieldAttributeWarning: " + "; ".join(
        str(w.message) for w in ours
    )
