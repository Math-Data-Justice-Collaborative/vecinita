# BUG-2026-09-03-staging-embed-url-mirror-regress

## Error description

After EV-338 prod→staging corpus mirror and a successful H3 (sources present),
Deploy Staging on promote PR #341 re-synced GitHub Environment `staging`
`VECINITA_MODAL_EMBED_URL` pointing at **`vecinita-staging--`** (BGE). Staging
ChatRAG queries became incompatible with mirrored **e5** vectors → H3 no-context
with empty `sources` while browse still showed 95 documents.

## Error logs

```
staging embed /health: model_id=BAAI/bge-small-en-v1.5
main embed /health:    model_id=intfloat/multilingual-e5-small

POST staging /api/v1/ask pantry →
{"answer":"I don't have enough community corpus context…","sources":[],"cache_hit":"exact"}

EV-338 prior diagnosis: staging embed + staging DB top cosine ~0.02;
main embed + staging DB top cosine ~0.90
```

## Investigation

| Time (EDT) | Note |
|------------|------|
| 2026-09-03 afternoon | EV-338 mirror + point staging DO at `vecinita--` embed → H3 PASS with sources |
| 2026-09-03 17:14 | Deploy Staging #341 sync-all-secrets --env staging overwrites DO from GH Env |
| 2026-09-03 18:20 | Post-hotfix health: staging H3 0 sources again |

**Root cause:** GH Environment `staging` secret still held `vecinita-staging--` embed URL;
Deploy Staging blindly syncs it onto DO apps that serve a mirrored prod corpus.

## Repro test

`tests/unit/scripts/test_modal_url_validate.py` —
`test_mirrored_staging_embed_rejects_staging_environment_host`

## Fix

1. Set GH Env `staging` + DO staging chat/write embed URL to `vecinita--` (e5)
2. Redeploy staging chat-api / write-api
3. Fail-closed Deploy Staging check unless `VECINITA_ALLOW_STAGING_EMBED=1`

**Applied 2026-09-03:** GH secret updated; staging chat-api redeployed ACTIVE; H3 pantry ask
returned 8 sources (scores ~0.90). Guard landed in `modal_url_validate.assert_mirrored_staging_embed_url`
+ `scripts/deploy/check_staging_embed_mirror_align.sh` wired into `deploy-staging.yml`.

## Interview record

Operator: hotfix staging retrieval after health WARN (2026-09-03).

## Prevention & countermeasures

- Deploy Staging gate on embed host for mirrored corpus
- staging-secrets-matrix + runbook already require `vecinita--` after mirror; keep GH Env aligned

## Cursor rule

Deferred — existing staging-runbook §mirror + secrets matrix; workflow guard is enough.
