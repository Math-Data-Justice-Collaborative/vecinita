"""TC-077/078/079 unit tests for vecinita_shared_schemas.auth."""

from __future__ import annotations

import time
from typing import Annotated
from uuid import uuid4

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from vecinita_shared_schemas.auth import (
    AuthConfig,
    AuthContext,
    AuthPrincipal,
    _principal_from_authorization,
    _resolve_operator_or_service,
    get_auth_config,
    get_principal,
    require_admin_write,
    require_authenticated,
    require_role,
    reset_auth_config_for_tests,
    resolve_operator_or_service,
    verify_supabase_jwt,
)

from tests.unit.shared_schemas.auth_fixtures import (
    InvalidSigningKeyResolver,
    generate_es256_keypair,
    make_auth_config,
    sign_test_jwt,
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


def test_verify_rejects_when_supabase_url_missing() -> None:
    private_key = generate_es256_keypair()
    token = sign_test_jwt(private_key)
    cfg = make_auth_config(private_key)
    cfg.supabase_url = ""

    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(token, config=cfg)
    assert exc_info.value.status_code == 503  # type: ignore[attr-defined]


def test_verify_rejects_invalid_sub_and_role_metadata() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key)
    bad_sub = sign_test_jwt(private_key)
    payload = jwt.decode(
        bad_sub,
        private_key.public_key(),
        algorithms=["ES256"],
        options={"verify_signature": False},
    )
    payload["sub"] = 123
    bad_sub_token = jwt.encode(payload, private_key, algorithm="ES256")

    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(bad_sub_token, config=cfg)
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]

    no_role = sign_test_jwt(private_key, role="guest")
    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(no_role, config=cfg)
    assert exc_info.value.status_code == 403  # type: ignore[attr-defined]


def test_dev_bypass_when_auth_not_required() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key, auth_required=False)

    ctx = _resolve_operator_or_service(authorization=None, config=cfg)
    assert ctx.principal is not None
    assert ctx.principal.role == "admin"

    principal = _principal_from_authorization(None, config=cfg)
    assert principal.role == "admin"


def test_resolve_operator_or_service_requires_bearer_when_auth_required() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key, auth_required=True)

    with pytest.raises(Exception) as exc_info:
        _resolve_operator_or_service(authorization=None, config=cfg)
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]


def test_require_authenticated_allows_viewer_and_service() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key)
    viewer = verify_supabase_jwt(sign_test_jwt(private_key, role="viewer"), config=cfg)
    ctx_viewer = require_authenticated(
        AuthContext(principal=viewer, is_service=False),
    )
    assert ctx_viewer.principal is not None

    ctx_service = require_authenticated(AuthContext(principal=None, is_service=True))
    assert ctx_service.is_service is True

    with pytest.raises(Exception) as exc_info:
        require_authenticated(AuthContext(principal=None, is_service=False))
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]


def test_auth_config_from_env_and_cache() -> None:
    reset_auth_config_for_tests()
    import os

    os.environ["SUPABASE_URL"] = "https://env.supabase.co/"
    os.environ["SUPABASE_JWT_AUD"] = "authenticated"
    os.environ["VECINITA_AUTH_REQUIRED"] = "false"
    os.environ["VECINITA_INTERNAL_API_KEY"] = "env-key"

    cfg = AuthConfig.from_env()
    assert cfg.supabase_url == "https://env.supabase.co"
    assert cfg.jwt_aud == "authenticated"
    assert cfg.auth_required is False
    assert cfg.internal_api_key == "env-key"
    assert cfg.jwks_url.endswith("/auth/v1/.well-known/jwks.json")

    assert get_auth_config() is get_auth_config()
    reset_auth_config_for_tests()


