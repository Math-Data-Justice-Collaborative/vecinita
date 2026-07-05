---
name: feature-inspection
description: >
  Manual visual inspection of new features during 11-verify-impl. Opens the relevant admin or
  ChatRAG UI route in the browser (screenshots) and/or FastAPI Swagger UI (/docs) for API
  endpoints. Asks the user which surface and environment to inspect first, then blocks on
  Approve/Flag/Defer. Use when verifying implementation, walking through user journeys, or when
  the user asks to manually inspect a feature, UI page, or API contract.
---

# Feature Inspection (manual walkthrough)

Interactive **visual + contract inspection** during **11-verify-impl**. Complements automated
QA (09) and E2E (10) by showing the user what was built before signoff.

**Pipeline hook:** Phase 3b in [11-verify-impl](../11-verify-impl/SKILL.md) — run **before** the
feature-by-feature AskQuestion in Phase 3.

**Tool:** cursor-ide-browser MCP for UI; browser navigate to FastAPI `/docs` for Swagger.

**Reference:** [reference.md](reference.md) — URL matrix, routes, OpenAPI ↔ service map.

## When to use

| Surface | Inspect via |
|---------|-------------|
| Admin UI (`data-management-frontend`) | Browser → route from UJ |
| ChatRAG UI (`chat-rag-frontend`) | Browser → `/` or `/corpus` |
| ChatRAG API | Swagger → `{chat}/docs` |
| Data Management API (Modal) | Swagger → `{admin-api}/docs` |
| Internal write API | Swagger → `{write}/docs` |

Skip inspection (go straight to Phase 3 AskQuestion) when the delta is **backend-only with no
new/changed browser or Swagger-visible contract** — document the skip in `verify-impl.md`.

## Prerequisites

1. **09-qa** and **10-e2e** reports available (Phase 1 of 11).
2. Feature scope from `docs/feature-list.md` and linked UJ-NNN in `docs/user-journeys.md`.
3. OpenAPI paths from `openapi/*.yaml` when the feature adds or changes HTTP routes.
4. For UI inspection: target app reachable (local dev server or staging). If unreachable, report
   the blocker and offer to continue with OpenAPI file paths only.

## Workflow

Copy this checklist per feature in the active session cycle:

```
Feature inspection — [Fn / feature name]:
- [ ] Classify surfaces (UI / API / both)
- [ ] AskQuestion: environment (local vs staging)
- [ ] If both surfaces: AskQuestion — inspect UI first or API first?
- [ ] Inspect first surface (browser + screenshot)
- [ ] Inspect second surface (if applicable)
- [ ] AskQuestion: Approve · Flag · Defer · Explain
- [ ] Record in verify-impl.md
```

### Step 1 — Classify surfaces

From `docs/feature-list.md`, UJ entry points, and changed files:

| Signal | Surface |
|--------|---------|
| `apps/*-frontend/` or UJ browser steps | **UI** |
| `openapi/*.yaml`, FastAPI routes, UJ `POST/GET …` | **API** |
| Both | **both** — user picks order (Step 3) |

Note the **primary route** (admin) or **pathname** (chat) and **operationIds** / paths from
OpenAPI. See [reference.md](reference.md).

### Step 2 — Choose environment (AskQuestion)

Ask every time — do not assume:

```
prompt: "Feature inspection — [feature name]. Which environment?"

options:
  1. "Local dev (5173/5174 + localhost backends)"
  2. "Staging (deploy-state / workflow-state URLs)"
  3. "Skip live inspection — OpenAPI files + code refs only"
  4. "Let me explain / provide more context"
```

Resolve URLs from [reference.md](reference.md):

- **Local:** `docs/LOCAL_DEV.md` ports (5173 chat FE, 5174 admin FE, 8000 chat API, 8002 write API; Modal `serve` for DM API).
- **Staging:** `docs/sessions/S000-internal-docs-archive/deploy-state.md` §Live URLs or `workflow-state.yaml` §`deployment.staging.urls`.

