# Gitleaks resolution (QA-005)

## Summary

| Scan scope | Tool | Result |
|------------|------|--------|
| **Current working tree** | `scripts/check_secrets.sh` + `gitleaks detect --no-git` | **Clean** (0 findings) |
| **Full git history** | `gitleaks detect` (default, all commits) | **54 advisory** hits in **deleted** legacy paths only |

Vecinita was forked/evolved from a larger monolith. Historical commits still contain documentation and example code with **placeholder** credentials (curl examples, `rk_live_xxx`, env var templates). None of those paths exist in the current tree.

## Historical findings (54)

| Gitleaks rule | Count | Typical content |
|---------------|-------|-----------------|
| `curl-auth-header` | 36 | `Authorization: Bearer …` in deleted guides |
| `generic-api-key` | 14 | `API_KEY=…` / env examples in removed docs and `backend/` |
| `stripe-access-token` | 4 | Placeholder `rk_live_xxx` in deleted deployment docs |

Example paths (all removed from HEAD):

- `docs/guides/AUTH_PROXY_GUIDE.md`, `docs/reference/PROJECT_README.md`
- `backend/src/api/router_scrape.py`, `apps/scraper-worker/…`
- Root-level `ENV_VARIABLES_REFERENCE.md`, `DEPLOYMENT_*.md`
- `.github/render-llm.txt`, `.github/llm-txt/render-llm.txt`

## Why we did not rewrite git history

- **No live secrets in current code** — QA and CI scans target the working tree only.
- **History rewrite is destructive** — requires `git filter-repo` / BFG, **force-push**, and coordination for every clone and open PR.
- **Risk vs benefit** — placeholders in old docs do not grant access; rewriting 500+ commits adds operational risk without changing what ships today.

**Decision:** Accept advisory history risk; block merges on **current-tree** scans only.

## When a history rewrite might be warranted

Consider `git filter-repo` (with legal/security review) only if:

1. A **real** credential (not a doc placeholder) was committed and may still be valid, or
2. Compliance requires scrubbing history before open-sourcing or handing the repo to a third party, or
3. The default remote is **public** and auditors mandate zero gitleaks hits on `gitleaks detect` without `--no-git`.

Otherwise, keep history as-is and rely on CI `--no-git` + `scripts/check_secrets.sh`.

## Operator commands

### CI-equivalent (blocking — current files only)

```bash
bash scripts/check_secrets.sh
gitleaks detect --no-git --config .gitleaks.toml
```

### Full history audit (expect ~54 with allowlist for legacy paths)

```bash
gitleaks detect --config .gitleaks.toml
```

With `.gitleaks.toml` allowlists for deleted monolith paths, a full scan should report **0** or only new, actionable findings.

### Reproduce QA-005 counts (no allowlist)

```bash
gitleaks detect --report-format json --report-path /tmp/gitleaks.json
jq 'length' /tmp/gitleaks.json
```

## CI behavior

`.github/workflows/ci.yml`:

1. **`scripts/check_secrets.sh`** — blocking; ripgrep high-confidence patterns under `apps/`, `packages/`, `tests/`, `infra/`, `openapi/`.
2. **`gitleaks detect --no-git`** — blocking; default rules + Vecinita allowlist; does **not** traverse git history.

Pull requests are not failed by historical placeholder tokens in deleted files.

## Gitignored local runtime files

Developers keep staging/deploy credentials in files that are **gitignored** and must never be
committed:

| Path | Purpose |
|------|---------|
| `prod.env` | Staging/prod env vars for smokes and deploy scripts |
| `apps/*-frontend/.env` | Local Vite env (Supabase publishable key, dev API URLs) |
| `supabase/.env` | Local Supabase CLI secrets |
| `.deploy-keys.local` | Generated API keys for local deploy |
| `.tmp/` | Ephemeral operator artifacts (e.g. DO secret JSON exports) |
| `*-spec.yaml` (root) | Local `doctl apps spec get` exports (encrypted secrets) |

These paths are allowlisted in `.gitleaks.toml` so `gitleaks detect --no-git` passes locally
while CI still scans all **tracked** paths. Blocking gate remains `scripts/check_secrets.sh`
under `apps/`, `packages/`, `tests/`, `infra/`, `openapi/`.

## QA-S007-001 (2026-07-01) — false positives in working tree

| Finding | Resolution |
|---------|------------|
| `vecinita.eval.explore.v1` localStorage key in `evalDashboardStorage.ts` | Regex allowlist — public storage key name, not a credential |
| Supabase demo anon JWT in `scripts/ui/build_for_playwright.sh` | Path allowlist + regex for `iss":"supabase-demo"` prefix |
| Bundled JWT in `apps/*/dist/` after Playwright build | Path allowlist for `dist/` (gitignored build output) |
| QA reports quoting the above for traceability | Path allowlist for `docs/sessions/*/reports/qa-report.md` |
| Supabase publishable key in `apps/*-frontend/.env` (local Vite dev) | Path allowlist — gitignored; use `.env.example` placeholders in repo |

Re-verify: `gitleaks detect --no-git --config .gitleaks.toml` → **0 leaks**.

## Test fixtures

Integration tests use synthetic values such as `test-internal-key` for `VECINITA_INTERNAL_API_KEY`. These are not production secrets and are outside the high-confidence pattern set in `check_secrets.sh`.

## References

- QA report: `docs/qa-report.md` (Security — Git history)
- Finding: **QA-005**
- Config: `.gitleaks.toml`
- Script: `scripts/check_secrets.sh`
