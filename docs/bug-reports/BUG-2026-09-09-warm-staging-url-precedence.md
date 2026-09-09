# BUG-2026-09-09-warm-staging-url-precedence

[Corpus: staging] [Corpus: feature-list.md §F83]  
**Found by:** EV-staging-adversarial-plunge (2026-09-09)  
**Status:** fixed  
**Session:** HF-2026-09-09-staging-plunge-findings

## Error description

`scripts/ops/warm_staging_for_smoke.py` CLI defaults resolved
`VECINITA_MODAL_EMBED_URL` / `VECINITA_MODAL_LLM_URL` **before**
`VECINITA_STAGING_MODAL_*`. On a developer `.env` that defines both, `warm_staging_for_smoke`
logged and warmed **`vecinita--` (main)** hosts, not `vecinita-staging--`.

## Error logs

```text
$ uv run python scripts/ops/warm_staging_for_smoke.py
warming embed: https://vecinita--vecinita-embedding-embedding-api.modal.run/warm
warming llm: https://vecinita--vecinita-llm-fastapi-app.modal.run/warm
warm-before-smoke: ok
```

## Investigation

**Root cause:** precedence order + dual-populated local env.

## Repro test

`tests/unit/scripts/test_warm_staging_for_smoke.py` —
`test_default_modal_url_prefers_staging_env`, `test_main_dry_run_uses_staging_defaults`.

## Fix

Prefer `VECINITA_STAGING_MODAL_*` when set; explicit `--embed-url` / `--llm-url` still win.
CI can keep passing explicit staging URLs.

## Interview record

Discovered during EV-staging-adversarial-plunge; fixed in HF-2026-09-09 as option 1
(prefer staging-named vars).
