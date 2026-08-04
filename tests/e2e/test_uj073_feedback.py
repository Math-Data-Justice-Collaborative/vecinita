"""UJ-073 / TC-225-228: anonymous feedback API + admin list + 90d purge (F68)."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING, Self, cast
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from vecinita_chat_rag_backend.app import create_app as create_chat_app
from vecinita_chat_rag_backend.config import ChatRagSettings
from vecinita_data_management_backend.app import create_app as create_dm_app
from vecinita_data_management_backend.store import InMemoryJobStore
from vecinita_shared_schemas.db_mapping import sqlalchemy_scalar_one
from vecinita_shared_schemas.internal_write import FeedbackListResponse
from vecinita_shared_schemas.json_types import as_json_object

from tests.helpers.json_response import (
    json_int,
    json_object_list,
    json_str,
    response_json_object,
)
from tests.unit.shared_schemas.auth_fixtures import sign_test_jwt

if TYPE_CHECKING:
    from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
    from sqlalchemy.engine import Engine

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(os.environ.get("VECINITA_SKIP_E2E") == "1", reason="E2E skipped"),
]

_API_KEY = "test-internal-key"
_RETENTION_DAYS = 90
_MESSAGE = "The search results felt truncated on mobile."


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita",
    )


def _bearer(private_key: EllipticCurvePrivateKey, *, role: str) -> str:
    return f"Bearer {sign_test_jwt(private_key, role=role)}"


def _auth_key() -> dict[str, str]:
    return {"Authorization": f"Bearer {_API_KEY}"}


@pytest.fixture
def chat_feedback_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """ChatRAG client configured to forward feedback to internal-write."""
    monkeypatch.setenv("DATABASE_URL", _database_url())
    monkeypatch.setenv("VECINITA_INTERNAL_API_KEY", _API_KEY)
    monkeypatch.setenv("VECINITA_INTERNAL_WRITE_URL", "http://internal-write.test")
    settings = ChatRagSettings(
        database_url=_database_url(),
        top_k=3,
        embed_url="http://embed.test",
        llm_url="http://llm.test",
        request_timeout_s=30.0,
        internal_write_url="http://internal-write.test",
        internal_api_key=_API_KEY,
    )
    return TestClient(create_chat_app(settings=settings))


def test_uj073_post_feedback_stores_anonymous_row(write_client: TestClient, engine: Engine) -> None:
    """TC-225: POST /internal/v1/feedback persists category + message only."""
    resp = write_client.post(
        "/internal/v1/feedback",
        json={"category": "suggestion", "message": _MESSAGE, "locale": "en"},
        headers=_auth_key(),
    )
    assert resp.status_code == HTTPStatus.CREATED
    body = response_json_object(resp)
    feedback_id = UUID(json_str(body, "id"))
    assert "created_at" in body

    with engine.connect() as conn:
        row = (
            conn.execute(
                text(
                    """
                SELECT category, message, locale
                FROM feedback
                WHERE id = :id
                """
                ),
                {"id": feedback_id},
            )
            .mappings()
            .one()
        )
    assert row["category"] == "suggestion"
    assert row["message"] == _MESSAGE
    assert row["locale"] == "en"

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM feedback WHERE id = :id"), {"id": feedback_id})


def test_uj073_post_feedback_rejects_email_field(write_client: TestClient) -> None:
    """TC-225 / AC-UX10: feedback write rejects visitor email."""
    resp = write_client.post(
        "/internal/v1/feedback",
        json={
            "category": "bug",
            "message": _MESSAGE,
            "email": "visitor@example.com",
        },
        headers=_auth_key(),
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_uj073_chatrag_post_feedback_rejects_email(chat_feedback_client: TestClient) -> None:
    """TC-225: ChatRAG public POST rejects email/identity fields."""
    resp = chat_feedback_client.post(
        "/api/v1/feedback",
        json={
            "category": "wrong_answer",
            "message": _MESSAGE,
            "email": "visitor@example.com",
        },
    )
    assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_uj073_chatrag_post_feedback_returns_created(
    chat_feedback_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-225: ChatRAG POST /api/v1/feedback returns 201 id + created_at."""
    created_at = datetime.now(UTC).isoformat()
    feedback_id = str(uuid.uuid4())

    class _FakeResponse:
        status_code = HTTPStatus.CREATED

        @staticmethod
        def json() -> dict[str, str]:
            return {"id": feedback_id, "created_at": created_at}

    class _FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            _ = (args, kwargs)

        async def __aenter__(self) -> Self:
            return self

        async def __aexit__(self, *args: object) -> None:
            _ = args

        async def post(self, url: str, **kwargs: object) -> _FakeResponse:
            assert url.rstrip("/").endswith("/internal/v1/feedback")
            headers_raw = kwargs.get("headers")
            assert isinstance(headers_raw, dict)
            headers = cast("dict[str, str]", headers_raw)
            assert headers.get("Authorization") == f"Bearer {_API_KEY}"
            payload = as_json_object(cast("object", kwargs.get("json")))
            assert payload.get("category") == "other"
            assert payload.get("message") == _MESSAGE
            assert "email" not in payload
            return _FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)

    resp = chat_feedback_client.post(
        "/api/v1/feedback",
        json={"category": "other", "message": _MESSAGE, "locale": "es"},
    )
    assert resp.status_code == HTTPStatus.CREATED
    body = response_json_object(resp)
    assert json_str(body, "id") == feedback_id
    assert json_str(body, "created_at") == created_at


