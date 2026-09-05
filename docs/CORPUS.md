# Doc corpus registry

Canonical index of **standing** product docs. Cite rows as `[Corpus: <id>]` (see
`.cursor/rules/doc-corpus-citation.mdc`). Session/ephemeral artifacts live under
`docs/sessions/{id}/` and are **not** corpus rows unless promoted here.

**Pack session store:** new orchestrator cycles use `~/.cursor/workflow/{owner}/vecinita/sessions/{id}/` (`state.yaml`, `HANDOFF.md`). Legacy `workflow-state.yaml` at repo root remains for in-flight brownfield sessions only. See [.cursor/MIGRATED-TO-PLUGIN.md](../.cursor/MIGRATED-TO-PLUGIN.md).

**Parity:** Before shipping a behavior change, the cited corpus row(s) must already
define or be updated to define that behavior — or carry an explicit waiver cite.

## Standing docs

| ID | Path | Purpose |
|----|------|---------|
| product | [feature-list.md](feature-list.md) | Features (Fn) + acceptance bullets |
| journeys | [user-journeys.md](user-journeys.md) | Caller journeys (UJ-NNN) |
| system-spec | [spec.md](spec.md) | Architecture, components, constraints |
| architecture | [architecture.md](architecture.md) | System topology / data-flow companion |
| config | [config-spec.md](config-spec.md) | Config parameters, defaults, validation |
| api | [api-contract.md](api-contract.md) | HTTP/API surface |
| tests | [test-plan.md](test-plan.md) | Test matrix + TC-NNN |
| acceptance | [acceptance-criteria.md](acceptance-criteria.md) | Pass/fail thresholds |
| deps | [dependency-inventory.md](dependency-inventory.md) | Dependencies and licenses |
| data | [data-management-plan.md](data-management-plan.md) | Schema, seed corpus, eval fixtures |
| data-flow | [data-flow.md](data-flow.md) | Runtime data paths |
| deploy | [deploy-checklist.md](deploy-checklist.md) | Deploy checklist |
| deploy-integration | [deployment-integration.md](deployment-integration.md) | Modal / DO / hybrid wiring |
| staging | [staging-runbook.md](staging-runbook.md) | Staging ops + corpus protection; Stage→Main merge gate (F83 / EV-033) |
| typing | [typing-policy.md](typing-policy.md) | Python/TS typing (ADR-018) |
| adr | [adr/README.md](adr/README.md) + `adr/ADR-*.md` | Architecture decisions |
| decisions | [decisions/](decisions/) + [decisions.md](decisions.md) | Interview / evolve decision logs |
| evolve-decisions | [decisions/evolve-decisions.md](decisions/evolve-decisions.md) | Evolve cycle scopes + waivers |

### Tech satellites (cite path or nearest hub id)

Vecinita has not merged a single `tech-spec.md` / `env-contract.md` / `deploy.md`.
When personal skills say `[Corpus: tech-spec]`, open **config** + **deps** +
**deploy-integration** (+ **staging** as needed).

| Topic | Path |
|-------|------|
| Env / secrets matrix | [staging-secrets-matrix.md](staging-secrets-matrix.md) |
| Local dev | [LOCAL_DEV.md](LOCAL_DEV.md) |
| Eval golden set | [eval-golden-set.md](eval-golden-set.md) |
| OpenAPI (write API) | [../openapi/internal-write.yaml](../openapi/internal-write.yaml) |
| OpenAPI (data management) | [../openapi/data-management.yaml](../openapi/data-management.yaml) |
| OpenAPI (ChatRAG) | [../openapi/chat-rag.yaml](../openapi/chat-rag.yaml) |
| Changelog | [../CHANGELOG.md](../CHANGELOG.md) |
| Frontend i18n (EN/ES UI catalog) | [../packages/frontend-i18n/](../packages/frontend-i18n/) — cite `[Corpus: frontend-i18n]` or `[Corpus: feature-list.md §F31]` |
| Staff copy-change (ChatRAG + Admin UX) | [runbooks/staff-copy-change.md](runbooks/staff-copy-change.md) — cite `[Corpus: staff-copy]` |

Runbooks stay **opt-in** (cite by path or id): [runbooks/corpus-operator-guide.md](runbooks/corpus-operator-guide.md), [runbooks/staff-copy-change.md](runbooks/staff-copy-change.md) (`[Corpus: staff-copy]`).
`docs/research-brief.md` is **not** a Vecinita standing doc — `[Corpus: WAIVED — research-brief.md; reason: antibody leftover cite; decided: S031]`.
The EV-037 waiver for a standing staff-maintainability runbook is **lifted** (EV-297 / #297) — use `[Corpus: staff-copy]` instead of that waiver.

## Citation examples

```
[Corpus: product]          → feature-list.md (prefer + §Fn when known)
[Corpus: feature-list.md §F70]
[Corpus: feature-list.md §F75]   → corpus change automations (catch-up)
[Corpus: feature-list.md §F76]   → freshness (stale threshold / Refresh now)
[Corpus: feature-list.md §F77]   → LoRA fine-tune + human promote
[Corpus: feature-list.md §F84]   → admin Monitoring + staging Grafana/Loki (#114)
[Corpus: feature-list.md §F85]   → FAQ fast-path canned answers (#79 / #320; Layer D)
[Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]
[Spec: docs/adr/ADR-055-operational-monitoring-grafana-loki.md]
[Corpus: api]
[Spec: docs/api-contract.md §POST /chat]
[Corpus: WAIVED — multilingual dim; reason: spike only; decided: 2026-08 / S027]
[Corpus: WAIVED — community maps/alerts mock; reason: non-normative HTML mock, no Fn; decided: S031]
[Corpus: WAIVED — research-brief.md; reason: antibody leftover; decided: S031]
```

## Skill obligations (open only touched rows)

Pack skills load from **engineering-memory** plugin (`evolve`, `spec-*`, `build-*`). Project-only skills: see [.cursor/skills/README.md](../.cursor/skills/README.md).

| Stage band | Minimum corpus rows |
|------------|---------------------|
| Orchestrator intake / `spec-context` | product, journeys (if UI), system-spec |
| Spec band (`spec-requirements`, `spec-draft-docs`, …) | product, journeys, system-spec, api (if contract), tests |
| Tech band (`spec-tech-plan`, …) | system-spec, config, api, deps, deploy-integration, data (if schema) |
| Build band (`build-build`, `build-verify-*`, …) | cited Spec Source rows + tests |
| QA / verify (`build-qa`, `build-verify-impl`, …) | tests, acceptance, journeys (if UI), product |
| Deploy (`build-verify-deploy`, `build-deploy-smoke`) | deploy, deploy-integration, staging |
| Agent merge / PR-to-main | staging, deploy-integration, acceptance (AC-ST5/AC-ST8) |
| `hotfix` | product + system-spec + rows for the failing surface |
| `build-health` | deploy-integration, staging |

Domain / runbooks (e.g. [runbooks/corpus-operator-guide.md](runbooks/corpus-operator-guide.md))
are **opt-in** — cite by path when touched; add a CORPUS row only if they become normative.

## Missing coverage

If a needed row or authoritative section is absent: **AskQuestion** per
`.cursor/rules/doc-corpus-citation.mdc` — add docs (recommended), waive with
`[Corpus: WAIVED — …]`, defer, or re-scope. Do not invent normative text silently.
| consumer-gates | [policies/CONSUMER-GATES.md](policies/CONSUMER-GATES.md) | EV-049 plugin-consumer security/quality/exact pins |
