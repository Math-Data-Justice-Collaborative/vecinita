# BUG-2026-06-30 — deploy-preflight modal-secrets auth failure (transient)

**Status:** fixed (pending CI re-run on main)  
**Severity:** medium (main deploy-preflight red; deploy-modal succeeded on same commit)  
**Feature:** infra / CI — deploy-preflight `modal-secrets` job  
**Reported:** 2026-06-30

## Error description

After merge of PR #102 (Phase 12 / EV-006) to `main`, the **Deploy preflight**
workflow failed on job `modal-secrets` step **Verify Modal secrets and volumes**.
The script printed `Modal CLI is not authenticated. Run: modal token new` and
exited 1.

The same commit's **Deploy Modal** workflow (triggered after CI passed) ran
`verify_secrets.sh` with the same repo secrets ~2 minutes later and **succeeded**
(`==> Modal workspace: vecinita (token auth)`).

Run: https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/28465357940/job/84363607196

## Error logs

```
modal-secrets	Verify Modal secrets and volumes	2026-06-30T18:00:43.9331939Z ##[group]Run bash scripts/deploy/verify_secrets.sh
modal-secrets	Verify Modal secrets and volumes	2026-06-30T18:00:43.9365840Z   MODAL_TOKEN_ID: ***
modal-secrets	Verify Modal secrets and volumes	2026-06-30T18:00:43.9366135Z   MODAL_TOKEN_SECRET: ***
modal-secrets	Verify Modal secrets and volumes	2026-06-30T18:01:47.6656546Z Modal CLI is not authenticated. Run: modal token new
modal-secrets	Verify Modal secrets and volumes	2026-06-30T18:01:47.6673853Z ##[error]Process completed with exit code 1.
```

| Field | Value |
|-------|-------|
| Workflow | `deploy-preflight.yml` |
| Job | `modal-secrets` |
| Commit | `9193060` (PR #102 merge) |
| Step duration | ~64s (18:00:43 → 18:01:47) vs ~5s on last success (2026-06-29) |
| Compare run | deploy-modal run `28465498075` — verify OK at 18:03:13 |

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-30 | Failed step message from `scripts/modal_ensure_workspace.sh` line 13–15 (`modal token info` non-zero). |
| 2026-06-30 | GitHub secrets present (detect step `skip=false`; env shows `MODAL_TOKEN_*`). |
| 2026-06-30 | Prior success on `main` (run `28410599267`, 2026-06-29): same script, ~5s verify. |
| 2026-06-30 | deploy-modal on same SHA succeeded verify 2 min after preflight failure — tokens valid. |
| 2026-06-30 | 64s hang suggests Modal API timeout/retry, not missing secrets. |
| 2026-06-30 | `modal-secrets` job has no `setup-python` (system Py3.12); deploy-modal uses Py3.11 — unlikely root cause (Py3.12 worked 2026-06-29). |

**Root cause (confirmed):** Transient Modal API failure during `modal token info`
(~64s hang in CI). Same `MODAL_TOKEN_*` secrets succeeded in deploy-modal 2 min
later. Script had no retry and swallowed stderr, producing misleading
"not authenticated" on a single failed attempt.

## Repro test

- Path: `tests/bugs/test_bug_2026_06_30_deploy_preflight_modal_auth_flaky.py`
- Encodes: `modal_ensure_workspace.sh` retries `modal token info` when first call fails transiently
- RED: 2026-06-30 (before retry logic)
- GREEN: 2026-06-30 (after `_wait_for_modal_token`)

## Remediation path

**local-first** — retry + actionable error messages in `modal_ensure_workspace.sh`

## Interview record

| Question | Answer |
|----------|--------|
| Intent | New bug — investigate and fix |
| Symptom type | Integration (Modal API / CI) |
| Where seen | GitHub Actions deploy-preflight on main (PR #102 merge) |
| When started | This merge; last preflight success 2026-06-29 |
| Frequency | Once (deploy-modal succeeded shortly after) |
| Environment | GHA only |
| Severity | Medium — preflight red, deploy still OK |
| Evidence | CI logs + compare deploy-modal run |
| Remediation | Fix locally first |

## Fix

- `scripts/modal_ensure_workspace.sh`: `_wait_for_modal_token()` — up to 3 attempts
  (configurable via `MODAL_TOKEN_INFO_RETRIES`, delay via `MODAL_TOKEN_INFO_RETRY_DELAY`);
  surfaces last Modal CLI error and CI-specific hint when `MODAL_TOKEN_*` are set.

## Prevention & countermeasures

| Layer | Action |
|-------|--------|
| Detection | `tests/bugs/test_bug_2026_06_30_deploy_preflight_modal_auth_flaky.py` |
| Process | Re-run deploy-preflight on main if modal-secrets flakes; compare deploy-modal on same SHA |
| Cursor rule | Declined — one-off transient API hardening |

## Cursor rule

Declined (user).
