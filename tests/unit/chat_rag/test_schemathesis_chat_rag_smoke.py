"""TC-334: Schemathesis smoke on ChatRAG OpenAPI (in-process ASGI).

[Corpus: api] [Corpus: tests] [Spec: docs/test-plan.md §TC-334]
"""

from __future__ import annotations

from http import HTTPStatus

import pytest
import schemathesis
from hypothesis import HealthCheck, Phase, given, settings
from schemathesis.core.result import Ok
from vecinita_chat_rag_backend.app import create_app
from vecinita_chat_rag_backend.config import ChatRagSettings

pytestmark = pytest.mark.unit

_INCLUDE = frozenset(
    {
        ("get", "/health"),
        ("get", "/api/v1/tags"),
        ("post", "/api/v1/warm"),
    }
)


def test_schemathesis_chat_rag_safe_ops_no_server_error() -> None:
    """Safe read/warm ops must not return 5xx under Schemathesis generation."""
    app_settings = ChatRagSettings(
        database_url="postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
        top_k=5,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=5.0,
    )
    schema = schemathesis.openapi.from_asgi(
        "/openapi.json",
        create_app(settings=app_settings),
    )
    matched = 0
    for result in schema.get_all_operations():  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]
        if not isinstance(result, Ok):
            continue
        op = result.ok()  # pyright: ignore[reportUnknownVariableType]
        method = str(op.method).lower()
        path = str(op.path)
        if (method, path) not in _INCLUDE:
            continue
        matched += 1
        strategy = op.as_strategy()  # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType]

        @given(case=strategy)  # type: ignore[misc]
        @settings(
            max_examples=8,
            deadline=None,
            phases=[Phase.generate],
            suppress_health_check=[
                HealthCheck.too_slow,
                HealthCheck.filter_too_much,
                HealthCheck.data_too_large,
            ],
        )
        def _run(case: object) -> None:
            response = case.call()  # type: ignore[attr-defined]
            status_code = int(response.status_code)  # type: ignore[attr-defined]
            assert status_code < int(HTTPStatus.INTERNAL_SERVER_ERROR), (
                f"{case.method} {case.path} -> {status_code}: "  # type: ignore[attr-defined]
                f"{(response.text or '')[:300]}"  # type: ignore[attr-defined]
            )

        _run()

    assert matched == len(_INCLUDE)
