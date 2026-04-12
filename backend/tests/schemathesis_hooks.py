"""Schemathesis hooks for schema coverage reporting and live CLI stability."""

try:
    import tracecov
except Exception:  # pragma: no cover - optional during partial installs
    tracecov = None

if tracecov is not None:
    tracecov.schemathesis.install()

from schemathesis import HookContext, hook


@hook
def map_body(context: HookContext, body):  # noqa: ANN001
    """Avoid impossible POST /model-selection bodies during agent fuzzing (Vecinita agent path only).

    Modal microservices (embedding, scraper, model) use different paths; this hook leaves their bodies unchanged.
    """
    operation = context.operation
    if operation.path == "/model-selection" and operation.method.upper() == "POST":
        return {"provider": "ollama", "model": None, "lock": False}
    return body
