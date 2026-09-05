# BUG-2026-09-02 — Modal daily schedule missing DATA_MGMT_URL (+ service auth)

## Error description

`daily_corpus_automations` on `vecinita-data-management` failed at the F76 freshness
branch with `ModalJobsEnqueueError: VECINITA_MODAL_DATA_MGMT_URL and
VECINITA_MODAL_PROXY_KEY are required`. Live Modal secret had the proxy key but not
`VECINITA_MODAL_DATA_MGMT_URL`. `sync_modal_secret.sh` did not push that key.

After adding the URL, the same schedule failed with
`enqueue_freshness_refresh failed: 401 Unauthorized` because
`ModalJobsEnqueueClient` sent only the proxy key; POST `/jobs` also requires admin JWT
or `Authorization: Bearer {VECINITA_INTERNAL_API_KEY}` when `VECINITA_AUTH_REQUIRED=true`.

## Error logs

```
2026-09-02 16:00:35-04:00 File "/root/data_management_app.py", line 124, in _run_scheduled_freshness_tick
2026-09-02 16:00:35-04:00     jobs = ModalJobsEnqueueClient()
2026-09-02 16:00:35-04:00 vecinita_data_management_backend.modal_jobs_client.ModalJobsEnqueueError:
VECINITA_MODAL_DATA_MGMT_URL and VECINITA_MODAL_PROXY_KEY are required
```

```
ModalJobsEnqueueError: enqueue_freshness_refresh failed: 401 {"detail":"Unauthorized"}
```

## Investigation

| Time | Note |
|------|------|
| 2026-09-02 | Hotfix intake: only schedule failure among Modal apps; health 200 elsewhere |
| 2026-09-02 | Exported live `vecinita-data-management` secret — PROXY_KEY present, DATA_MGMT_URL absent |
| 2026-09-02 | Root cause 1: sync script REQUIRED_KEYS omitted self-URL |
| 2026-09-02 | Operator approved option 1 (merge-add URL; accept live freshness may enqueue) |
| 2026-09-02 | After URL fix: curl repro — proxy-only → 401; proxy+service Bearer → 202 |
| 2026-09-02 | Root cause 2: client did not default Authorization to INTERNAL_API_KEY |

## Repro test

- Offline contract: `tests/smoke/test_modal_dm_secret_contract.py::test_sync_modal_secret_script_requires_data_mgmt_url`
- Unit: `tests/unit/data_management/test_modal_jobs_client.py::test_modal_jobs_client_defaults_service_authorization_from_env`
- Live verify: `modal run infra/modal/data_management_app.py::daily_corpus_automations` (exit 0; no ModalJobsEnqueueError)

## Fix

1. Add `VECINITA_MODAL_DATA_MGMT_URL` to sync REQUIRED_KEYS + `.env.example` + app docstring + secrets matrix
2. `bash scripts/deploy/sync_modal_secret.sh --merge --apply` from `.env`
3. Default `Authorization: Bearer $VECINITA_INTERNAL_API_KEY` in `ModalJobsEnqueueClient`
4. Redeploy `vecinita-data-management`; re-invoke schedule successfully

## Citations

[Corpus: feature-list.md §F75 §F76]
[Spec: docs/staging-secrets-matrix.md §Modal — Data management]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