If the chosen environment is not running, say so and offer: start instructions, switch environment, or skip.

### Step 3 — Pick inspection order (AskQuestion, both surfaces only)

```
prompt: "[Feature] has UI and API changes. Inspect which first?"

options:
  1. "UI first — then Swagger for the API"
  2. "API first (Swagger) — then UI"
  3. "UI only this round"
  4. "API only this round"
```

### Step 4 — UI inspection (browser MCP)

1. `browser_navigate` to `{baseUrl}{route}` (include query tabs, e.g. `/evaluation?tab=playground`).
2. **Admin auth:** protected routes need a Supabase session. If login wall appears, tell the user
   and either wait for manual login or skip UI with waiver in the report. Do not paste secrets.
3. Perform **minimal journey steps** from the UJ (nav click, tab switch, one representative action).
4. `browser_take_screenshot` — capture the feature area, not the whole desktop.
5. In chat, show the screenshot and cite: feature id, UJ-NNN, URL, what the user should verify.

**ChatRAG paths:** `/` (chat), `/corpus` (browse). **Admin paths:** see reference.md.

### Step 5 — API inspection (Swagger UI)

1. `browser_navigate` to `{apiBase}/docs` (FastAPI Swagger UI).
2. Find the **tag group** or **path** matching the feature (cross-check `openapi/*.yaml`).
3. Expand the new/changed operation; screenshot the operation block (method, path, schema summary).
4. In chat, link: Swagger URL, OpenAPI file path, `operationId`, and auth scheme if applicable.

**Auth notes:**

| API | Browser Swagger | Live try-it-out |
|-----|-----------------|-----------------|
| ChatRAG `/api/v1/*` | No auth | Usually works on staging |
| Internal write | JWT or API key | Prefer read-only GET; do not expose keys in chat |
| Data Management (Modal) | JWT + proxy key | Inspect schema only unless user supplies session |

Default: **show the contract in Swagger**; only execute Try-it-out when the user explicitly asks.

Repo OpenAPI source of truth (when server down): `openapi/chat-rag.yaml`, `openapi/data-management.yaml`, `openapi/internal-write.yaml`.

### Step 6 — Approval gate (AskQuestion)

After showing inspection artifacts:

```
prompt: "Manual inspection — [feature name]

  UI: [URL inspected | skipped — reason]
  API: [Swagger URL + paths | skipped — reason]

  Does what you see match your expectations?"

options:
  1. "Approve — matches expectations"
  2. "Flag — needs changes (I'll explain)"
  3. "Defer — review later"
  4. "Let me explain / provide more context"
```

**Flag** → feed into 11 Phase 4 patches. **Defer** → list in `verify-impl.md`; do not mark
11 `completed` for that feature without waiver.

### Step 7 — Record in session report

Append to `{active_session.artifacts_dir}/reports/verify-impl.md` §Manual inspection:

| Feature | Env | UI URL | Swagger URL | OpenAPI ops | Verdict |
|---------|-----|--------|-------------|-------------|---------|
| F37 Playground | local | …/evaluation?tab=playground | …/docs#/… | `createEvalPreset`, … | Approved |

Include screenshot filenames or inline references from the browser tool.

## Anti-patterns

- Do not mark 11 complete without running inspection or documenting a **skip waiver** per feature.
- Do not run full automated E2E here — that is **10-e2e**.
- Do not commit operator specs or paste `prod.env` secrets for auth.
- Do not inspect unrelated pages — stay on the UJ route and named endpoints.
- Do not treat T0 pytest green as substitute for this walkthrough when UI/API surfaces changed.

## Integration with 11-verify-impl

Run **Phase 3b (this skill)** after **Phase 3a journey signoff** and **before Phase 3** feature
AskQuestion. Phase 3 prompts may reference inspection verdicts ("you approved UI at …/playground").
