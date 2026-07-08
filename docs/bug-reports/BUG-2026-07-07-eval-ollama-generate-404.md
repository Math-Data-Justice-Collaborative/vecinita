# BUG-2026-07-07 — Eval run 502: Ollama generate 404 (model not found)

**Status:** fixing (local patch ready; deploy pending)  
**Severity:** critical  
**Feature:** F36 / F38 eval playground (ADR-035, EV-009/EV-010)  
**Reported:** 2026-07-07  
**Environment:** Production admin frontend + internal-write-api + Modal vecinita-ollama

## Error description

Golden eval run fails with HTTP 502 from internal-write-api; upstream Ollama returns 404 Not Found
when generating with the default model `qwen2.5:1.5b-instruct`.

## Error logs

```text
GET /internal/v1/eval/runs/be320989-b5e1-4f78-9649-d75b073a292b

{
  "run_id": "be320989-b5e1-4f78-9649-d75b073a292b",
  "status": "failed",
  "mode": "golden",
  "config_snapshot": {
    "model_id": "qwen2.5:1.5b-instruct",
    ...
  },
  "error_message": "generate failed with status 502: {\"detail\":\"ollama generate failed: HTTP Error 404: Not Found\"}"
}
```

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Error / crash — eval run failed |
| Where | Production (admin frontend → internal-write-api) |
| When | After last deploy |
| Frequency | Every time |
| Repro env | Production only |
| Severity | Critical — evals blocked |
| Evidence | User pasted run JSON + fetch (JWT redacted) |
| Tried | Nothing |

## Remediation path

**local-first** — fix locally, deploy after user approval.

## Verification plan

| Field | Value |
|-------|-------|
| Success criterion | Original error gone — golden eval run completes |
| Verification checks | Full main CI parity (local) + GitHub CI on PR/main after merge |
| Monitoring | User watches production after deploy |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | Ollama routing fixed (post BUG-2026-07-05) but default model never staged on `vecinita-models` volume | **Confirmed** — generate hits Ollama 404 |
| H2 | Manifest reports `available:true` when no manifest / no pull (`_read_manifest` default) | **Confirmed** — `infra/modal/ollama_app.py` defaulted to `available: True` |
| H3 | `vecinita-ollama` deployed without `stage_default_model` run | **Likely** — per `deployment-integration.md` EV-010 post-deploy step |
| H4 | Wrong model tag vs volume contents | **Rejected** — tag matches `DEFAULT_MODEL_ID` / `EvalConfig` default |

**Related bugs:** BUG-2026-07-05 (422 vLLM routing, resolved), BUG-2026-07-06 (pull 503 / missing Modal app).

## Root cause

**Code bug + data/ops gap:** On a fresh or unstaged `vecinita-models` volume, `_read_manifest()` falsely marked the default model as available. `_ollama_generate_text()` forwarded Ollama's HTTP 404 without pulling the model, producing `502` at internal-write-api and failed eval runs.

## Spec conformance

| Check | Result |
|-------|--------|
| `deployment-integration.md` EV-010 — models on `vecinita-models` volume | Implementation drift fixed — manifest now honest; generate lazy-pulls |
| `config-spec.md` — default `model_id` | Pass — unchanged |
| `api-contract.md` — eval error shape | Pass — 502 with detail preserved |

## Repro test

- `tests/bugs/test_bug_2026_07_07_eval_ollama_generate_404.py` — RED → GREEN (2026-07-07)

## TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-07-07 | Added repro tests (generate 404 + manifest default) | RED |
| 2 | 2026-07-07 | Lazy pull on 404 + manifest `available:false` default | GREEN |

## Fix

- `infra/modal/ollama_app.py` — `_read_manifest` / `_list_models_payload` default `available: false`; `_mark_model_available` helper; `_ollama_generate_text` pulls on HTTP 404 and retries once
- `tests/unit/modal/test_ollama_volume_manifest.py` — updated default expectation
- `tests/bugs/test_bug_2026_07_07_eval_ollama_generate_404.py` — regression tests

## Verification

### Layer 1 — Automated (partial)

- [x] Repro test red → green
- [x] Scoped lint + typecheck + modal unit tests
- [ ] Full CI parity (local) — pending before PR
- [ ] PR branch CI — pending push

### Layer 2–4

- [ ] Layer 2 — User re-runs golden eval in admin
- [ ] Layer 3 — Pre-deploy: redeploy `vecinita-ollama` Modal app
- [ ] Layer 4 — Production verified after deploy

## Prevention & countermeasures

*(Pending Phase 5)*
