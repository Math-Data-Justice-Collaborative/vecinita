# Quickstart: Measure CI and Render build times

## 0. Governance baseline table (copy-paste)

Use this table in [artifacts/baseline-pre-optimization.md](./artifacts/baseline-pre-optimization.md) (or spreadsheets) so rows align with [data-model.md](./data-model.md) **TimingSample** fields. Per [spec.md](./spec.md) **FR-001**, keep **N ≥ 20** successful samples per row in the reporting window; if **N < 20**, set **`provisional`** to **yes** and extend the window or record an engineering-lead exception in the same artifact.

| `phase` | `change_category` | `median_sec` | `n_runs` | `cache_state` | `provisional` | `source` |
|---------|-------------------|--------------|----------|---------------|---------------|----------|
| e.g. `ci_job_backend-quality` | e.g. `infrastructure_or_workflow` | (fill) | (fill) | `warm` \| `cold` \| `unknown` | `yes` \| `no` | e.g. `github_actions` |
| e.g. `render_build` | e.g. `application_code_typical` | (fill) | (fill) | `warm` \| `cold` \| `unknown` | `yes` \| `no` | `render_dashboard` |

- **`phase`**: job id, workflow slice, or `render_build` / `ci_total` as defined in the artifact.
- **`source`**: `github_actions`, `render_dashboard`, `manual_export`, or other label from data-model.

## 1. GitHub Actions baseline

1. Open **Actions** → workflow **Tests** (`test.yml`).
2. Filter **branch** and **event** (e.g. `pull_request`).
3. For each critical job (`backend-quality`, `frontend-quality`, Schemathesis-related jobs if present), record **duration** for **≥20** successful runs in the baseline window.
4. Compute **median**; note **p90** if variance is high (concurrent runs / queueing).

Export: optional **API** or **gh run list`** for scripting (document exact `gh` commands in tasks if automated).

## 2. Render build-phase baseline

1. Render Dashboard → service → **Events** / **Logs**.
2. Filter **build** logs for deploys tagged as **code-only** (no Dockerfile or lockfile change).
3. Record platform-reported build duration or log timestamps from **build start** to **image ready**.

Optional: `make render-logs LOG_TYPE=build SERVICE_ID=...` (see root `Makefile`) for scripted samples.

## 3. Local parity checks

- **`make ci`** — full local gate (constitution).
- **`make test-schemathesis-gateway`** (and agent / data-management) — isolate one TraceCov session per OpenAPI (see `Makefile` comment on `test-schemathesis`).
- Compare local median (3 runs) only as a **sanity** signal; CI and Render remain authoritative for **FR-001**.

## 4. After changes

Repeat §1–§2 with the **same** change categories; document improvement vs baseline in the PR description (supports **SC-001**–**SC-003** and **User Story 3**).
