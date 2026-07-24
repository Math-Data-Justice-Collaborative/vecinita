# Pipeline skills preamble (00–18)

Shared conventions for numbered pipeline stage skills. Every stage `SKILL.md` under
`.cursor/skills/00-context` … `18-pr-review` follows this preamble unless a stage
explicitly documents an exception.

**Orchestrators** (not numbered stages): [pipeline](pipeline/SKILL.md) (greenfield **session**),
[16-evolve](16-evolve/SKILL.md) (feature / new_service **sessions**).

**State agent (mandatory):** [workflow-state-manager](../agents/workflow-state-manager.md) —
sole writer of `workflow-state.yaml`.

**Sessions:** [sessions-reference.md](sessions-reference.md) — session-first work model; ephemeral
reports under `docs/sessions/{session-id}/`, standing specs stay in `docs/` root.

**Deep policy** (do not duplicate in each skill): [considerations.md](considerations.md),
[connectivity-gates.md](connectivity-gates.md),
[workflow-state-reference.md](workflow-state-reference.md).

---

## Sessions (session-first work model)

Every bounded unit of work runs inside a **session** with an explicit, user-approved routing
plan. Full convention: [sessions-reference.md](sessions-reference.md).

| Concept | Summary |
|---------|---------|
| **Session** | `S{NNN}-{slug}` bounded work unit; opened by [00-context](00-context/SKILL.md), tracked in `workflow-state.yaml` §`active_session` |
| **Session types** | `greenfield`, `feature`, `new_service`, `hotfix`, `integration`, `ops`, `process` |
| **Routing plan** | `docs/sessions/{id}/routing-plan.md` — approved stage list + skip rationale |
| **Reports** | Stage outputs under `docs/sessions/{id}/reports/` (not `docs/` root) |
| **Standing docs** | Long-lived specs stay in `docs/` root; session deltas append a §Session changelog |
| **Dual-layer state** | `project.stages.*` = historical baseline; `active_session` = current work unit |

**Stage obligation (01–19):** require `active_session` (else block → 00-context), confirm the
stage is in `active_session.routing_plan`, write reports to `active_session.artifacts_dir/reports/`,
and mirror `project.stages.{key}` on completion. **00-context** is the session opener and is exempt.

---

## 1. Purpose and numbering

| Range | Phase | Skills |
|-------|-------|--------|
| **00–03** | A — Product planning | Context (optional), requirements, verify plan, plan tooling |
| **04–06** | B — Technical planning | Tech plan, verify tech, tech tooling |
| **07–08** | C — Build | Build, verify build (milestone gate) |
| **09–13** | D — Verify & deploy | QA + E2E (parallel), verify impl, verify deploy, deploy smoke |
| **14–15** | E — Maintenance (on-demand) | Hotfix, service health |
| **16–17** | F — Change & learn (on-demand) | Evolve (features + scope), retrospective |
| **18** | G — Review (on-demand) | PR review (GitHub post, no merge) |

Stages are **linear in greenfield** ([pipeline](pipeline/SKILL.md)). Stages **14–18** are
**on-demand** and may re-invoke subsets of 00–15 in **delta mode**.

**Any stage 00–17** may accept a user request to **add features** onto the current application
when an active evolve cycle exists or after prerequisite checks pass — see §Feature addition.

---

## 2. SKILL.md frontmatter

Each numbered skill includes YAML frontmatter:

