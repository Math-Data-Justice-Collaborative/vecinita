"""Unit tests for corpus test-artifact URL classifier (HF corpus cleanup).

[Corpus: corpus-db-safety] [Spec: docs/bug-reports/BUG-2026-07-02-staging-corpus-wipe-prevention.md]
"""

from __future__ import annotations

import pytest

from tests.helpers.corpus_test_artifacts import (
    TEST_ARTIFACT_URL_SQL_PREDICATE,
    is_corpus_test_artifact_url,
)

pytestmark = pytest.mark.unit

_SHOULD_MATCH = (
    "https://example.com/",
    "https://batch-upsert-abc123.example.com/",
    "https://test.example.com/uj017-deadbeef",
    "https://e2e-rebuild-92a16ff83c.example.com",
    "https://tree.example.com/guides/a.html",
    "fixture://corpus/en/community-resources.md",
    "http://localhost:8080/doc",
    "http://127.0.0.1:5432/x",
)

_SHOULD_NOT_MATCH = (
    "https://www.rifreeclinic.org/services",
    "https://wrwc.org/programs",
    "https://vecina.wrwc.org/es/",
    "https://www.providenceri.gov/planning/",
    "https://drive.google.com/file/d/abc",
    "",
)


@pytest.mark.parametrize("url", _SHOULD_MATCH)
def test_is_corpus_test_artifact_url_matches_synthetic_hosts(url: str) -> None:
    """Classifier flags example.com / fixture:// / localhost URLs."""
    assert is_corpus_test_artifact_url(url) is True


@pytest.mark.parametrize("url", _SHOULD_NOT_MATCH)
def test_is_corpus_test_artifact_url_keeps_community_hosts(url: str) -> None:
    """Classifier never flags real community document URLs."""
    assert is_corpus_test_artifact_url(url) is False


def test_sql_predicate_mentions_example_fixture_and_localhost() -> None:
    """SQL fragment used by cleanup/audit must cover all three artifact classes."""
    predicate = TEST_ARTIFACT_URL_SQL_PREDICATE.lower()
    assert "example.com" in predicate
    assert "fixture://" in predicate
    assert "localhost" in predicate
    assert "127.0.0.1" in predicate
