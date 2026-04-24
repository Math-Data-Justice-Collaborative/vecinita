# Contract: Configuration resolution (Vecinita)

**Applies to**: Python services using `shared_config.BaseServiceSettings` (and siblings), chat `backend/` settings modules, and any new root-level config loader introduced for this feature.  
**Out of scope**: Browser runtime (Vite) except where noted for parity checks.

## C1 — Secret vs non-secret sources

1. **Secrets** (API keys, tokens, passwords, private URLs with embedded credentials) MUST be read **only** from environment variables or the hosting platform’s secret mechanism.
2. **Non-secrets** (public URLs without credentials, timeouts, boolean feature flags, default ports) SHOULD default from **committed config files** when the repo adopts them for this feature; environment variables MAY override file defaults.
3. **Forbidden**: placing live secrets in `*.env.example`, `config/*.yaml`, or README.

## C2 — Derivation

1. If setting **B** is fully determined by setting **A** and both are non-secret, implementers SHOULD **derive B in code** and **omit B** from the root template unless a consumer outside Python still requires it (document exception in migration table).
2. If **B** is secret-derived from secret **A**, do **not** log derived values; prefer **not** duplicating secret **B** in templates when **A** suffices.

## C3 — Soft deprecation (aliases)

1. During the **published transition window**, resolving configuration MUST accept **canonical name** and **documented aliases** for the same logical field.
2. When an **alias** supplies the value, the process MUST emit a **DeprecationNotice**-equivalent: log or `warnings.warn` at **warning** level including **legacy name** and **canonical name** only.
3. Messages MUST NOT echo resolved secret values (FR-008).

**Implementation strategies (use together where applicable)**

- **Pydantic `AliasChoices`**: preferred inside `BaseSettings` models so the **resolved** field value accepts multiple env keys without manual `os.environ` scans.
- **Pre-parse / `os.environ` scan**: use for entrypoints that are **not** yet on Pydantic (e.g. early `backend/src/config.py`) or to emit a **single** warning when an alias key is set even if Pydantic would silently map it—must still print **names only**.
- **Machine-readable source of truth**: legacy→canonical rows MUST be listed in **`config/env_aliases.example.yaml`** (committed); human tables in `docs/environment-migration.md` MUST stay consistent with that file (same pairs).
- **Acceptance, not warnings alone**: For each supported `aliases[]` row during the transition window, runtime MUST still **resolve** the legacy env key to the same logical value as the canonical key—via **`AliasChoices` / `validation_alias` on the relevant `BaseSettings` field**, **or** by copying from the legacy key into the canonical key in bootstrap code **before** consumers read `os.getenv` for the canonical name. Emitting a warning **without** acceptance violates FR-008.

## C4 — Root vs subsidiary templates

1. The **root** canonical template MUST list all **required_default_local** and all **optional_profile** keys (grouped) except keys explicitly granted **subsidiary-only** status in the migration doc (e.g. certain `VITE_*` only used in one app).
2. Each **subsidiary** `*.env.example` MUST include pointer text to the root template within the **first 40 lines** (grep-friendly contract for tests).
3. Subsidiary files MUST NOT introduce **conflicting** defaults for the same logical key as the root template (same public URL family).

### C4b — Required pointer substring (tests)

Every **subsidiary** committed `*.env.example` (all paths under the repo except the root `/.env.example` itself) MUST contain the following **exact substring** within the **first 40 lines** of the file so `backend/tests/unit/test_env_example_templates.py` can assert it without ambiguity:

`Canonical environment catalog: repo root .env.example`

**Also**: `/.env.local.example` MUST include the same substring within its **first 40 lines** whenever that file is a **pointer** to the root catalog (not the full variable list), so it is covered by the same contract tests as other subsidiary templates.

## C5 — Service boundaries

1. Services MUST NOT read another service’s private env prefix for **new** couplings; shared keys live in **`shared_config`** or explicit env names documented in migration.
2. Cross-service URLs remain **typed fields** in settings (existing `scraper_service_url`, etc.) with **AliasChoices** for legacy env names—changes continue to honor OpenAPI-only boundaries for HTTP APIs.

## C6 — Frontend (Vite)

1. Only variables prefixed `VITE_` MAY be assumed available in browser code.
2. Root template MUST document which `VITE_*` keys are **required** for default local frontend builds; values MUST be **non-secret** public endpoints or placeholders.

## C7 — Verification hooks

1. CI or pytest contract tests MUST fail if a new **secret-shaped** literal appears in tracked example env files (pattern-based, allowlisted test fixtures excluded).
2. Optional: assert root template contains required key set from machine-readable manifest (future task if introduced).
