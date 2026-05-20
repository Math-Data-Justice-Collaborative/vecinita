# Risk Register

> **Project**: Vecinita  
> **Last updated**: 2026-05-19

| # | Risk | Likelihood | Impact | Mitigation | Status |
|---|------|------------|--------|------------|--------|
| R1 | Monthly cost exceeds **$50** (multi-app DO + vLLM GPU) | Medium | High | Line-item in execution-plan; consolidate DO first; Ollama fallback | Mitigated (pilot est. ≤ $50) |
| R2 | Stale RFantibody `.cursor/rules/` mislead build agents | Low | Medium | 03-plan-tooling rewrite (ISS-001) | Resolved |
| R3 | Sibling API drift if ports copied without OpenAPI | Medium | Medium | OpenAPI-first; greenfield contracts | Mitigated |
| R4 | Accidental PII table in migration | Medium | High | Privacy tests + CI deny-list | Mitigated |
| R5 | vLLM cold start breaks p95 < 15s | Medium | Medium | Warm pools; smaller model; measure in smoke | Open |
| R6 | Modal worker cannot reach DO internal API | Low | High | Private networking / stable TLS; integration tests | Open |
| R7 | Third-party LLM introduced by dependency | Low | High | Dependency audit; ADR for exceptions | Open |
| R8 | LlamaIndex version incompatibility with pgvector | Medium | Medium | Pin versions; integration tests | Open |
| R9 | Multi-app DO secrets sprawl | Medium | Low | Document secret matrix in deploy plan | Open |

## Risk details

### R1: Cost overrun

- **Description:** User chose **multi-app DO topology** and **vLLM as primary LLM** — both increase spend vs ADR-004 $25 target.
- **Trigger:** Deploy to production without cost spreadsheet.
- **Mitigation:** 04-tech-plan must prove ≤ $50 or `[Decision]` to change topology/model.
- **Owner:** ⚠️ User + tech plan stage

### R2: Stale Cursor rules

- **Description:** `.cursor/rules/` reference RFantibody Modal job template.
- **Trigger:** 07-build agent follows wrong constraints.
- **Mitigation:** 03-plan-tooling before 07-build.
- **Source:** ISS-001

### R4: PII schema regression

- **Description:** Future migration adds `users` or `messages`.
- **Trigger:** Feature creep / ported sibling code.
- **Mitigation:** `tests/privacy/test_no_pii_tables.py` blocking in CI.
- **Source:** ADR-004
