# BUG-2026-07-09 — Admin shows Ollama catalog tags as Not downloaded after pull

**Status:** verifying (local fix green; deploy pending)  
**Severity:** critical  
**Feature:** F38 playground model download / F39 unified vecinita-llm (ADR-037)  
**Reported:** 2026-07-09  
**Environment:** Production/staging admin dashboard + Modal vecinita-llm

## Error description

User downloaded model weights for **qwen3.6:latest** (reported as "qwen3.6-latest") via the
admin Models tab, but the dashboard still shows **Not downloaded** every time after refresh.

## Error logs

```text
ValueError: no HuggingFace mapping for model_id 'qwen3.6:latest' (normalized 'qwen3.6:latest')
```

(Reproduced locally via `resolve_hf_repo("qwen3.6:latest")` — pull path cannot complete.)

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Wrong output — status shows Not downloaded |
| Where | Production/staging admin dashboard |
| When | After ADR-037 / vecinita-llm deploy |
| Frequency | Every time |
| Repro env | Production only |
| Severity | Critical — blocks using qwen3.6 for eval |
| Model tag | `qwen3.6:latest` |
| Tried | Refreshed admin page / re-expanded model family |

## Remediation path

**local-first** — fix locally, deploy after user approval.

## Verification plan

| Field | Value |
|-------|-------|
| Success criterion | Admin dashboard shows **Downloaded** for qwen3.6:latest after pull completes |
| Verification checks | Full main CI parity (local) + GitHub CI on PR/main after merge |
| Monitoring | User watches production after deploy |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | Playground tags missing from HF registry → `pull_model_job` fails before `_mark_model_available` | **Confirmed** — static dict only covered qwen2.5/qwen3 |
| H2 | Catalog availability exact-match only — quant suffix tags stay Not downloaded | **Confirmed** — fixed via normalized lookup |
| H3 | UI poll bug — status not refreshed | **Rejected** — user refreshed; root is manifest never updated |
| H4 | Weights on legacy vecinita-ollama volume | **Possible** — ADR-037 reads vecinita-llm `llm-models` manifest only |

**Note:** `qwen3.6` is a distinct Ollama family from `qwen3:8b` (Qwen3 vs Qwen3.6). Registry only maps `qwen3:*` tags today.

## Root cause

**Code bug (registry gap + catalog overlay):** After ADR-037, playground pulls use HuggingFace
`snapshot_download` via `resolve_hf_repo`. Only a small static tag list was mapped; most
ollama.com catalog families failed resolution, so `pull_model_job` never updated the manifest.
Catalog availability also required an exact tag match, so quantized variants stayed Not
downloaded when the base tag was staged.

## Spec conformance

| Check | Result |
|-------|--------|
| ADR-037 — HF Hub staging for playground tags | Implementation drift fixed — inference for common families |
| `deployment-integration.md` — manifest at `/models/manifest.json` | Pass — behavior correct once pull succeeds |
| F38 download UI | Pass — UI reflects manifest; normalized overlay added |

## Repro test

- `tests/bugs/test_bug_2026_07_09_qwen36_not_downloaded.py` — RED (2026-07-09)

## TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-07-09 | Added repro tests for qwen3.6 registry mapping | RED |
| 2 | 2026-07-09 | Generalized HF inference + normalized catalog availability | GREEN |

## Fix

- `packages/shared-schemas/vecinita_shared_schemas/ollama_hf_registry.py` — family inference
  for common ollama.com tags + suffix normalization
- `infra/modal/llm_model_registry.py` — re-export shared registry
- `infra/modal/llm_app.py` — mount shared-schemas on Modal image
- `ollama_catalog.py` + `app.py` — normalized availability for catalog tags
- Tests: `test_ollama_hf_registry.py`, bug repro, catalog overlay

**Limitation:** Ollama-only tags with no HF vLLM repo still error at pull time (ADR-037).

## Verification

### Layer 1 — Automated (partial)

- [x] Repro test red → green
- [x] Registry unit tests pass
- [ ] Full CI parity (local) — pending before PR

## Prevention & countermeasures

(pending Phase 5)
