# Quickstart: Verifying minimal env work (feature 010)

Use this after implementation lands to confirm behavior matches `spec.md` and `contracts/configuration-resolution.md`.

## 1. Templates and pointers

1. Open the **root** canonical template (expected: `.env.example` after consolidation).
2. Confirm sections distinguish **required** default-local keys vs **optional profiles**.
3. Open each subsidiary `*.env.example` **and** (when pointer-only) **`/.env.local.example`**; within the **first 40 lines**, confirm the exact substring **`Canonical environment catalog: repo root .env.example`** appears (contract C4b).

## 2. No secrets in repo examples

From repo root (example using `git grep` — adjust if project adds automated test instead):

```bash
# Heuristic: fail if obvious sk-/Bearer tokens appear in example env files
git grep -nE '(sk-[a-zA-Z0-9]{10,}|Bearer [a-zA-Z0-9]{20,})' -- '*.env.example' '.env*.example' || true
```

Expect **no matches** in tracked templates. Prefer running the project’s pytest contract module once added in `/speckit.tasks`.

## 3. Soft deprecation warning

1. Set a **legacy** env name (from `config/env_aliases.example.yaml` / migration mapping) instead of the canonical one for one field.
2. Start a **default local** service: verify **both** paths when implemented—**data-management** services using `shared_config` **and** chat **`backend/src/config.py`** (gateway/agent) after **T012** lands.
3. Observe logs/stderr: warning references **canonical** name, **not** secret material.

## 4. SC-002 baseline (documentation)

1. Open **migration documentation** linked from README.
2. Verify **before** count uses **deduplicated union** methodology text and tables.
3. Verify **after** required count meets **≥ 50%** reduction claim against that baseline.

## 5. Config file merge (if implemented)

1. Place a non-secret override in `config/defaults.example.yaml` (or untracked `config/defaults.yaml`).
2. Unset matching env var: service should use YAML default.
3. Set env var: service should prefer **env** over file (override rule).

## 6. Regression suite

Run **`make ci`** from repository root before declaring the feature merge-ready.
