"""Optional live smoke crawl (opt-in with ``-m live``)."""

from __future__ import annotations

import pytest


@pytest.mark.live
@pytest.mark.asyncio
async def test_smoke_placeholder() -> None:
    """Reserved for operator-approved live smoke runs (see smoke/crawl_smoke_urls.yaml)."""
    pytest.skip("Live smoke crawl is manual; enable when running against approved URLs.")
