# BUG-2026-05-27 — modal_embedding health check HTTP 404

**Status:** verifying  
**Severity:** high (admin health degraded; embedding status unknown)  
**Feature:** EV-002 / F26 — health aggregator  
**Reported:** 2026-05-27

## Error description

Admin frontend `/health` (production) shows `modal_embedding` **down** with error
`HTTP 404` and overall status **degraded**. Other services report up.

URL: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/health

Related: deferred follow-up from
[BUG-2026-05-27-health-page-blank-degraded.md](BUG-2026-05-27-health-page-blank-degraded.md)
(UI shape fix merged; embedding 404 out of scope there).

## Error logs

```json
{
  "status": "degraded",
  "services": {
    "modal_embedding": {"status": "down", "latency_ms": null, "error": "HTTP 404"}
  }
}
```

(Same pattern as prior health/all capture; full payload in parent BUG report.)

## Investigation

| Time | Finding |
|------|---------|
| 2026-05-27 | User: every reload on production admin `/health`; started after 2026-05-27 deploy; nothing tried yet. |
| 2026-05-27 | `GET https://vecinita--vecinita-embedding-embedding-api.modal.run/health` → **200** from agent curl. |
| 2026-05-27 | `GET …/health/health` → **404** — matches aggregator behavior if `VECINITA_MODAL_EMBED_URL` includes `/health`. |
| 2026-05-27 | `health_all` builds probe URL as `f"{url.rstrip('/')}/health"` (`app.py`). |
| 2026-05-27 | Modal `vecinita-embedding` app state: **deployed**. |

**Root cause (proposed):** Config / implementation — `VECINITA_MODAL_EMBED_URL` likely set to
health URL (…`/health`) on DO internal-write-api; probe doubles path to `/health/health` → 404.
Code should normalize base URL; ops should set secret to Modal ASGI **base** (no `/health`).

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/api-contract.md` §health/all | Aggregator should reflect true dependency liveness |
| `docs/config-spec.md` `VECINITA_MODAL_EMBED_URL` | Base URL for Modal FastEmbed (not documented with `/health` suffix) |
| `infra/modal/README.md` | Documents base URL + `/health` endpoint separately |
| F26 scope | In scope — health aggregator behavior |

## Repro test

- Path: `tests/bugs/test_bug_2026_05_27_modal_embedding_health_404.py`
- Encodes: embed URL env ending in `/health` must probe single `/health`, not `/health/health`

## Remediation path

**local-first** — PR + CI; DO secret sync / redeploy on user approval.

## Verification plan

| Item | Choice |
|------|--------|
| Success | Admin `/health` shows `modal_embedding` up and overall **healthy** |
| Checks | Full main CI parity (local) + PR branch CI after push |
| Follow-up | 15-service-health after deploy |

## Fix

- `apps/internal-write-api/vecinita_internal_write_api/app.py`: `_dependency_health_url()` —
  if base already ends with `/health`, do not append a second `/health`.
- `docs/staging-secrets-matrix.md`: clarify base URL (no `/health` suffix).

**Ops (after deploy):** Ensure DO `VECINITA_MODAL_EMBED_URL` is the Modal ASGI base, e.g.
`https://vecinita--vecinita-embedding-embedding-api.modal.run` (not `…/health`).

## Verification

| Layer | Result | Evidence |
|-------|--------|----------|
| L1 Automated | pass | repro test + `test_health_aggregator.py`; ruff on changed files |
| L2 Reproduction | pending | user reload admin `/health` after internal-write-api deploy |
| L4 Production | pending | deploy + user confirmation |

## Follow-ups

| Item | Owner | When |
|------|-------|------|
| Sync `VECINITA_MODAL_EMBED_URL` on DO (base URL, no `/health`) | Ops / user | After merge |
| Optional: align chat-rag `_check_dependency` normalization | Agent | If same secret shape |