```yaml
---
name: NN-short-name    # matches folder, lowercase hyphens
description: >
  Third-person summary: WHAT the stage does and WHEN to invoke it.
  Include trigger terms (e.g. "requirements interview", "deploy smoke", "add feature").
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
| **State management** | workflow-state-manager agent — read/update protocol |
| **Delta / feature-addition mode** | Behavior when adding features or in evolve cycle |
| **Workflow** | Step-by-step work for this stage |
| **Output rules** | Artifacts, commits, handoff to next stage |
| **Continue** | Verbatim “Enter this into the chat to continue:” block with the next `@.cursor/skills/NN-…/SKILL.md` (plus any trailing notes) |

Orchestrators (16) add: routing plans, phase gates, safe stopping points, child-skill tables.

Every numbered stage skill **ends** with a **Continue** section. When the stage completes,
print that block verbatim at the end of the user-facing summary so the user can paste the
next skill into chat. If `active_session.routing_plan` names a different next stage,
substitute that skill’s `@.cursor/skills/.../SKILL.md` path.

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

## 5. State management (workflow-state-manager)

**Single canonical file:** repo-root [`workflow-state.yaml`](../workflow-state.yaml).

**Sole writer:** [workflow-state-manager](../agents/workflow-state-manager.md). Pipeline skills
**must not** read or edit `workflow-state.yaml` directly — always invoke the agent.

| Rule | Requirement |
|------|-------------|
| **Read first** | Invoke agent `operation: read_context` as first action on every invocation |
| **Write via agent** | Invoke agent `operation: update` after each substep — never buffer |
| **Resume** | Agent context brief reports `status`, timestamps, substeps, active cycles |
| **Stage key** | Agent maps `skill_id` → `stages.{key}` (e.g. `stages.07-build`) |
| **Cycles** | `evolve_cycles[]` (16-evolve), `retrospective_cycles[]` (17), `pr_review_cycles[]` (18-pr-review), `pr_remediation_cycles[]` (19-address-pr-review) |
| **Cross-stage issues** | Agent appends `issue_log` with category + evidence |
| **Artifacts** | Agent appends paths to top-level `artifacts[]` on completion |
| **Deviations** | Agent returns **blocking** issues → skill must AskQuestion; do not proceed |

### On invocation (standard pattern)

1. Invoke **workflow-state-manager** with `read_context` + `skill_id` + optional `user_intent`.
2. If agent returns **blocking deviations**: AskQuestion with evidence; stop until resolved or user waives.
3. If stage **`completed`**: AskQuestion — reuse / update section / restart (agent confirms).
4. If **`in_progress`**: Report substeps from context brief; AskQuestion — resume or restart.
5. If **`pending`** or **`skipped`**: Start or remain skipped per stage rules.
6. After work begins, invoke agent `update` to set `in_progress` + `started_at`.

Detail state may also live in stage reports (`docs/sessions/S000-internal-docs-archive/execution-plan.md`, session `reports/*.md`, etc.);
**stage completion** must still be mirrored via agent `update`.

Schema detail: [workflow-state-reference.md](workflow-state-reference.md).

---

## 6. Feature addition (any stage)

Users may say **"add features X, Y, Z"** at any point — not only via 16-evolve.

| Situation | Behavior |
|-----------|----------|
| **Existing app, no active evolve cycle** | Agent blocks → recommend [16-evolve](16-evolve/SKILL.md) (one cycle, multiple Fn) |
| **Active evolve cycle** | Current stage runs in **delta mode** for scoped Fn |
| **Greenfield (no specs yet)** | Route to [pipeline](pipeline/SKILL.md) or 01-requirements |
| **User names features at stage N** | Stage invokes agent with `user_intent`; agent sets `mode: delta` when cycle active |

**Default for multiple features:** one **evolve cycle** with multiple **Fn** (e.g. F19, F20, F21)
— shared specs and build where dependencies allow.

**Orchestrator:** [16-evolve](16-evolve/SKILL.md) owns intake, routing, phase checkpoints, and
multi-feature cycles. Individual stages execute their slice in delta mode when invoked directly
or as child of 16-evolve.

---

## 7. Delta mode

When `mode: delta` or an active `evolve_cycles[]` entry applies:

- Pass evolve context to child stages: `evolve_cycle_id`, `feature_ids[]`, `scope`,
  `affected_artifacts[]`, `delta_only: true`.
- Update **only** sections tied to the change; no full doc regeneration without user approval.
- One child stage at a time (except **09 + 10** in parallel).
- **16-evolve** adds mandatory **phase checkpoints** (digest + AskQuestion) between A–D.

Per-stage delta rules live in each skill §Delta / feature-addition mode and
[16-evolve/reference.md](16-evolve/reference.md).

---

## 8. User authority and AskQuestion

**The user is the source of truth.** Specs and plans trace to interview answers or explicit
approvals — not agent inference.

### AskQuestion protocol ([considerations.md](considerations.md) §7)

| Rule | Detail |
|------|--------|
| **Blocking issues** | Never silently resolve — always AskQuestion |
| **Agent deviations** | Present agent evidence verbatim; first option = recommended path |
| **Batching** | 2–4 questions per call when found together |
| **Recommendation** | First option = recommended with rationale |
| **Escape hatch** | Last option = `Let me explain / provide more context` |
| **Categories** | Label prompts: `[Decision]`, `[Ambiguity]`, `[Contradiction]`, `[Uncertainty]`, `[Scope Drift]`, `[Template Drift]` |
| **Evidence** | Cite spec section, code path, workflow-state, or user answer |

Stages that **collect choices for a later stage** (e.g. 09-qa → 11-verify-impl) may defer
AskQuestion to the handoff skill; that exception must be stated in the stage SKILL.md.

---

## 9. Phase gates and prerequisites

Downstream stages **must not start** until upstream gates pass (unless user waives via AskQuestion).
The **workflow-state-manager** enforces this in `read_context`; skills treat blocking deviations as hard stops.

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

## 10. Git, branches, and commits

Per [considerations.md](considerations.md) §11–12 and [workflow-state-reference.md](workflow-state-reference.md) §Git history:

| Rule | Detail |
|------|--------|
| **Commit-as-you-go** | Commit before next stage, blocking AskQuestion, gate check, or session end |
| **Atomic commits** | One logical change; repo valid after each commit |
| **Record commits** | Agent `update` appends `git_history.commits` with `stage: "NN-…"` |
| **Branches** | `feat/`, `fix/`, `docs/`, `chore/`, `infra/`, `evolve/{id}-{slug}` |

**User rule override:** Do not commit unless the user asked — pipeline skills still **prepare**
commits and record intent via agent when commits are deferred.

---

## 11. Decisions, ADRs, and fix-in-place

| Mechanism | When |
|-----------|------|
| **ADR** | Resolved `[Decision]`, non-obvious `[Ambiguity]`, structural tech choices — `docs/adr/ADR-NNN.md` |
| **Decision logs** | `docs/decisions.md#requirements-decisions-01-requirements`, `docs/decisions.md#technical-decisions-05-verify-tech`, `docs/decisions.md#evolve-cycle-decisions` |
| **Fix in place** | Verification failure → patch code, spec, hook, or infra — **do not re-run whole phases** |
| **Bugs** | [bug-investigation](bug-investigation/SKILL.md) + [14-hotfix](14-hotfix/SKILL.md) |

Classify failures per considerations §1: **spec** vs **code** vs **infra** vs **tooling** before choosing remediation.

---

## 12. Specs and artifacts

| Convention | Detail |
|------------|--------|
| **Output directory** | Default `docs/` (`workflow-state.yaml` §project.output_directory) |
| **Templates** | Stage 01 fills from `templates/`; manifest user-approved before generation |
| **Execution plan** | `docs/sessions/S000-internal-docs-archive/execution-plan.md` — 07-build source of truth for tasks |
| **No invention** | Do not add requirements, SLOs, or dependencies not in specs or user answers |
| **Scope drift** | Work outside approved feature list → `[Scope Drift]` AskQuestion |

Project rules (`.cursor/rules/`) enforce plan-adherence, domain vocabulary, and constraints —
stages **03** and **06** install or update those guardrails.

---

## 13. Verification and connectivity tiers

| Tier | Meaning | Typical stage |
|------|---------|---------------|
| **H0c** | CORS unit tests | 06, 07, 09, 13 |
| **H0i** | Integration (API + DB, mocked upstreams) | 07, 09, 10 |
| **H1–H3** | Live API smokes | 13, 15 |
| **H4–H5** | Browser connectivity (CORS live + VITE bundle) | 11, 12, 13 |

`curl` API success is **not** proof the UI works in production. Vitest mocks are **not** T3 E2E.

Live H1–H5, DO deploy, Modal deploy, and hotfix production verification **must** load operator
secrets from repo-root **`prod.env`** (see §17) before running shell commands — do not ask the
user to paste tokens when `prod.env` exists.

---

## 14. Stage roles (summary)

| Skill | Primary output | Blocks |
|-------|----------------|--------|
| **00-context** | Session `context-brief.md` + **`checkpoints/01-requirements-seed.md`** (when 01 is routed) | Optional (but seed mandatory before 01) |
| **01-requirements** | Product spec suite (loads 00 seed in Phase 0C) | Yes (start of A) |
| **02-verify-plan** | Audit report, verified specs | Yes |
| **03-plan-tooling** | Cursor rules, hooks, skills, agents | Yes |
| **04-tech-plan** | Execution plan, tech docs, ADRs | Yes (start of B) |
| **05-verify-tech** | Tech audit | Yes |
| **06-tech-tooling** | Hooks, CI, formatters, smoke layout | Yes |
| **07-build** | Code, tests, PRs | Yes (start of C) |
| **08-verify-build** | `docs/sessions/{id}/reports/verification-report.md` | Milestone gate |
| **09-qa** | `docs/sessions/{id}/reports/qa-report.md` | Parallel with 10 |
| **10-e2e** | `docs/sessions/{id}/reports/e2e-report.md` | Parallel with 09 |
| **11-verify-impl** | `docs/sessions/{id}/reports/verify-impl.md` | Yes |
| **12-verify-deploy** | `docs/deploy-checklist.md` | Yes |
| **13-deploy-smoke** | Deploy, smokes, CHANGELOG | Yes (end of D) |
| **14-hotfix** | BUG report + fix + optional redeploy | On-demand |
| **15-service-health** | Health report | On-demand |
| **16-evolve** | Features, delta specs, selective 00–15, checkpoints | On-demand |
| **17-retrospective** | Retro report + skill patches | On-demand |

---

## 15. Standard cross-cutting line (for SKILL.md)

Paste immediately after the stage title paragraph:

```markdown
**Preamble:** [pipeline-preamble.md](../pipeline-preamble.md) — shared conventions for stages 00–19.
**Sessions:** [sessions-reference.md](../sessions-reference.md) — requires `active_session` unless waived; reports under `docs/sessions/{id}/reports/`.
**Cross-cutting:** [considerations.md](../considerations.md), [connectivity-gates.md](../connectivity-gates.md).
**State agent:** [workflow-state-manager](../../agents/workflow-state-manager.md) — mandatory read/update.
```

Then add the stage-specific **Connectivity (stage NN)** section (when applicable).

---

## 16. Safe stopping and session end

Every **stage boundary** is a safe stop. Natural pause points:

- After **03** or **06** — planning complete for that phase
- After **08** at a milestone — partial build verified
- After **11** — built and verified; deploy optional
- After **13** — deployed
- Mid **evolve cycle** — see 16-evolve §Safe stopping points

On session end: invoke workflow-state-manager `update` to reflect last completed substep;
uncommitted work is a process violation unless the user deferred commits.

---

## 17. Operator environment (`prod.env`)

Repo-root **`prod.env`** is the canonical **local operator secrets file** (gitignored per
`.gitignore`). Stages **13–15**, **14-hotfix** deploy phases, and any live `pytest -m live` /
`scripts/deploy/*.sh` run **must** load it before invoking DO, Modal, Postgres, or staging smokes.

### Rules

| Rule | Detail |
|------|--------|
| **Read first** | If `prod.env` exists at repo root, `source` it — do not prompt for tokens already in that file |
| **Never commit** | Do not add `prod.env` to git; do not echo secret values in chat, logs, or bug reports |
| **Corpus safety** | If `DATABASE_URL` host is `.ondigitalocean.com`, do **not** run `pytest` / corpus seeds in the same shell — see [corpus-db-safety](corpus-db-safety/SKILL.md) |
| **Missing file** | AskQuestion: user provides path, creates `prod.env`, or pastes vars for one-off use |
| **Staging URLs** | Not stored in `prod.env` by default — derive via `do_apps.py urls` (below) or `docs/sessions/S000-internal-docs-archive/deploy-state.md` |

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
| `VECINITA_MODAL_EMBED_URL` | Modal embedding ASGI base (no `/health`); DO backends + GitHub CD — see [do-secrets-sync](do-secrets-sync/SKILL.md) |
| `VECINITA_MODAL_LLM_URL` | Modal LLM ASGI base; same sync path as embed URL |

Add other operator-only keys to `prod.env` locally as needed (e.g. `VECINITA_INTERNAL_API_KEY`
for authenticated curl smokes). Keep names aligned with `docs/staging-secrets-matrix.md`.

### Staging service URLs (`VECINITA_STAGING_*`)

After sourcing `prod.env`, print DO ingress URLs (requires `DIGITALOCEAN_TOKEN`):

```bash
set -a && source prod.env && set +a
eval "$(uv run --with pydo --with pyyaml scripts/deploy/do_apps.py urls --frontend)"
```

Set Modal admin API separately (from last `modal deploy` or `docs/sessions/S000-internal-docs-archive/deploy-state.md`):

```bash
export VECINITA_STAGING_ADMIN_API_URL=https://vecinita--vecinita-data-management-fastapi-app.modal.run
```

Then run connectivity / staging smokes:

```bash
bash scripts/deploy/verify_connectivity.sh
# or: uv run pytest tests/smoke -m live -v
```

Canonical live URL table: `docs/sessions/S000-internal-docs-archive/deploy-state.md` §Live URLs.

### Example: DO hotfix redeploy

```bash
cd /path/to/vecinita
set -a && source prod.env && set +a
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py sync-all-secrets
uv run --with pydo --with pyyaml scripts/deploy/do_apps.py deploy --name vecinita-internal-write-api
bash scripts/infra/do_verify_required_secrets.sh
```

After Modal URL rotation, also run `bash scripts/deploy/sync_github_secrets.sh --apply`.
Full checklist: [do-secrets-sync](do-secrets-sync/SKILL.md).

### Example: DO deploy only (no secret change)

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

---

## 18. Planning-only stages (00–06) — plan, don't build

Stages **00–06** are **planning stages**. When invoked — even early, out of order, or with a
user request that sounds like "just build it" — they **produce plans, not product code**. The
first stage that writes application/feature source code is **07-build**.

| Stage | May create | Must NOT create |
|-------|------------|-----------------|
| 00–02, 04–05 | `docs/` specs, ADRs, audits, decision logs | Any feature code under `src/`, `apps/`, `packages/` |
| 03-plan-tooling | `.cursor/` rules, hooks, skills, agents (guardrails) | Product/feature source code |
| 06-tech-tooling | `.cursor/` dev hooks/rules, tool config (ruff/pytest/tsconfig), CI workflow validation | Product/feature source code |

**Boundary:** "software" / "the build" = the product's feature implementation (business logic,
API handlers, UI components, jobs that fulfil F-numbers). That is **always deferred to 07-build**
and tracked as tasks in `docs/sessions/S000-internal-docs-archive/execution-plan.md`. Planning stages may write docs, guardrail/dev
**tooling**, and **config** scaffolding only when a spec or the execution plan calls for it — never
the feature implementation itself.

**If the user asks to implement a feature during 00–06:** capture it as a task/spec in the plan
and route to 07-build (via [pipeline](pipeline/SKILL.md) or [16-evolve](16-evolve/SKILL.md)) rather
than writing the code now. If the request is ambiguous, AskQuestion `[Scope Drift]` — first option
"plan this for 07-build (recommended)", with "switch to build now" as an alternative.
