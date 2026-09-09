#!/usr/bin/env bash
# Staging adversarial API probes (read-mostly). Requires .env staging URLs + keys.
# Usage: bash scripts/adversarial/staging_api_probe.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
export PATH="/usr/bin:/bin:/opt/homebrew/bin:${PATH:-}"

if [[ "${VECINITA_ALLOW_STAGING_ADVERSARIAL:-}" != "1" ]]; then
  echo "Set VECINITA_ALLOW_STAGING_ADVERSARIAL=1 to run (staging only)." >&2
  exit 2
fi

uv run python <<'PY'
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

env: dict[str, str] = {}
for line in Path(".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, _, val = line.partition("=")
    env[key.strip()] = val.strip().strip('"').strip("'")

chat = env["VECINITA_STAGING_CHAT_URL"].rstrip("/")
write = env["VECINITA_STAGING_WRITE_URL"].rstrip("/")
dm = env["VECINITA_STAGING_MODAL_DATA_MGMT_URL"].rstrip("/")
key = env["VECINITA_INTERNAL_API_KEY"]
proxy = env.get("VECINITA_MODAL_PROXY_KEY", "")
supa = (
    env.get("SUPABASE_STAGING_URL")
    or env.get("VITE_SUPABASE_STAGING_URL")
    or env["SUPABASE_URL"]
).rstrip("/")
anon = (
    env.get("SUPABASE_STAGING_PUBLISHABLE_KEY")
    or env.get("VITE_SUPABASE_STAGING_PUBLISHABLE_KEY")
    or env["SUPABASE_PUBLISHABLE_KEY"]
)


def http(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: float = 60,
) -> tuple[int, str]:
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


rows: list[dict[str, object]] = []


def check(name: str, code: int, expect: set[int]) -> None:
    ok = code in expect
    rows.append({"name": name, "code": code, "ok": ok, "expect": sorted(expect)})
    print(f"{code:4} {name} ok={ok}")


# OpenAPI body gate
_, oa_raw = http("GET", f"{chat}/openapi.json")
oa = json.loads(oa_raw)
for path in ("/api/v1/ask", "/api/v1/feedback"):
    has = "requestBody" in oa["paths"][path]["post"]
    rows.append({"name": f"openapi{path}", "has_requestBody": has})
    print(f"openapi {path} requestBody={has}")

check("write_noauth", http("GET", f"{write}/internal/v1/stats/summary")[0], {401})
check(
    "write_service",
    http(
        "GET",
        f"{write}/internal/v1/stats/summary",
        {"Authorization": f"Bearer {key}"},
    )[0],
    {200},
)
check(
    "write_x_api_key",
    http(
        "GET",
        f"{write}/internal/v1/stats/summary",
        {"X-API-Key": key},
    )[0],
    {401},
)

# JWT + DM dual auth
login_code, login_body = http(
    "POST",
    f"{supa}/auth/v1/token?grant_type=password",
    {"apikey": anon, "Content-Type": "application/json"},
    json.dumps(
        {"email": env["SUPABASE_ADMIN_EMAIL"], "password": env["SUPABASE_ADMIN_PASSWORD"]}
    ).encode(),
)
assert login_code == 200, login_body[:200]
token = json.loads(login_body)["access_token"]
check(
    "dm_jwt_only",
    http("GET", f"{dm}/jobs", {"Authorization": f"Bearer {token}"})[0],
    {401},
)
if proxy:
    check(
        "dm_jwt_proxy",
        http(
            "GET",
            f"{dm}/jobs",
            {
                "Authorization": f"Bearer {token}",
                "X-Vecinita-Proxy-Key": proxy,
            },
        )[0],
        {200},
    )

check(
    "ask_identity",
    http(
        "POST",
        f"{chat}/api/v1/ask",
        {"Content-Type": "application/json"},
        json.dumps({"question": "x", "email": "a@b.com"}).encode(),
    )[0],
    {400},
)

failed = [r for r in rows if r.get("ok") is False]
print(json.dumps({"failed": len(failed), "rows": rows}, indent=2))
raise SystemExit(1 if failed else 0)
PY
