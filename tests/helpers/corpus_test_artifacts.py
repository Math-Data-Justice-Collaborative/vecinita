"""Classify synthetic / pytest corpus document URLs that must not live on managed DBs.

Used by operator cleanup (`scripts/ops/cleanup_corpus_test_artifacts.py`) and unit
tests. Patterns match leftover e2e/integration inserts seen on DO Managed Postgres
(HF-prod-corpus-test-artifacts, 2026-09-03).

[Corpus: corpus-db-safety] [Corpus: no-live-prod-corpus-push]
"""

from __future__ import annotations

from urllib.parse import urlparse

# SQL WHERE fragment (column alias `url`) — keep in sync with is_corpus_test_artifact_url.
TEST_ARTIFACT_URL_SQL_PREDICATE = """(
  url ILIKE '%example.com%'
  OR url LIKE 'fixture://%'
  OR url ILIKE '%localhost%'
  OR url ILIKE '%127.0.0.1%'
)"""

# Full SELECT used by the operator cleanup script (fixed constant, not user input).
LIST_TEST_ARTIFACT_DOCUMENTS_SQL = """
SELECT id::text AS id, url, title
FROM documents
WHERE (
  url ILIKE '%example.com%'
  OR url LIKE 'fixture://%'
  OR url ILIKE '%localhost%'
  OR url ILIKE '%127.0.0.1%'
)
ORDER BY url
"""

_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def is_corpus_test_artifact_url(url: str) -> bool:
    """Return True when a document URL is a synthetic test/fixture artifact.

    True for:
    - any host under ``example.com`` (incl. subdomains used by e2e)
    - ``fixture://`` seed paths
    - ``localhost`` / ``127.0.0.1`` hosts

    Real community https URLs return False.
    """
    stripped = url.strip()
    if not stripped:
        return False
    lowered = stripped.lower()
    if lowered.startswith("fixture://"):
        return True
    parsed = urlparse(stripped)
    host = (parsed.hostname or "").lower()
    if not host:
        return "example.com" in lowered or "localhost" in lowered or "127.0.0.1" in lowered
    if host == "example.com" or host.endswith(".example.com"):
        return True
    return host in _LOCAL_HOSTS
