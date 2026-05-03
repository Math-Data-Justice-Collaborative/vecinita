"""Regression tests for gateway-owned Modal scraper persistence."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_reraise_psycopg_sanitized_dns_style(monkeypatch):
    """``_reraise_psycopg_sanitized`` maps fake psycopg-style errors without real psycopg2.

    Session ``conftest`` stubs ``sys.modules['psycopg2']`` for agent imports, so
    ``modal_scraper_persist`` may load with ``Json is None``; test the sanitizer in isolation.
    """
    from src.services.ingestion import modal_scraper_persist as msp

    class FakePsycopg:
        class Error(Exception):
            pass

    class ConnErr(FakePsycopg.Error):
        pass

    monkeypatch.setattr(msp, "psycopg2", FakePsycopg)
    with pytest.raises(RuntimeError) as ei:
        msp._reraise_psycopg_sanitized(
            ConnErr(
                'could not translate host name "dpg-test123" to address: Name or service not known\n'
            )
        )
    assert "dpg-" not in str(ei.value).lower()


def test_reraise_psycopg_sanitized_non_db_raises_through():
    from src.services.ingestion import modal_scraper_persist as msp

    with pytest.raises(ValueError, match="boom"):
        msp._reraise_psycopg_sanitized(ValueError("boom"))
