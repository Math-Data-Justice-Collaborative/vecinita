import importlib.util
import sys
import types
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient


def _load_auth_module(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "test-key")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret")
    monkeypatch.setenv("JWT_EXPIRATION_MINUTES", "15")
    monkeypatch.setenv("JWT_REFRESH_EXPIRATION_DAYS", "7")

    class _FakeSupabaseClient:
        def table(self, _name):
            return self

        def select(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def execute(self):
            return SimpleNamespace(data=[], count=0)

    import supabase

    monkeypatch.setattr(supabase, "create_client", lambda *_args, **_kwargs: _FakeSupabaseClient())

    module_path = Path(__file__).resolve().parents[1] / "src" / "main.py"
    module_name = f"auth_main_test_{uuid.uuid4().hex}"

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def auth_module(monkeypatch):
    module = _load_auth_module(monkeypatch)
    module.rate_limit = module.RateLimitState()
    return module


@pytest.fixture
def client(auth_module):
    return TestClient(auth_module.app)


def test_validate_api_key_format_accepts_known_prefixes(auth_module):
    assert auth_module.validate_api_key_format("sk_vp_" + "a" * 20)
    assert auth_module.validate_api_key_format("apk_" + "b" * 20)


def test_validate_api_key_format_rejects_invalid_values(auth_module):
    assert not auth_module.validate_api_key_format("short")
    assert not auth_module.validate_api_key_format("badprefix_" + "a" * 20)


def test_rate_limit_blocks_after_repeated_failures(auth_module):
    rl = auth_module.RateLimitState()
    key = "sk_vp_" + "x" * 20

    for _ in range(5):
        rl.record_failed_attempt(key)

    assert key in rl.blocked_keys


def test_password_complexity_validation_rejects_weak_password(auth_module):
    with pytest.raises(ValueError):
        auth_module.PasswordChangeRequest(old_password="old", new_password="weakpass")


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "auth-service"


def test_validate_key_marks_invalid_and_records_failure(client, auth_module):
    key = "invalid"

    response = client.post("/validate-key", json={"api_key": key})

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert auth_module.rate_limit.failed_attempts[key] == 1


def test_validate_key_blocks_after_five_failures(client):
    key = "bad"

    for _ in range(5):
        client.post("/validate-key", json={"api_key": key})

    blocked = client.post("/validate-key", json={"api_key": key})

    assert blocked.status_code == 200
    assert blocked.json()["message"].startswith("API key is blocked")


def test_token_requires_authorization_header(client):
    response = client.post("/token")

    assert response.status_code == 401


def test_token_generation_with_valid_key(client):
    key = "sk_vp_" + "z" * 20

    response = client.post("/token", headers={"Authorization": key})

    assert response.status_code == 200
    token_payload = response.json()
    assert token_payload["token_type"] == "bearer"
    assert token_payload["expires_in"] == 900
    assert token_payload["access_token"]
    assert token_payload["refresh_token"]


def test_track_usage_increments_and_usage_endpoint_reflects_values(client):
    key = "sk_vp_" + "k" * 20

    track = client.post("/track-usage?tokens=3", headers={"Authorization": key})
    usage = client.get("/usage", headers={"Authorization": key})

    assert track.status_code == 200
    assert track.json()["tokens_today"] == 3

    assert usage.status_code == 200
    usage_payload = usage.json()
    assert usage_payload["tokens_today"] == 3
    assert usage_payload["requests_today"] >= 1


def test_track_usage_enforces_daily_limit(client, auth_module):
    key = "sk_vp_" + "m" * 20
    auth_module.rate_limit.usage[key] = {
        "tokens_today": 1000,
        "requests_today": 10,
        "last_reset": auth_module.datetime.now(auth_module.timezone.utc),
    }

    response = client.post("/track-usage?tokens=1", headers={"Authorization": key})

    assert response.status_code == 429
    assert "Daily token limit exceeded" in response.text


def test_config_endpoint_has_security_and_feature_flags(client):
    response = client.get("/config")

    assert response.status_code == 200
    config = response.json()
    assert config["security"]["password_min_length"] == 12
    assert config["features"]["jwt_tokens"] is True
    assert config["features"]["brute_force_protection"] is True


def test_rate_limit_increment_resets_after_day_boundary(auth_module):
    rl = auth_module.RateLimitState()
    key = "sk_vp_" + "r" * 20
    now = auth_module.datetime.now(auth_module.timezone.utc)

    rl.usage[key] = {
        "tokens_today": 100,
        "requests_today": 8,
        "last_reset": now - auth_module.timedelta(days=2),
    }

    updated = rl.increment(key, tokens=4)

    assert updated["tokens_today"] == 4
    assert updated["requests_today"] == 1


def test_rate_limit_increment_raises_for_blocked_key(auth_module):
    rl = auth_module.RateLimitState()
    key = "sk_vp_" + "b" * 20
    rl.blocked_keys.add(key)

    with pytest.raises(ValueError):
        rl.increment(key, tokens=1)


def test_reset_failed_attempts_removes_counter(auth_module):
    rl = auth_module.RateLimitState()
    key = "sk_vp_" + "f" * 20
    rl.record_failed_attempt(key)

    rl.reset_failed_attempts(key)

    assert key not in rl.failed_attempts


def test_password_complexity_validation_rejects_missing_character_classes(auth_module):
    with pytest.raises(ValueError):
        auth_module.PasswordChangeRequest(old_password="old", new_password="Lowercaseonly123")


def test_hash_password_matches_sha256(auth_module):
    hashed = auth_module.hash_password("abc123")

    assert len(hashed) == 64
    assert hashed == auth_module.hashlib.sha256("abc123".encode()).hexdigest()


def test_validate_api_key_handles_internal_exception(auth_module, monkeypatch):
    monkeypatch.setattr(
        auth_module,
        "validate_api_key_format",
        lambda _api_key: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    assert auth_module.validate_api_key("sk_vp_" + "x" * 20) is False


@pytest.mark.asyncio
async def test_get_api_key_from_header_rejects_missing_header(auth_module):
    with pytest.raises(HTTPException) as exc:
        await auth_module.get_api_key_from_header(None)

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_api_key_from_header_rejects_invalid_header_format(auth_module):
    with pytest.raises(HTTPException) as exc:
        await auth_module.get_api_key_from_header(" ")

    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_api_key_from_header_rejects_blocked_key(auth_module):
    key = "sk_vp_" + "q" * 20
    auth_module.rate_limit.blocked_keys.add(key)

    with pytest.raises(HTTPException) as exc:
        await auth_module.get_api_key_from_header(f"Bearer {key}")

    assert exc.value.status_code == 429


def test_validate_key_success_branch_returns_metadata(client):
    key = "sk_vp_" + "e" * 20

    response = client.post("/validate-key", json={"api_key": key})

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is True
    assert payload["metadata"]["usage"]["requests_today"] >= 1


def test_validate_key_handles_internal_exception_branch(client, auth_module, monkeypatch):
    key = "sk_vp_" + "v" * 20
    monkeypatch.setattr(
        auth_module.rate_limit,
        "increment",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("fail")),
    )

    response = client.post("/validate-key", json={"api_key": key})

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert "Internal server error" in response.json()["message"]


def test_token_endpoint_rejects_invalid_api_key(client, auth_module, monkeypatch):
    key = "sk_vp_" + "n" * 20
    monkeypatch.setattr(auth_module, "validate_api_key", lambda _api_key: False)

    response = client.post("/token", headers={"Authorization": key})

    assert response.status_code == 401


def test_token_endpoint_handles_unexpected_error(client, auth_module, monkeypatch):
    key = "sk_vp_" + "w" * 20
    monkeypatch.setattr(
        auth_module.rate_limit,
        "reset_failed_attempts",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    response = client.post("/token", headers={"Authorization": key})

    assert response.status_code == 500


def test_usage_endpoint_defaults_when_no_stats_exist(client):
    key = "sk_vp_" + "u" * 20

    response = client.get("/usage", headers={"Authorization": key})

    assert response.status_code == 200
    body = response.json()
    assert body["tokens_today"] == 0
    assert body["requests_today"] == 0


def test_track_usage_handles_unexpected_error(client, auth_module, monkeypatch):
    key = "sk_vp_" + "t" * 20
    monkeypatch.setattr(
        auth_module.rate_limit,
        "increment",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("broken")),
    )

    response = client.post("/track-usage?tokens=1", headers={"Authorization": key})

    assert response.status_code == 500


def test_change_password_success(client):
    key = "sk_vp_" + "c" * 20
    response = client.post(
        "/change-password",
        headers={"Authorization": key},
        json={
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_change_password_handles_unexpected_error(client, auth_module, monkeypatch):
    key = "sk_vp_" + "p" * 20

    async def _fail_change_password(*_args, **_kwargs):
        raise RuntimeError("forced")

    # Patch underlying endpoint function by replacing logger with object that triggers exception on info call.
    monkeypatch.setattr(
        auth_module,
        "logger",
        SimpleNamespace(
            info=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("forced")),
            error=lambda *_args, **_kwargs: None,
        ),
    )

    response = client.post(
        "/change-password",
        headers={"Authorization": key},
        json={
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!",
        },
    )

    assert response.status_code == 500


def test_http_exception_handler_formats_payload(auth_module):
    request = object()
    exc = HTTPException(status_code=418, detail="teapot")

    response = auth_module.http_exception_handler(request, exc)
    if hasattr(response, "__await__"):
        import asyncio

        response = asyncio.get_event_loop().run_until_complete(response)

    assert response.status_code == 418


def test_lifespan_context_runs_startup_and_shutdown(auth_module):
    events = {"startup": False, "shutdown": False}

    class _FakeQuery:
        def select(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

        def execute(self):
            events["startup"] = True
            return SimpleNamespace(data=[], count=0)

    class _FakeSupabase:
        def table(self, _name):
            return _FakeQuery()

    auth_module.supabase = _FakeSupabase()

    async def _exercise():
        async with auth_module.lifespan(auth_module.app):
            pass
        events["shutdown"] = True

    import asyncio

    asyncio.get_event_loop().run_until_complete(_exercise())

    assert events["startup"] is True
    assert events["shutdown"] is True


def test_lifespan_context_handles_startup_exception(auth_module):
    class _FailingSupabase:
        def table(self, _name):
            raise RuntimeError("table missing")

    auth_module.supabase = _FailingSupabase()

    async def _exercise():
        async with auth_module.lifespan(auth_module.app):
            pass

    import asyncio

    asyncio.get_event_loop().run_until_complete(_exercise())


def test_import_package_init_module_executes_version_constant():
    init_path = Path(__file__).resolve().parents[1] / "src" / "__init__.py"
    spec = importlib.util.spec_from_file_location("auth_src_init_test", init_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)

    assert module.__version__ == "0.1.0"


def test_module_raises_if_required_env_is_missing(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_KEY", "")

    fake_supabase = types.ModuleType("supabase")
    fake_supabase.create_client = lambda *_args, **_kwargs: SimpleNamespace()
    fake_supabase.Client = object
    monkeypatch.setitem(sys.modules, "supabase", fake_supabase)

    module_path = Path(__file__).resolve().parents[1] / "src" / "main.py"
    module_name = f"auth_main_missing_env_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None

    with pytest.raises(ValueError):
        spec.loader.exec_module(module)
