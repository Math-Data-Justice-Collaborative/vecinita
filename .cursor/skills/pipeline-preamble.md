# Pipeline skills preamble (00–18)

Shared conventions for numbered pipeline stage skills. Every stage `SKILL.md` under
`.cursor/skills/00-context` … `18-add-feature` follows this preamble unless a stage
explicitly documents an exception.

**Orchestrators** (not numbered stages): [pipeline](pipeline/SKILL.md),
[16-evolve](16-evolve/SKILL.md), [18-add-feature](18-add-feature/SKILL.md).

**Deep policy** (do not duplicate in each skill): [considerations.md](considerations.md),
[connectivity-gates.md](connectivity-gates.md),
[workflow-state-reference.md](workflow-state-reference.md).

---

## 1. Purpose and numbering

| Range | Phase | Skills |
|-------|-------|--------|
| **00–03** | A — Product planning | Context (optional), requirements, verify plan, plan tooling |
| **04–06** | B — Technical planning | Tech plan, verify tech, tech tooling |
| **07–08** | C — Build | Build, verify build (milestone gate) |
| **09–13** | D — Verify & deploy | QA + E2E (parallel), verify impl, verify deploy, deploy smoke |
| **14–15** | E — Maintenance (on-demand) | Hotfix, service health |
| **16–18** | F — Change (on-demand) | Evolve, retrospective, add feature |

Stages are **linear in greenfield** ([pipeline](pipeline/SKILL.md)). Stages **14–18** are
**on-demand** and may re-invoke subsets of 00–15 in **delta mode**.

---

## 2. SKILL.md frontmatter

Each numbered skill includes YAML frontmatter:

```yaml
---
name: NN-short-name    # matches folder, lowercase hyphens
description: >
  Third-person summary: WHAT the stage does and WHEN to invoke it.
  Include trigger terms (e.g. "requirements interview", "deploy smoke").
---
```

- **`description`**: Written in **third person**; max ~1024 chars; must state **what** and **when**.
- **`disable-model-invocation`**: Omitted on pipeline stages (agent may auto-select from description).
- Body title: `# NN — Human Title` matching the stage name.

---

## 3. Standard document skeleton

Most stage skills use this section order (omit sections that do not apply):

| Section | Typical content |
|---------|-----------------|
| **Cross-cutting links** | Preamble, considerations, connectivity-gates |
| **Connectivity (stage NN)** | Stage-specific obligations from connectivity-gates |
| **When to use / Prerequisites** | Upstream stages, artifacts, gates |
| **Uncertainty / AskQuestion** | Pointer to considerations §7 |
| **State management** | `workflow-state.yaml` key + on-invocation rules |
| **Workflow** | Step-by-step work for this stage |
| **Output rules** | Artifacts, commits, handoff to next stage |

Orchestrators (16, 18) add: routing plans, phase gates, safe stopping points, child-skill tables.

---

## 4. Cross-cutting files (required reading)

| File | Role |
|------|------|
| [considerations.md](considerations.md) | Fix-in-place, ADRs, security, data, AskQuestion categories, commit-as-you-go |
| [connectivity-gates.md](connectivity-gates.md) | H0c / H0i / H4–H5 browser+API wiring per stage |
| [workflow-state-reference.md](workflow-state-reference.md) | YAML schema, skill→key map, git_history |
| [template-registry.md](template-registry.md) | Org template layout (when `workflow-state.yaml` §template set) |

Every stage skill includes a **Connectivity (stage NN)** section pointing at the matching row in
connectivity-gates — hybrid deploys (static UI + separate API) are never “API-only done.”

---

## 5. State management

**Single canonical file:** repo-root [`workflow-state.yaml`](../workflow-state.yaml).