class _FeedbackWriteAdapter:
    """Adapt write TestClient to InternalWriteClient.list_feedback for DM e2e."""

    def __init__(self, client: TestClient) -> None:
        self._client = client

    def list_feedback(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
    ) -> FeedbackListResponse:
        params: dict[str, int | str] = {"page": page, "page_size": page_size}
        if category is not None:
            params["category"] = category
        response = self._client.get(
            "/internal/v1/feedback",
            params=params,
            headers=_auth_key(),
        )
        assert response.status_code == HTTPStatus.OK
        return FeedbackListResponse.model_validate(response.json())


def test_uj073_admin_lists_feedback(
    supabase_auth_env: EllipticCurvePrivateKey,
    write_client: TestClient,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-227 / AC-UX12: admin and super-admin can list feedback; viewer 403."""
    _ = supabase_auth_env
    monkeypatch.setenv("VECINITA_MODAL_PROXY_KEY", "test-proxy-key")
    dm = TestClient(
        create_dm_app(
            store=InMemoryJobStore(),
            require_proxy_auth=True,
            eval_runs_client=_FeedbackWriteAdapter(write_client),  # type: ignore[arg-type]
        )
    )
    dm.headers.update({"X-Vecinita-Proxy-Key": "test-proxy-key"})

    create = write_client.post(
        "/internal/v1/feedback",
        json={"category": "bug", "message": f"admin-list-{uuid.uuid4().hex[:8]}", "locale": "en"},
        headers=_auth_key(),
    )
    assert create.status_code == HTTPStatus.CREATED
    feedback_id = json_str(response_json_object(create), "id")

    admin = dm.get(
        "/admin/feedback",
        headers={"Authorization": _bearer(supabase_auth_env, role="admin")},
    )
    assert admin.status_code == HTTPStatus.OK
    admin_body = response_json_object(admin)
    assert "items" in admin_body
    ids = {json_str(item, "id") for item in json_object_list(admin_body, "items")}
    assert feedback_id in ids
    for item in json_object_list(admin_body, "items"):
        assert "email" not in item
        assert "name" not in item
        assert "user_id" not in item

    super_admin = dm.get(
        "/admin/feedback",
        headers={"Authorization": _bearer(supabase_auth_env, role="super-admin")},
    )
    assert super_admin.status_code == HTTPStatus.OK

    viewer = dm.get(
        "/admin/feedback",
        headers={"Authorization": _bearer(supabase_auth_env, role="viewer")},
    )
    assert viewer.status_code == HTTPStatus.FORBIDDEN

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM feedback WHERE id = :id"), {"id": UUID(feedback_id)})


def test_uj073_feedback_purge_removes_rows_older_than_90_days(
    write_client: TestClient,
    engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-228 / AC-UX13: cleanup purges feedback older than retention days."""
    monkeypatch.setenv("VECINITA_FEEDBACK_RETENTION_DAYS", str(_RETENTION_DAYS))
    old_id = uuid.uuid4()
    fresh_id = uuid.uuid4()
    old_created = datetime.now(UTC) - timedelta(days=_RETENTION_DAYS + 1)
    fresh_created = datetime.now(UTC) - timedelta(days=1)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO feedback (id, created_at, category, message, locale)
                VALUES (:id, :created_at, 'other', 'old row', 'en')
                """
            ),
            {"id": old_id, "created_at": old_created},
        )
        conn.execute(
            text(
                """
                INSERT INTO feedback (id, created_at, category, message, locale)
                VALUES (:id, :created_at, 'other', 'fresh row', 'en')
                """
            ),
            {"id": fresh_id, "created_at": fresh_created},
        )

    try:
        resp = write_client.post(
            "/internal/v1/feedback/cleanup",
            headers=_auth_key(),
        )
        assert resp.status_code == HTTPStatus.OK
        body = response_json_object(resp)
        assert json_int(body, "retention_days") == _RETENTION_DAYS
        assert json_int(body, "deleted") >= 1

        with engine.connect() as conn:
            old_count = int(
                str(
                    sqlalchemy_scalar_one(
                        conn.execute(
                            text("SELECT COUNT(*) FROM feedback WHERE id = :id"),
                            {"id": old_id},
                        )
                    )
                )
            )
            fresh_count = int(
                str(
                    sqlalchemy_scalar_one(
                        conn.execute(
                            text("SELECT COUNT(*) FROM feedback WHERE id = :id"),
                            {"id": fresh_id},
                        )
                    )
                )
            )
        assert old_count == 0
        assert fresh_count == 1
    finally:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM feedback WHERE id = :id"), {"id": old_id})
            conn.execute(text("DELETE FROM feedback WHERE id = :id"), {"id": fresh_id})
