# ADR-027: Supabase auth verification, role model, env-sync & cost-cap change

**Status:** Accepted
**Stage:** 04-tech-plan (S004, EV-005)
**Date:** 2026-06-28
**Feature:** F34 — Supabase Auth for admin surfaces
**Issue:** [#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75)
**Builds on:** [ADR-026](ADR-026-supabase-admin-auth.md) (admin-only Supabase Auth, invite-only, two roles)
**Supersedes (in part):** [ADR-004](ADR-004-cost-sovereignty-zero-personal-data.md) §Cost (the
`≤ $50/mo` hard cap — raised for EV-005, see §Decision 6).

## Context

[ADR-026](ADR-026-supabase-admin-auth.md) (01-requirements) decided **that** Supabase Auth gates
the admin surfaces (DM UI, DM API, internal-write API), invite-only, with `admin` + `viewer`
roles, identity in Supabase, corpus DB PII-free, env-sync via branching. It explicitly deferred the
**technical mechanism** decisions to 04-tech-plan:

- JWT verification mechanism (asymmetric JWKS vs shared HS256 secret) and the role-claim source
  (`app_metadata` vs a `user_roles` table).
- Dependency choice + pins (`@supabase/supabase-js`; a Python JWT-verify library).
- Cost of Supabase Auth + branching against the ADR-004 `≤ $50/mo` cap.
- First-admin bootstrap; invite delivery mechanism.
- R53: the Supabase MCP cannot reach the canonical project `cfuvghdsuwactfeamtym`.

These were resolved via the 04-tech-plan interview (2026-06-28); this ADR records the technical
decisions and the cost-cap change they force.

## Decision

### 1. JWT verification — shared **HS256** secret

The DM API and internal-write API verify the Supabase access token symmetrically with the project's
JWT secret (`SUPABASE_JWT_SECRET`). On each protected request the backend verifies **signature**
(HS256), **expiry** (`exp`), and the **audience** (`aud == SUPABASE_JWT_AUD`, default
`authenticated`). Invalid/missing/expired → `401`.

- Rejected: asymmetric JWKS (ES256/RS256). Simpler operational model now; HS256 is the Supabase
  default and avoids a JWKS fetch/cache path. The secret is delivered as a backend secret (Modal
  secret / DO env) and never tracked. **Trade-off recorded:** rotating the JWT secret requires a
  coordinated backend env update; revisit asymmetric keys if/when key rotation cadence grows.

### 2. Role source — **`app_metadata.role`**, read directly from the verified JWT

The role lives in Supabase **`app_metadata.role`** (`admin` | `viewer`). `app_metadata` is
admin-controlled (not user-editable) and is included in the access token by default, so backends
read the role straight from the verified JWT — **no custom access-token hook and no per-request DB
round-trip**. Writes (`POST`/`PATCH`/`DELETE`) require `admin`; `viewer` → `403`.

- Rejected: custom access-token hook injecting a top-level `user_role` claim (extra config), and a
  separate `user_roles` table (extra round-trip).

### 3. Shared verifier module — `vecinita_shared_schemas.auth`

A single JWT-verification helper lives in the existing shared package
`packages/shared-schemas` as `vecinita_shared_schemas.auth` (mirroring the existing
`vecinita_shared_schemas.cors`). Both the DM backend (Modal) and the internal-write API import it as
a FastAPI dependency. No new package is created.

- The verifier exposes the authenticated principal (opaque Supabase user `sub` UUID + `role`) and a
  `require_role("admin")` dependency. Modal-agnostic, locally testable.

### 4. Dependencies & pins (back-added to `dependency-inventory.md`)

| Package | Where | Pin | Purpose |
|---------|-------|-----|---------|
| **PyJWT** | Python (shared verifier) | `>=2.10,<3` (2.12+ on lock) | HS256 verify (signature/exp/aud); pure-Python, no `cryptography` needed for HS256 |
| **@supabase/supabase-js** | Node (DM frontend only) | `^2.108.2` | SPA session, login, invite-accept, logout |
| **Supabase CLI** | dev/ops + CI | `>=2,<3` (latest 2.x) | Migrations-in-repo, branching, local link |

`cryptography` is **not** added — HS256 needs only PyJWT's HMAC path. It would only be required if a
future ADR switches to asymmetric keys (§1 trade-off).

### 5. Backend enforcement boundaries

- **DM backend (Modal `/jobs*`)** — keeps the existing `X-Vecinita-Proxy-Key` Modal-proxy header
  (transport guard, `modal-proxy-header.mdc`) **and** adds the Supabase JWT dependency
  (application-level operator auth). Both must pass.
- **Internal-write API (`/internal/v1/*`)** — accepts **either** a Supabase JWT (operator; role
  enforced) **or** the existing `VECINITA_INTERNAL_API_KEY` (service-to-service, Modal→write path).
  Operator write routes require role `admin`.
- **ChatRAG** — unchanged (anonymous, stateless); CORS tightened to the ChatRAG frontend origin only
  (RD-079).

### 6. Environment syncing — Supabase **Pro + Git-driven branching**; **cost cap raised to ~$75/mo**

Env-sync uses Supabase **branching** (Pro plan, $25/mo) with **ephemeral preview branches**
(created for a migration/PR, torn down after) to bound branch-hours; auth/schema **migrations live
in the repo** and are applied via the **Supabase CLI** (CI-friendly, MCP-independent — unblocks
R53). Secrets are delivered via Modal secrets + DO env, never committed.

**Cost impact (supersedes ADR-004 cost line):** Supabase Pro ($25/mo, incl. $10 compute credits) on
top of the existing ~$42–48/mo (DO + Modal, TP-009) yields an all-in **~$67–75/mo**. This **exceeds
the prior $50/mo hard cap**. Per the cost-constraint protocol the change was raised as a blocking
`[Decision]` and the user **approved raising the monthly cap to ~$75/mo**.

| Item | Prior (ADR-004) | New (ADR-027) |
|------|-----------------|---------------|
| Monthly target | $25 | $25 (best-effort; not achievable with Pro) |
| Monthly **hard cap** | **$50** | **~$75** |

Branching billing detail: `$0.01344` per preview branch per hour (~$0.32/day; ~$9.60/mo if left
running). Mitigation: keep preview branches ephemeral; keep the org **spend cap ON** for non-branch
usage (branches are billed outside the cap, so they must be torn down promptly).

### 7. Invitation delivery — `inviteUserByEmail` + **custom SMTP**

Operators are onboarded with the Supabase admin `inviteUserByEmail` API, with a **custom SMTP**
provider configured on the project for production-grade delivery. Public sign-up stays **disabled**.

### 8. First-admin bootstrap — idempotent **seed script**

A one-time, idempotent seed script (run at deploy/manually) uses `SUPABASE_SECRET_KEY` (admin API)
to create the first admin from `SUPABASE_ADMIN_EMAIL` / `SUPABASE_ADMIN_PASSWORD` with
`app_metadata.role = admin`. Re-runs are no-ops. Credentials live in `prod.env` only (never tracked).

## Consequences

- New deps (§4) added to `dependency-inventory.md`; pins resolved (no remaining "pin in 04-tech-plan"
  for F34).
- `config-spec.md` gains `SUPABASE_JWT_SECRET`; the verification mechanism + role source are now
  fixed (HS256 + `app_metadata.role`), removing the "finalized in 04-tech-plan" placeholders.
- The corpus DB `audit_log` gains nullable `actor_id` (UUID) + `actor_role` (text) only — **no PII**
  (extends ADR-016). A repo Alembic migration adds them; privacy tests assert no identity/PII
  columns and that `actor_id` is a UUID.
- Cost envelope rises to ~$75/mo (§6). ADR-004's cost line is superseded for EV-005; the
  execution-plan Cost Estimate is updated accordingly.
- R53 is unblocked: schema/auth config is managed via Supabase CLI + repo migrations, independent of
  MCP access to `cfuvghdsuwactfeamtym`. MCP access remains a nice-to-have.
- Operational runbook required (invite/disable/role-change, JWT-secret rotation, branch cleanup) —
  authored as a task in Phase 11 and surfaced in the deploy/secrets matrix.

## Alternatives considered

- **Asymmetric JWKS verification** — better rotation story, no shared secret; rejected for v1 in
  favor of the simpler HS256 default (§1).
- **Free tier + CLI-only env sync (no paid branching)** — keeps ≤ $50/mo; rejected because the
  ticket explicitly asks for best-practice env syncing (branching) and the user approved the cap
  raise (§6).
- **Custom access-token hook / `user_roles` table** — rejected for added config / round-trips (§2).

## References

- Builds on: [ADR-026](ADR-026-supabase-admin-auth.md); Supersedes cost line of
  [ADR-004](ADR-004-cost-sovereignty-zero-personal-data.md)
- Decisions: `docs/decisions.md` §EV-005 04-tech-plan (TP-S004-01–TP-S004-12); RD-073–RD-079
- Config: `docs/config-spec.md` §Admin auth — Supabase, §CORS
- API: `docs/api-contract.md` §Authentication
- Deps: `docs/dependency-inventory.md` §EV-005
- Tests: `docs/test-plan.md` TC-077–TC-086; `docs/acceptance-criteria.md` AC-A1–AC-A10
- Plan: `docs/sessions/S000-internal-docs-archive/execution-plan.md` §Phase 11 (EV-005)