| Rule | Requirement |
|------|-------------|
| **Read first** | First action on every invocation |
| **Write immediately** | After each substep — never buffer |
| **Resume** | `status`, timestamps, substeps determine position |
| **Stage key** | `stages.{skill-id}` (e.g. `stages.07-build`) |
| **Cycles** | `evolve_cycles[]` (16, 18), `retrospective_cycles[]` (17) |
| **Cross-stage issues** | `issue_log` with category + evidence |
| **Artifacts** | Append paths to top-level `artifacts[]` on completion |

### On invocation (standard pattern)

1. Read `workflow-state.yaml` for this stage’s block (and `template` / `issue_log` if relevant).
2. If **`completed`**: AskQuestion — reuse / update section / restart.
3. If **`in_progress`**: Report substeps; AskQuestion — resume or restart.
4. If **`pending`** or **`skipped`**: Start or remain skipped per stage rules.
5. Set `in_progress` + `started_at` when work begins.

Detail state may also live in stage reports (`docs/execution-plan.md`, `docs/qa-report.md`, etc.);
**stage completion** must still be mirrored in `workflow-state.yaml`.

---

## 6. User authority and AskQuestion

**The user is the source of truth.** Specs and plans trace to interview answers or explicit
approvals — not agent inference.

### AskQuestion protocol ([considerations.md](considerations.md) §7)

| Rule | Detail |
|------|--------|
| **Blocking issues** | Never silently resolve — always AskQuestion |
| **Batching** | 2–4 questions per call when found together |
| **Recommendation** | First option = recommended with rationale |
| **Escape hatch** | Last option = `Let me explain / provide more context` |
| **Categories** | Label prompts: `[Decision]`, `[Ambiguity]`, `[Contradiction]`, `[Uncertainty]`, `[Scope Drift]`, `[Template Drift]` |
| **Evidence** | Cite spec section, code path, or user answer |

Stages that **collect choices for a later stage** (e.g. 09-qa → 11-verify-impl) may defer
AskQuestion to the handoff skill; that exception must be stated in the stage SKILL.md.

---

## 7. Phase gates and prerequisites

Downstream stages **must not start** until upstream gates pass (unless user waives via AskQuestion).

| Gate | Requires |
|------|----------|
| **A→B** | 01–03 complete (00 optional); product specs approved |
| **B→C** | 04–06 complete; execution plan approved |
| **C→D** | 07 tasks done; 08 pass at milestone/phase boundary |
| **Deploy** | 09+10 pass; 11+12 user-approved; 13 with user deploy approval |

Each skill’s **Prerequisites** section lists its direct dependencies. The orchestrator
([pipeline](pipeline/SKILL.md)) runs **transition checks** between stages: artifacts exist,
cross-doc consistency, scope drift, staleness, template drift.

---

## 8. Git, branches, and commits

Per [considerations.md](considerations.md) §11–12 and [workflow-state-reference.md](workflow-state-reference.md) §Git history:

| Rule | Detail |
|------|--------|
| **Commit-as-you-go** | Commit before next stage, blocking AskQuestion, gate check, or session end |
| **Atomic commits** | One logical change; repo valid after each commit |
| **Record commits** | Append `git_history.commits` with `stage: "NN-…"` |
| **Branches** | `feat/`, `fix/`, `docs/`, `chore/`, `infra/`, `evolve/{id}-{slug}` |

**User rule override:** Do not commit unless the user asked — pipeline skills still **prepare**
commits and record intent in workflow-state when commits are deferred.

---

## 9. Decisions, ADRs, and fix-in-place

| Mechanism | When |
|-----------|------|
| **ADR** | Resolved `[Decision]`, non-obvious `[Ambiguity]`, structural tech choices — `docs/adr/ADR-NNN.md` |
| **Decision logs** | `requirements-decisions.md`, `tech-decisions.md`, `evolve-decisions.md` |
| **Fix in place** | Verification failure → patch code, spec, hook, or infra — **do not re-run whole phases** |
| **Bugs** | [bug-investigation](bug-investigation/SKILL.md) + [14-hotfix](14-hotfix/SKILL.md) |

