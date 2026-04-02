"""Schemathesis hooks for schema coverage reporting."""

try:
    import tracecov
except Exception:  # pragma: no cover - optional during partial installs
    tracecov = None

if tracecov is not None:
    tracecov.schemathesis.install()
