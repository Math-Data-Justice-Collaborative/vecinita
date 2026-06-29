# ADR-028: Supabase JWT verification — ES256/JWKS (supersedes ADR-027 §1/§4)

**Status:** Accepted
**Stage:** 07-build (S004, EV-005)
**Date:** 2026-06-28
**Feature:** F34 — Supabase Auth for admin surfaces
**Issue:** [#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75)
**Supersedes (in part):** [ADR-027](ADR-027-supabase-auth-verification-and-env-sync.md) §1 (HS256
shared secret) and §4 (`cryptography` exclusion)

## Context

ADR-027 §1 chose **HS256 shared-secret** verification via `SUPABASE_JWT_SECRET`. During 07-build
pre-flight, the live canonical project `cfuvghdsuwactfeamtym` was inspected:

- JWKS endpoint publishes an **ES256** (P-256) public key.
- The operator provided **new-scheme** keys (`sb_publishable_*` / `sb_secret_*`) and no
  `SUPABASE_JWT_SECRET`.

HS256 verification would reject all real tokens from this project. The user approved switching to
**asymmetric ES256/JWKS** verification (07-build interview, 2026-06-28).

## Decision

1. **JWT verification — ES256 via JWKS** — Backends fetch the project's JWKS from
   `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` (cached) and verify signature (`ES256`), `exp`,
   and `aud` (`SUPABASE_JWT_AUD`, default `authenticated`). No `SUPABASE_JWT_SECRET` is required.
2. **Dependencies** — Add **`cryptography`** alongside **PyJWT `>=2.10,<3`** in
   `vecinita_shared_schemas` for ES256 verify (back-added to `dependency-inventory.md`).
3. **Role source unchanged** — Still read `app_metadata.role` from the verified JWT (ADR-027 §2).
4. **Testability** — `verify_supabase_jwt()` accepts an injectable JWKS resolver so unit tests sign
   tokens with a local ES256 keypair without calling Supabase.

## Consequences

- `config-spec.md` drops `SUPABASE_JWT_SECRET`; `SUPABASE_URL` is sufficient for JWKS discovery.
- Operational rotation is key-rotation friendly (JWKS auto-refreshed); no coordinated secret push.
- ADR-027 §1 trade-off note (HS256 rotation) is moot for EV-005; asymmetric is now the chosen path.

## References

- Supersedes: ADR-027 §1/§4
- Config: `docs/config-spec.md` §Admin auth — Supabase
- Deps: `docs/dependency-inventory.md` §EV-005
