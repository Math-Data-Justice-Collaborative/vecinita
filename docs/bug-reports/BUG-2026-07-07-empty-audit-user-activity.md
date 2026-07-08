# BUG-2026-07-07 — Empty user activity / audit logs missing actor attribution

**Status:** verifying  
**Severity:** high (admin audit & user activity unusable)  
**Feature:** EV-002 F29 / EV-005 / EV-006 F35  
**Reported:** 2026-07-07

## Error description

Admin `/audit` shows **No audit events found** when filtering by user activity or
`document.created` for known document IDs. Users → **View activity** returns empty
because the link filtered `entity_id=<user uuid>` instead of actions **by** that user.

Ingest/retag jobs wrote `document.created` rows with **null `actor_id`** because the
Modal pipeline calls internal-write-api with the service key only.

## Root cause

| Issue | Detail |
|-------|--------|
| Wrong activity filter | Users page linked `/audit?entity_id=<user>`; document/job events use `entity_id` = resource id |
| Missing API filter | `GET /internal/v1/audit` had no `actor_id` query param |
| Missing API fields | Response omitted `actor_id` / `actor_role` |
| Service attribution | `_resolve_write_actor` returned `(None, None)` for service-key batch upsert |
| Job audit gap | `POST /jobs` did not emit `job.created`; pipeline did not forward initiator |

## Fix

- `GET /internal/v1/audit`: `actor_id` filter; return `actor_id` + `actor_role` on items
- Service writes: honor `X-Vecinita-Audit-Actor-Id` / `Role` headers on write routes
- Jobs: store `initiated_by_*` on job records; emit `job.created|completed|failed` audits
- Pipeline: `InternalWriteClient.with_audit_actor()` forwards initiator on upsert/tag writes
- Frontend: Users → View activity uses `actor_id=`; `fetchAuditLog` supports `actor_id`
- Migration `20260707_0008`: index `ix_audit_log_actor_id_created_at` on DO Postgres

**Note:** `audit_log` (EV-002) is the activity store — no separate table required.

## Repro test

- `tests/bugs/test_bug_2026_07_07_user_activity_audit_actor.py` (red → green)

## Verification

| Layer | Result | Evidence |
|-------|--------|----------|
| L1 Automated | pass | pytest bug + unit tests; FE vitest audit user events |
| DO migration | pass | `alembic upgrade head` → `20260707_0008` on staging Postgres |
| L4 Production | pending | Deploy internal-write-api, data-management Modal, admin FE |

## Remediation path

**local-first** — deploy after user approval.
