"""Operations exercised by ``test_agent_openapi_stable_operations``.

TraceCov uses the same set so ``--tracecov-fail-under=100`` matches the
skipped-heavy allowlist (see ``test_agent_api_schema_schemathesis.py``).
"""

from __future__ import annotations

AGENT_STABLE_OPERATIONS = frozenset(
    {
        ("GET", "/"),
        ("GET", "/health"),
        ("GET", "/config"),
        ("GET", "/privacy"),
        ("GET", "/model-selection"),
    }
)