def test_verify_rejects_non_dict_app_metadata_and_invalid_signing_key() -> None:
    private_key = generate_es256_keypair()
    token = sign_test_jwt(private_key)
    cfg = make_auth_config(private_key)
    payload = jwt.decode(
        token,
        private_key.public_key(),
        algorithms=["ES256"],
        options={"verify_signature": False},
    )
    payload["app_metadata"] = "not-a-dict"
    bad_meta = jwt.encode(payload, private_key, algorithm="ES256")
    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(bad_meta, config=cfg)
    assert exc_info.value.status_code == 403  # type: ignore[attr-defined]

    cfg.signing_key_resolver = InvalidSigningKeyResolver()  # type: ignore[assignment]
    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(token, config=cfg)
    assert exc_info.value.status_code == 503  # type: ignore[attr-defined]


def test_verify_rejects_non_uuid_sub() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key)
    token = sign_test_jwt(private_key)
    payload = jwt.decode(
        token,
        private_key.public_key(),
        algorithms=["ES256"],
        options={"verify_signature": False},
    )
    payload["sub"] = "not-a-uuid"
    bad_sub = jwt.encode(payload, private_key, algorithm="ES256")
    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(bad_sub, config=cfg)
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]


def test_get_principal_and_resolve_operator_or_service_dependencies() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key)
    admin_token = sign_test_jwt(private_key, role="admin")

    app = FastAPI()

    @app.get("/principal")
    def principal_route(principal: Annotated[AuthPrincipal, Depends(get_principal)]) -> dict[str, str]:
        return {"role": principal.role}

    @app.get("/context")
    def context_route(ctx: Annotated[AuthContext, Depends(resolve_operator_or_service)]) -> dict[str, bool]:
        return {"service": ctx.is_service}

    reset_auth_config_for_tests()
    import os

    os.environ["SUPABASE_URL"] = cfg.supabase_url
    os.environ["VECINITA_INTERNAL_API_KEY"] = cfg.internal_api_key or ""
    os.environ["VECINITA_AUTH_REQUIRED"] = "true"
    cfg_for_override = make_auth_config(private_key)
    app.dependency_overrides[get_principal] = lambda: verify_supabase_jwt(
        admin_token,
        config=cfg_for_override,
    )
    app.dependency_overrides[resolve_operator_or_service] = lambda: _resolve_operator_or_service(
        f"Bearer {admin_token}",
        config=cfg_for_override,
    )
    client = TestClient(app)
    assert client.get("/principal").status_code == 200
    assert client.get("/context").json() == {"service": False}


def test_resolve_operator_or_service_rejects_non_bearer_authorization() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key, auth_required=True)

    with pytest.raises(Exception) as exc_info:
        _resolve_operator_or_service(authorization="Token abc", config=cfg)
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]

    with pytest.raises(Exception) as exc_info:
        _principal_from_authorization("Bearer ", config=cfg)
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]

    operator_token = sign_test_jwt(private_key, role="viewer")
    ctx = _resolve_operator_or_service(
        authorization=f"Bearer {operator_token}",
        config=cfg,
    )
    assert ctx.is_service is False
    assert ctx.principal is not None


def test_get_principal_reads_authorization_header() -> None:
    import vecinita_shared_schemas.auth as auth_mod

    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key)
    token = sign_test_jwt(private_key, role="admin")
    auth_mod._default_config = cfg

    app = FastAPI()

    @app.get("/principal")
    def principal_route(principal: Annotated[AuthPrincipal, Depends(get_principal)]) -> dict[str, str]:
        return {"role": principal.role}

    client = TestClient(app)
    response = client.get("/principal", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_verify_rejects_payload_without_sub() -> None:
    private_key = generate_es256_keypair()
    cfg = make_auth_config(private_key)
    payload = {
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "app_metadata": {"role": "admin"},
    }
    token = jwt.encode(payload, private_key, algorithm="ES256")
    with pytest.raises(Exception) as exc_info:
        verify_supabase_jwt(token, config=cfg)
    assert exc_info.value.status_code == 401  # type: ignore[attr-defined]
