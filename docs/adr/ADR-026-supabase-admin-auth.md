# ADR-026: Supabase Auth for admin surfaces (invite-only, two roles)

**Status:** Accepted
**Stage:** 01-requirements (S004, EV-005)
**Date:** 2026-06-28
**Feature:** F34 — Supabase Auth for admin surfaces
**Issue:** [#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75)
**Supersedes (in part):** ADR-004 §Decision "Data management access" + §"Excluded
dependencies/patterns" (the *no Supabase Auth / no identity* clause) — **for admin surfaces only**.

## Context

[ADR-004](ADR-004-cost-sovereignty-zero-personal-data.md) established a **zero personal data**
stance covering **both** visitors **and operators**: no Supabase Auth, no identity tables, no
invite-by-email; admin surfaces protected by **infrastructure credentials only** (F16). At the
time, sibling Supabase Auth / admin-invite patterns were explicitly rejected (R5/R11).

GitHub [#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75) now requires a
real **authentication interface** so that only permitted operators can manage the corpus, view
dashboards, and call admin APIs — and to unblock per-user features (per-user dashboards, audit
attribution). The user has provisioned a Supabase project and added credentials, and asked for
Supabase Auth, **invitation-only** registration, and best-practice **environment syncing**.

This directly contradicts the ADR-004 auth/identity clause. The contradiction (R49) was resolved
in 00-context as an **admin-only reversal**; this ADR records the superseding decision and the
boundaries that keep the rest of ADR-004 intact.

## Decision

Adopt **Supabase Auth** as the identity provider for **admin surfaces only**:

1. **Protected surfaces** — Data Management UI (`apps/data-management-frontend`), Data Management
   API (`apps/data-management-backend`), and the Internal Write API (`apps/internal-write-api`)
   require a valid Supabase-issued JWT.
2. **Anonymous surfaces (unchanged)** — the public ChatRAG chat/query API and public corpus
   browse stay **anonymous and stateless** (F3 preserved). No login on visitor-facing surfaces.
3. **Registration is invitation-only** — public sign-up is **disabled**; an admin invites an
   operator by email; the invitee accepts via an emailed link and **sets a password**. Login is
   **email + password** (RD-074).
4. **Two roles** — `admin` (full read/write) and `viewer` (read-only). Write operations require
   `admin`; `viewer` receives `403` on writes (RD-075).
5. **Session & token transport** — the DM frontend is an SPA: it uses `@supabase/supabase-js`
   for the browser session and sends the Supabase JWT as `Authorization: Bearer <token>` to the
   APIs. The FastAPI services verify the JWT on each request (RD-076).
6. **Identity / PII residency** — operator identity and PII (email, name, password) live **only
   in Supabase**. The Vecinita corpus database stays **PII-free**. For audit attribution, the
   corpus DB may store **only the opaque Supabase user UUID and the role** as the actor on
   `audit_log` — never email, name, or any other PII (RD-077).
7. **Environment syncing** — environments are kept in sync via **Supabase branching** (preview /
   staging branches driven from Git) on the canonical project; auth/schema migrations live in the
   repo. Secrets are delivered via Modal secrets + DO env and are **never** committed
   (no-operator-spec-commits) (RD-078).
8. **CORS** — the admin APIs add `Authorization` to allowed request headers. Separately, the
   anonymous ChatRAG API tightens CORS to allow **only the ChatRAG frontend origin** (RD-079).

## What ADR-004 still governs (unchanged)

| ADR-004 clause | Status under ADR-026 |
|----------------|----------------------|
| Visitor zero-PII; stateless chat (F3) | **Unchanged** — ChatRAG anonymous |
| Corpus DB has no `users`/`accounts`/`sessions`/`messages` identity tables | **Unchanged** — identity stays in Supabase |
| No raw prompts / IPs in persistent logs | **Unchanged** |
| Data sovereignty (US regions) | **Unchanged**; Supabase project region confirmed in 04-tech-plan |
| Cost ≤ $50/mo (target $25) | **Constrained** — Supabase Auth + branching cost sized in 04-tech-plan; may pressure the cap |

The only reversal is: **operators now authenticate to Vecinita via Supabase identity** instead of
infrastructure credentials only (F16 upgraded → Supabase JWT verification). Visitor privacy is
untouched.

## Privacy enforcement (extended, not relaxed)

- The forbidden-schema deny-list still forbids `users`, `accounts`, `sessions`, `messages`,
  `profiles`, `invites`, `auth_*` **in the corpus DB**. Supabase manages its own `auth.*` schema
  in a **separate** database.
- `audit_log` gains an optional `actor_id` (opaque Supabase user UUID) + `actor_role` column —
  both non-PII. No email/name column is permitted.
- Privacy tests (`tests/privacy/`) are extended to assert (a) no identity tables in the corpus DB
  and (b) `actor_id` is a UUID with no accompanying PII columns.

## Consequences

- A new dependency is required (Supabase JS client on the frontend; a JWT-verification path on the
  FastAPI services). Exact libraries/pins are chosen in **04-tech-plan** and back-added to
  `docs/dependency-inventory.md`.
- `feature-list.md` out-of-scope row "User/admin accounts, Supabase Auth, OAuth, invite-by-email"
  is **partially admitted**: email invite + password admitted for admin surfaces; **OAuth/social
  login remains out of scope** this cycle.
- ADR-005 (Managed Postgres + pgvector) is unaffected — the corpus DB stays on DO Postgres; only
  identity moves to Supabase.
- Operational change: operator access control + key rotation now run through Supabase (invite,
  disable, role change) rather than platform secrets alone.
- The Supabase MCP is currently scoped to org *Cognitive Chemistry Labs* and **cannot** reach the
  `prod.env` project `cfuvghdsuwactfeamtym` (R53). The user confirmed `cfuvghdsuwactfeamtym` is
  canonical and will grant MCP access before branching/migrations are managed in 04/07.

## References

- Supersedes (in part): [ADR-004](ADR-004-cost-sovereignty-zero-personal-data.md) §Data management access, §Excluded dependencies
- Feature: `docs/feature-list.md` §F34
- Context: `docs/context-brief.md` §15 (EV-005); resolutions R49–R53
- Decisions: `docs/decisions.md#requirements-decisions-01-requirements` (RD-073–RD-079)
- Journeys: `docs/user-journeys.md` UJ-026–UJ-029
- Acceptance: `docs/acceptance-criteria.md` AC-A1–AC-A10
- Related: ADR-016 (audit log no IP), F3, F15, F16
