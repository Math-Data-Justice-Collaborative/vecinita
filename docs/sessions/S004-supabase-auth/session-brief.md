---
session_id: S004-supabase-auth
type: feature
status: in_progress
branch: feat/S004-supabase-auth
started_at: 2026-06-28
intent: "GitHub #75 — add Supabase Auth authentication for ADMIN surfaces only (Data Management UI + DM API + internal write API); ChatRAG stays anonymous; invitation-only registration; admin + viewer roles; identity in Supabase; env sync via Supabase branching."
orchestrator: 16-evolve
evolve_cycle_id: EV-005
linked_issues: [75]
context_briefs: [docs/context-brief.md#15-ev-005-supabase-admin-auth-75]
standing_docs_touched: [docs/context-brief.md]
---

# S004 — Supabase Auth (admin surfaces) — #75

## Intent

Add an **authentication interface** ([issue #75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75))
so that only permitted operators can manage the corpus, view dashboards, and call admin APIs.
Use **Supabase Auth** as the identity provider. Authentication applies to **admin surfaces only**;
the public ChatRAG experience stays anonymous and stateless.

## Scope (in)

1. **Data Management UI** (`apps/data-management-frontend`) — login screen, session handling,
   protected routes, surface current user (enables per-user dashboards + audit attribution).
2. **Data Management API** (`apps/data-management-backend`) — Supabase JWT verification
   middleware; reject unauthenticated requests.
3. **Internal Write API** (`apps/internal-write-api`) — Supabase JWT verification middleware;
   reject unauthenticated requests.
4. **Invitation-only registration** — public signup disabled; admins invite by email
   (Supabase invite / magic-link).
5. **Roles** — two roles: `admin` (full) and `viewer` (read-only).
6. **Environment syncing** — follow Supabase best practices: **branching** (preview/staging
   synced via git) on the canonical project; migrations in repo.
7. **Secrets/config** — Supabase keys via Modal secrets + DO env (no secrets in tracked specs;
   see `no-operator-spec-commits.mdc`).
8. **Specs + CORS** — update OpenAPI (`openapi/`, `internal-write-api-spec.yaml`) and CORS
   (`Authorization` header / cookies) as needed.

## Scope (out)

- **ChatRAG chat/query API + public corpus browse** stay anonymous and stateless (no login on
  visitor-facing surfaces). Preserves F3 (stateless chat).
- No PII for visitors in the Vecinita corpus DB. Identity/PII lives in Supabase only
  (corpus DB stays PII-free; F15 privacy guardrails extended, not relaxed).
- No richer RBAC beyond admin + viewer (this cycle).
- No OAuth social providers (this cycle) — email invite / password / magic-link only,
  pending 01-requirements.

## Key decisions (AskQuestion 2026-06-28)

| # | Decision | Choice | Rationale |
|---|----------|--------|-----------|
| 1 | Prior session S003 | **Close** (defer remaining QA/e2e/deploy) | F33 already merged to main (#96/#97); start auth clean |
| 2 | ADR-004 reversal scope | **Admin-only** Supabase Auth; ChatRAG stays anonymous | Preserve privacy stance for visitors; protect operators |
| 3 | Identity / PII residency | Identity in **Supabase**; corpus DB stays PII-free | Keep DO Postgres free of operator PII (revisit ADR-005) |
| 4 | Registration + roles | **Invite-only** (public signup off); `admin` + `viewer` | Matches ticket "invitation-only"; minimal RBAC |
| 5 | Environment syncing | **Supabase branching** on canonical project | Best-practice dev/staging/prod sync; user to grant MCP access |
| 6 | Routing | **Lite** evolve path (skip 02/03/05/06/11) | User-approved |

## Architectural reversal (must be recorded in 01/04)

This feature **reverses** prior hard constraints — a new superseding ADR is required:

- **ADR-004** (cost / sovereignty / **zero personal data — no Supabase Auth, no identity**):
  supersede the **auth/identity clause for admin surfaces only**. Visitor-side zero-PII intact.
- **ADR-005** referenced in feature-list out-of-scope ("Supabase Auth, OAuth, invite-by-email"):
  revisit. (Note: `docs/adr/ADR-005` on disk is *Managed Postgres + pgvector*; the auth-exclusion
  is tracked via ADR-004 + feature-list out-of-scope — 01-requirements must reconcile the exact
  ADR numbering and author the superseding ADR.)
- **F3** (stateless chat): unaffected — ChatRAG stays anonymous.
- **F15** (privacy schema guardrails) / **F16** (infra-only protection): extend, do not relax —
  the corpus DB remains PII-free; admin protection upgrades from infra-only creds to Supabase JWT.

## Open items to resolve in 01-requirements

- Confirm "no user rows mirrored into corpus DB" vs "minimal id/role mirror for attribution"
  (assumed: **Supabase-only**, no mirror).
- **Supabase MCP / project mismatch:** MCP is authenticated to org *Cognitive Chemistry Labs*
  (projects `lrbhxyikeiwmuanqwdya`, `uysuznqtbajeejjvszxc`), but `prod.env` keys point to project
  `cfuvghdsuwactfeamtym`. Confirm the canonical project ref and grant MCP access so branching +
  migrations can be managed.
- Auth credential type: password vs magic-link vs both.
- Cost impact of Supabase Auth + branching vs the $25/$50/mo ADR-004 cap (size in 04-tech-plan).
- CORS / token transport: `Authorization: Bearer` header vs cookies; H4 CORS re-run.

## Routing plan

See [routing-plan.md](./routing-plan.md). Lite evolve path; handoff to 01-requirements next.

## Links

- Issue: [#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75)
- Standing: [context-brief.md](../../context-brief.md), [feature-list.md](../../feature-list.md),
  [spec.md](../../spec.md), [api-contract.md](../../api-contract.md),
  [adr/ADR-004](../../adr/ADR-004-cost-sovereignty-zero-personal-data.md)
