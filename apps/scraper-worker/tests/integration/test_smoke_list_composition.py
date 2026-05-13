"""Verify smoke URL list meets SC-001 composition (no network)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.mark.integration
def test_smoke_yaml_has_required_kinds() -> None:
    yaml_path = Path(__file__).resolve().parents[2] / "smoke" / "crawl_smoke_urls.yaml"
    text = yaml_path.read_text(encoding="utf-8")
    kinds = re.findall(r"(?m)^\s*kind:\s*(\w+)\s*$", text)
    assert kinds.count("html") >= 2
    assert "pdf" in kinds
    assert "text" in kinds
    assert "any" in kinds
    assert len(kinds) >= 5
