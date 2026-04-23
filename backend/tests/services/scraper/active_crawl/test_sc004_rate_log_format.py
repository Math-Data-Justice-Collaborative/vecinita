"""SC-004: stable structured log line shape for active_crawl_rate."""

from __future__ import annotations

import re


def test_active_crawl_rate_line_regex() -> None:
    line = (
        "active_crawl_rate crawl_run_id=550e8400-e29b-41d4-a716-446655440000 "
        "host=example.com delta_ms=120 retrieval_mode=static_first ok=True loader=Playwright"
    )
    pat = re.compile(
        r"^active_crawl_rate crawl_run_id=[0-9a-f-]{36} host=\S+ delta_ms=\d+ "
        r"retrieval_mode=\S+ ok=(True|False) loader=\S+$"
    )
    assert pat.match(line)
