---
session_id: S009-playground-model-download
type: feature
status: in_progress
branch: feat/S009-playground-model-download
started_at: 2026-07-05
intent: "Super-admin-only Ollama model download UI on eval playground; admins list and select models only; full-stack test coverage"
orchestrator: 16-evolve
evolve_cycle_id: EV-010
context_briefs:
  - docs/sessions/S000-internal-docs-archive/context/playground-model-download.md
standing_docs_touched: []
linked_issues: []
prior_session: S008-eval-ux-playground
---

# Session S009 — playground model download

## Intent

Allow **super-admins** to download additional Ollama models into the Modal `vecinita-models`
volume so the eval playground can run experiments with tags beyond the default. Regular
**admins** continue to list and select available models for playground runs but cannot trigger
pulls.

## Scope

**In scope**

- Super-admin-only `POST /internal/v1/models/ollama/pull` (auth change from current admin)
- Playground UI: enter Ollama model tag, trigger download, poll model list until `available=true`
- Full-stack tests: unit, integration, Vitest, pytest e2e, Playwright
- Spec deltas: F38 in `feature-list.md`, api-contract, test-plan (TC-134 update + new cases)

**Out of scope (v1)**

- Ollama library catalog browser / search
- Auto-pull on eval run when model missing (explicit download only)
- Changing super-admin promote flow (F37)
- Live Modal GPU smoke in CI (optional manual staging verify)

## Routing plan

See [routing-plan.md](./routing-plan.md).

## Links

- Prior: [S008 session brief](../S008-eval-ux-playground/session-brief.md)
- Context: [playground-model-download.md](../../sessions/S000-internal-docs-archive/context/playground-model-download.md)
- Baseline infra: [ADR-035](../../adr/ADR-035-ev009-eval-playground-production-config.md), `infra/modal/ollama_app.py`
- Tech plan: [04-tech-plan report](./reports/04-tech-plan.md), [ADR-036](../../adr/ADR-036-ev010-playground-model-download.md)
- Roadmap: [roadmap.md](./roadmap.md)
