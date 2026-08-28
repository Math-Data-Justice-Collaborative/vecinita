r"""BUG-2026-08-27: Modal ASGI handlers must not block on sync .remote().

Live evidence (HF-272-275): vecinita-embedding returned HTTP 429
"pending input queue limit (2000)"; ChatRAG DO returned no_healthy_upstream.
Blocking service.*.remote() inside async Starlette routes holds ASGI workers
while EmbeddingService/RerankService crash or cold-start, saturating the queue.
"""

from __future__ import annotations

import re
from pathlib import Path

_REMOTE_CALL = re.compile(r"\.remote\(")
_ALLOWED_ASYNC = re.compile(r"\.remote\.aio\(|\.spawn\(|\.remote_gen\(")


def _strip_python_comments(source: str) -> str:
    """Drop full-line and trailing ``#`` comments so docs cannot false-positive."""
    lines: list[str] = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if "#" in line:
            code, _comment = line.split("#", 1)
            lines.append(code.rstrip())
        else:
            lines.append(line)
    return "\n".join(lines)


def _async_route_bodies(source: str) -> list[str]:
    """Return rough bodies of ``async def`` handlers in a Modal ASGI module."""
    cleaned = _strip_python_comments(source)
    parts = re.split(r"\n(?=    async def )", cleaned)
    return [part for part in parts if part.lstrip().startswith("async def ")]


def _assert_no_blocking_remote(path: str) -> None:
    source = Path(path).read_text(encoding="utf-8")
    for body in _async_route_bodies(source):
        for match in _REMOTE_CALL.finditer(body):
            window = body[match.start() : match.start() + 48]
            assert _ALLOWED_ASYNC.search(window), (
                f"{path}: async ASGI handler must use .remote.aio() / .spawn() / "
                f".remote_gen(), not blocking .remote(): {window!r}"
            )


def test_embedding_asgi_uses_nonblocking_modal_calls() -> None:
    """#275 / #274 — embed/warm must not block the ASGI event loop."""
    _assert_no_blocking_remote("infra/modal/embedding_app.py")


def test_rerank_asgi_uses_nonblocking_modal_calls() -> None:
    """#275 — score route must not block the ASGI event loop."""
    _assert_no_blocking_remote("infra/modal/rerank_app.py")


def test_llm_asgi_uses_nonblocking_modal_calls() -> None:
    """Prevent the same queue-saturation pattern on vecinita-llm ASGI."""
    _assert_no_blocking_remote("infra/modal/llm_app.py")
