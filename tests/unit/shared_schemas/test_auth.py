"""TC-077/078/079 unit tests for vecinita_shared_schemas.auth."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from tests.unit.shared_schemas.auth_fixtures import (
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
)
from vecinita_shared_schemas.auth import (
    AuthContext,
    AuthPrincipal,
    _resolve_operator_or_service,
    get_principal,
    require_admin_write,
    require_role,
    reset_auth_config_for_tests,
    verify_supabase_jwt,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_auth_config() -> None:
    reset_auth_config_for_tests()


def test_verify_valid_jwt_returns_principal_sub_and_role() -> None:
    private_key = generate_es256_keypair()
    user_id = uuid4()
    token = sign_test_jwt(private_key, sub=user_id, role="admin")
    cfg = make_auth_config(private_key)

    principal = verify_supabase_jwt(token, config=cfg)

    assert principal.sub == user_id
    assert principal.role == "admin"


@pytest.mark.parametrize("token", ["not-a-jwt", ""])
def test_verify_rejects_missing_or_malformed_token(token: str) -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key)

    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(token, config=cfg)
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]


def test_verify_rejects_expired_token() -> None:
    private_key = generate_es256_keypair()
    token = sign_test_jwt(private_key, exp_offset=-60)
    cfg = make_auth_config(private_key)

    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(token, config=cfg)
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]


def test_verify_rejects_wrong_audience() -> None:
    private_key = generate_es256_keypair()
    token = sign_test_jwt(private_key, aud="wrong-aud")
    cfg = make_auth_config(private_key)

    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(token, config=cfg)
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]


def test_require_role_admin_denies_viewer() -> None:
    app = FastAPI()
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key)
    viewer_token = sign_test_jwt(private_key, role="viewer")

    @app.get("/write", dependencies=[Depends(require_role("admin"))])
    def write_route() -> dict[str, str]:
        return {"ok": "true"}

    def override_principal() -> AuthPrincipal:
        return verify_supabase_jwt(viewer_token, config=cfg)

    app.dependency_overrides[get_principal] = override_principal
    client = TestClient(app)
    response = client.get("/write")
    assert response.status_code == 403


def test_require_role_admin_allows_admin() -> None:
    app = FastAPI()
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key)
    admin_token = sign_test_jwt(private_key, role="admin")

    @app.get("/write", dependencies=[Depends(require_role("admin"))])
    def write_route() -> dict[str, str]:
        return {"ok": "true"}

    def override_principal() -> AuthPrincipal:
        return verify_supabase_jwt(admin_token, config=cfg)

    app.dependency_overrides[get_principal] = override_principal
    client = TestClient(app)
    response = client.get("/write")
    assert response.status_code == 200


def test_resolve_operator_or_service_accepts_internal_api_key() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key, internal_api_key="svc-key-123")

    ctx = _resolve_operator_or_service(
        authorization="Bearer svc-key-123",
        config=cfg,
    )
    assert ctx.is_service is True
    assert ctx.principal is None


def test_require_admin_write_blocks_viewer_allows_admin_and_service() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key, internal_api_key="svc-key-123")

    viewer = verify_supabase_jwt(sign_test_jwt(private_key, role="viewer"), config=cfg)
    with pytest.raises(Exception) as exc_info:
        require_admin_write(AuthContext(principal=viewer, is_service=False))
    assert exc_info.value.status_code == 403  # type: ignore[attr-defined]

    admin = verify_supabase_jwt(sign_test_jwt(private_key, role="admin"), config=cfg)
    ctx_admin = require_admin_write(AuthContext(principal=admin, is_service=False))
    assert ctx_admin.principal is not None
    assert ctx_admin.principal.role == "admin"

    ctx_service = require_admin_write(AuthContext(principal=None, is_service=True))
    assert ctx_service.is_service is True
