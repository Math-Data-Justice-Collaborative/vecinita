"""Test helpers for Supabase JWT verification (ES256)."""

from __future__ import annotations

import time
from uuid import UUID, uuid4

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from vecinita_shared_schemas.auth import AuthConfig


class _StaticSigningKey:
    """StaticSigningKey."""

    def __init__(self, key: object) -> None:
        """Init  ."""
        self.key = key


class StaticSigningKeyResolver:
    """Injectable JWKS substitute for unit tests."""

    def __init__(self, public_key: object) -> None:
        """Init  ."""
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token: str) -> _StaticSigningKey:
        """Get signing key from jwt."""
        _ = token
        return _StaticSigningKey(self._public_key)


class InvalidSigningKeyResolver:
    """InvalidSigningKeyResolver."""

    def get_signing_key_from_jwt(self, token: str) -> object:
        """Get signing key from jwt."""
        _ = token
        return object()


def generate_es256_keypair() -> ec.EllipticCurvePrivateKey:
    """Generate es256 keypair."""
    return ec.generate_private_key(ec.SECP256R1())


def sign_test_jwt(  # noqa: PLR0913  # noqa: PLR0913
    private_key: ec.EllipticCurvePrivateKey,
    *,
    sub: UUID | None = None,
    role: str = "admin",
    aud: str = "authenticated",
    exp_offset: int = 3600,
    corrupt_signature: bool = False,
) -> str:
    """Sign test jwt."""
    payload: dict[str, object] = {
        "sub": str(sub or uuid4()),
        "aud": aud,
        "exp": int(time.time()) + exp_offset,
        "app_metadata": {"role": role},
    }
    token = jwt.encode(payload, private_key, algorithm="ES256")
    if corrupt_signature:
        return f"{token}x"
    return token


def make_auth_config(
    private_key: ec.EllipticCurvePrivateKey,
    *,
    auth_required: bool = True,
    internal_api_key: str | None = "test-internal-key",
) -> AuthConfig:
    """Make auth config."""
    public_key = private_key.public_key()
    return AuthConfig(
        supabase_url="https://test.supabase.co",
        jwt_aud="authenticated",
        auth_required=auth_required,
        internal_api_key=internal_api_key,
        signing_key_resolver=StaticSigningKeyResolver(public_key),
    )
