# 04-tech-plan report — S004 / EV-005 / F34 Supabase admin auth (#75)

> **Stage**: 04-tech-plan (evolve-lite) | **Session**: S004-supabase-auth | **Date**: 2026-06-28
> **Branch**: `feat/S004-supabase-auth` | **Issue**: [#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75)

## Summary

Resolved every technical decision 01-requirements deferred for F34, authored **ADR-027**, pinned
dependencies, and appended **Phase 11 (M43–M47, T43.1–T47.6)** to the execution plan. Implementation
is captured as tasks only (no product source written in this planning stage).

## Decisions (interview, 2026-06-28)

| ID | Decision |
|----|----------|
| TP-S004-01 | JWT verify = **HS256 shared secret** (`SUPABASE_JWT_SECRET`); verify sig + `exp` + `aud` |
| TP-S004-02 | Role from **`app_metadata.role`** read directly from the verified JWT (no hook/DB call) |
| TP-S004-03 | Shared verifier **`vecinita_shared_schemas.auth`** (no new package) reused by DM + write API |
| TP-S004-04 | Pins: **PyJWT `>=2.10,<3`** (no `cryptography`); **`@supabase/supabase-js ^2.108.2`** |
| TP-S004-05 | DM Modal `/jobs*`: keep `X-Vecinita-Proxy-Key` + add JWT dependency (both pass) |
| TP-S004-06 | **Cost cap raised to ~$75/mo** (Pro $25 + existing ~$42–48), supersedes ADR-004 — user-approved |
| TP-S004-07 | Env sync = **Supabase Pro + ephemeral branching** + **CLI migrations-in-repo**, MCP-independent (R53 unblocked) |
| TP-S004-08 | Invites = **`inviteUserByEmail` + custom SMTP**; public signup disabled |
| TP-S004-09 | Internal-write API = JWT (operator, role-gated) **or** `VECINITA_INTERNAL_API_KEY` (service) |
| TP-S004-10 | First-admin = **idempotent seed script** via `SUPABASE_SECRET_KEY` → `app_metadata.role=admin` |
| TP-S004-11 | Audit `actor_id` (UUID) + `actor_role` columns (no PII) via Alembic migration |
| TP-S004-12 | Single branch `feat/S004-supabase-auth`; one PR to `main` (PR-47) |

## Cost note (blocking [Decision] raised + resolved)

Supabase Pro (~$25/mo, branching prerequisite) breaches the prior ADR-004 **$50/mo hard cap**
(all-in ~$67–75/mo). Raised as a blocking decision per `constraint-enforcement`; **user approved
raising the cap to ~$75/mo**. ADR-027 supersedes the ADR-004 cost line; preview branches kept
ephemeral (billed outside the spend cap at `$0.01344`/branch/hour).

## Artifacts produced / updated

- **New**: `docs/adr/ADR-027-supabase-auth-verification-and-env-sync.md`
- **Updated**: `docs/decisions.md` (EV-005 04-tech-plan decisions; unresolved list closed),
  `docs/dependency-inventory.md` (pins + Supabase CLI), `docs/config-spec.md`
  (`SUPABASE_JWT_SECRET`; mechanism/role resolved; SMTP), `docs/api-contract.md` (HS256 + app_metadata),
  `docs/sessions/S000-internal-docs-archive/execution-plan.md` (Phase 11, Current State, Cost Estimate, Task Tracking, PR-47, Open Questions)

## Execution plan delta

- **Phase 11** — M43 (Supabase config + env-sync + seed + runbook), M44 (shared verifier),
  M45 (backend enforcement + audit attribution + ChatRAG CORS), M46 (DM frontend auth),
  M47 (integration/privacy/OpenAPI/gate). 29 tasks, TDD-ordered, all `pending`.

## Open / hand-off to 07-build

- Custom SMTP provider must be configured on the Supabase project before live invite delivery
  (T43.1 stubs config; live verification at 13-deploy-smoke).
- Supabase **Pro** must be enabled on `cfuvghdsuwactfeamtym` before branching is used.
- R53 (MCP access) is **not blocking** — env-sync uses the Supabase CLI; MCP access optional.

## Next stage

evolve-lite skips 05-verify-tech/06-tech-tooling → **07-build** (Phase 11, M43→M47).
