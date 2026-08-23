"""BUG-2026-08-22 — ingest host TLS/WAF fallbacks (#249).

[Spec: docs/bug-reports/BUG-2026-08-22-ingest-host-fallbacks.md]
[Spec: docs/test-plan.md §TC-258]

Full regression suite: tests/unit/ingest/test_scrape_host_fallbacks_ev249.py
"""

from __future__ import annotations

from tests.unit.ingest.test_scrape_host_fallbacks_ev249 import (
    test_fetch_url_retries_www_after_tls_connect_error,
)


def test_bug_2026_08_22_federalhillhouse_www_tls_retry() -> None:
    """Layer guard: apex TLS failure recovers via www host (#249)."""
    test_fetch_url_retries_www_after_tls_connect_error()