Classify failures per considerations §1: **spec** vs **code** vs **infra** vs **tooling** before choosing remediation.

---

## 10. Specs and artifacts

| Convention | Detail |
|------------|--------|
| **Output directory** | Default `docs/` (`workflow-state.yaml` §project.output_directory) |
| **Templates** | Stage 01 fills from `templates/`; manifest user-approved before generation |
| **Execution plan** | `docs/execution-plan.md` — 07-build source of truth for tasks |
| **No invention** | Do not add requirements, SLOs, or dependencies not in specs or user answers |
| **Scope drift** | Work outside approved feature list → `[Scope Drift]` AskQuestion |

Project rules (`.cursor/rules/`) enforce plan-adherence, domain vocabulary, and constraints —
stages **03** and **06** install or update those guardrails.

---

## 11. Verification and connectivity tiers

| Tier | Meaning | Typical stage |
|------|---------|---------------|
| **H0c** | CORS unit tests | 06, 07, 09, 13 |
| **H0i** | Integration (API + DB, mocked upstreams) | 07, 09, 10 |
| **H1–H3** | Live API smokes | 13, 15 |
| **H4–H5** | Browser connectivity (CORS live + VITE bundle) | 11, 12, 13 |

`curl` API success is **not** proof the UI works in production. Vitest mocks are **not** T3 E2E.

Live H1–H5, DO deploy, Modal deploy, and hotfix production verification **must** load operator
secrets from repo-root **`prod.env`** (see §16) before running shell commands — do not ask the
user to paste tokens when `prod.env` exists.

---

## 12. Stage roles (summary)

| Skill | Primary output | Blocks |
|-------|----------------|--------|
| **00-context** | `docs/context-brief.md` | Optional |
| **01-requirements** | Product spec suite | Yes (start of A) |
| **02-verify-plan** | Audit report, verified specs | Yes |
| **03-plan-tooling** | Cursor rules, hooks, skills, agents | Yes |
| **04-tech-plan** | Execution plan, tech docs, ADRs | Yes (start of B) |
| **05-verify-tech** | Tech audit | Yes |
| **06-tech-tooling** | Hooks, CI, formatters, smoke layout | Yes |
| **07-build** | Code, tests, PRs | Yes (start of C) |
| **08-verify-build** | `docs/verification-report.md` | Milestone gate |
| **09-qa** | `docs/qa-report.md` | Parallel with 10 |
| **10-e2e** | `docs/e2e-report.md` | Parallel with 09 |
| **11-verify-impl** | User feature/journey approval | Yes |
| **12-verify-deploy** | `docs/deploy-checklist.md` | Yes |
| **13-deploy-smoke** | Deploy, smokes, CHANGELOG | Yes (end of D) |
| **14-hotfix** | BUG report + fix + optional redeploy | On-demand |
| **15-service-health** | Health report | On-demand |
| **16-evolve** | Delta specs + selective 00–15 | On-demand |
| **17-retrospective** | Retro report + skill patches | On-demand |
| **18-add-feature** | New Fn + selective 00–15 + checkpoints | On-demand |

---

## 13. Delta mode (16, 18)

When evolving or adding a feature:

- Pass `mode: evolve`, `delta_only: true`, `evolve_cycle_id`, `affected_artifacts` to child stages.
- Update **only** sections tied to the change; no full doc regeneration without user approval.
- One child stage at a time (except **09 + 10** in parallel).
- **18-add-feature** adds mandatory **phase checkpoints** (digest + AskQuestion) between A–D.

---

## 14. Standard cross-cutting line (for SKILL.md)

Paste immediately after the stage title paragraph:

```markdown
**Preamble:** [pipeline-preamble.md](../pipeline-preamble.md) — shared conventions for stages 00–18.
**Cross-cutting:** [considerations.md](../considerations.md), [connectivity-gates.md](../connectivity-gates.md).
```

Then add the stage-specific **Connectivity (stage NN)** section.

---

## 15. Safe stopping and session end

Every **stage boundary** is a safe stop. Natural pause points:

- After **03** or **06** — planning complete for that phase
- After **08** at a milestone — partial build verified
- After **11** — built and verified; deploy optional
- After **13** — deployed
- Mid **evolve/feature cycle** — see 16/18 §Safe stopping points

On session end: workflow-state must reflect last completed substep; uncommitted work is a
process violation unless the user deferred commits.

---

## 16. Operator environment (`prod.env`)

Repo-root **`prod.env`** is the canonical **local operator secrets file** (gitignored per
`.gitignore`). Stages **13–15**, **14-hotfix** deploy phases, and any live `pytest -m live` /
`scripts/deploy/*.sh` run **must** load it before invoking DO, Modal, Postgres, or staging smokes.

### Rules

| Rule | Detail |
|------|--------|
| **Read first** | If `prod.env` exists at repo root, `source` it — do not prompt for tokens already in that file |
| **Never commit** | Do not add `prod.env` to git; do not echo secret values in chat, logs, or bug reports |
| **Missing file** | AskQuestion: user provides path, creates `prod.env`, or pastes vars for one-off use |
| **Staging URLs** | Not stored in `prod.env` by default — derive via `do_apps.py urls` (below) or `docs/deploy-state.md` |

### Load pattern (bash)

Run from repository root:

```bash
set -a
source prod.env
set +a
```

Equivalent one-liner for a single command:

```bash
set -a && source prod.env && set +a && <command>
```

### Variables in `prod.env`

| Key | Used by |
|-----|---------|
| `DIGITALOCEAN_TOKEN` | `scripts/deploy/do_apps.py` (deploy, list, urls, sync-secrets) — DO API |
| `MODAL_TOKEN_ID` | `modal deploy`, `modal app list`, Modal smokes |
| `MODAL_TOKEN_SECRET` | Paired with `MODAL_TOKEN_ID` |
| `DATABASE_URL` | H2 (`staging_h2.py`, Alembic), live DB checks; falls back as `VECINITA_STAGING_DATABASE_URL` when unset |

Add other operator-only keys to `prod.env` locally as needed (e.g. `VECINITA_INTERNAL_API_KEY`
for authenticated curl smokes). Keep names aligned with `docs/staging-secrets-matrix.md`.

### Staging service URLs (`VECINITA_STAGING_*`)

After sourcing `prod.env`, print DO ingress URLs (requires `DIGITALOCEAN_TOKEN`):

```bash
set -a && source prod.env && set +a
eval "$(uv run --with pydo --with pyyaml scripts/deploy/do_apps.py urls --frontend)"
```

Set Modal admin API separately (from last `modal deploy` or `docs/deploy-state.md`):

```bash
export VECINITA_STAGING_ADMIN_API_URL=https://vecinita--vecinita-data-management-fastapi-app.modal.run
```

Then run connectivity / staging smokes:

```bash
bash scripts/deploy/verify_connectivity.sh
# or: uv run pytest tests/smoke -m live -v
```

Canonical live URL table: `docs/deploy-state.md` §Live URLs.

### Example: DO hotfix redeploy

```bash
cd /path/to/vecinita
set -a && source prod.env && set +a
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-internal-write-api
```

### Example: production CORS check (no secrets in URL)

```bash
set -a && source prod.env && set +a
eval "$(uv run --with pydo --with pyyaml scripts/deploy/do_apps.py urls --frontend)"
curl -sS -D - -o /dev/null -X OPTIONS \
  "${VECINITA_STAGING_WRITE_URL}/internal/v1/documents/00000000-0000-0000-0000-000000000001" \
  -H "Origin: ${VECINITA_STAGING_ADMIN_FRONTEND_URL}" \
  -H "Access-Control-Request-Method: DELETE" \
  -H "Access-Control-Request-Headers: authorization"
```
