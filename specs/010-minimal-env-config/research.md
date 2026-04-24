# Research: Minimal environment configuration

## Decision: Root template consolidation

**Decision**: Keep **one** authoritative root template file. Today `.env.local.example` is labeled canonical while `.env.example` points at it—implementation should **end the split**: either (a) make **`.env.example`** the single full catalog and reduce `.env.local.example` to a one-line pointer + “copy to `.env` or `.env.local`”, or (b) keep `.env.local.example` as full catalog and shrink `.env.example` to pointer only. Default recommendation in implementation: **(a)** — `.env.example` is the conventional discovery path for new contributors.

**Rationale**: Matches FR-001 and clarify **Option A**; reduces “which file do I copy?” confusion.

**Alternatives considered**: Two full files kept in sync (rejected: drift risk); only `.env.local.example` (rejected: weaker GitHub UX for browsers opening `.env.example` first).

---

## Decision: Config files vs environment variables

**Decision**: Use **committed configuration files** (YAML or TOML under e.g. `config/` or per-service `config/`) for **non-secret defaults** (timeouts, feature flags, public base URLs for internal dev, provider *names*, routing toggles). Keep **secrets and connection credentials** exclusively in **environment variables** (or secret managers in hosted environments). Python services merge **file defaults → env overrides** using **pydantic-settings** (custom settings source or explicit load + `BaseSettings` merge) without placing secrets in repo files.

**Rationale**: Aligns with stakeholder direction; reduces env size; keeps rotation and audit for secrets in platform-native stores.

**Alternatives considered**: All-in-env (rejected: works against minimization and clarity); secrets in config files encrypted (rejected: out of scope, high operational cost).

---

## Decision: Derive redundant values

**Decision**: Where one value fully determines another, **derive at runtime** in Pydantic (`computed_field`, validators) or a tiny shared helper—e.g. parse `DATABASE_URL` for `DB_HOST` / `DB_*` when those discrete fields are still needed for legacy scripts; align `VITE_SUPABASE_URL` with `SUPABASE_URL` **in documentation** and optionally add a **dev-only** check or script that warns on mismatch rather than duplicating keys in the template. Prefer **removing** duplicate template keys over silent magic when removal does not break `FR-009`.

**Rationale**: Meets “extract from another” requirement and SC-002; avoids copy-paste drift.

**Alternatives considered**: Codegen step for `VITE_*` (defer unless friction remains high); runtime injection into Vite (rejected: nonstandard).

---

## Decision: Soft deprecation implementation

**Decision**: Continue and extend **`AliasChoices`** on `BaseSettings` fields (see `shared_config`) for legacy names; add **centralized** `warnings.warn` or structured logging when a legacy alias is used, message includes **canonical field/env name only** (FR-008). Publish **end date** in migration documentation; post-window remove aliases in a **major** or labeled breaking release per team policy.

**Rationale**: Already idiomatic in repo; testable; no new dependency.

**Alternatives considered**: Separate `env_compat` shim module (possible if settings classes proliferate); fail-hard on legacy names (rejected: violates clarify **Option C**).

---

## Decision: Frontend (Vite) constraints

**Decision**: `VITE_*` remain **env-based** for build-time exposure; **non-secret** public URLs may still be duplicated in `frontend/.env.example` **or** documented as “must match root row X”; do **not** commit secrets into `VITE_*`. For **parity**, root template lists `VITE_*` in a clearly labeled “Frontend (build-time)” section.

**Rationale**: Vite cannot read server YAML at runtime in the browser; boundary is explicit.

**Alternatives considered**: `vite.config.ts` reading YAML (possible later; adds coupling).

---

## Decision: Baseline / SC-002 measurement

**Decision**: Implement migration doc appendix with **deduplicated union** table (per clarify **Option B**) generated once via script scanning committed `*.env.example` + prior README revision (git show) or manually curated snapshot—**methodology text** is mandatory in migration doc (FR-004, SC-002).

**Rationale**: Auditable; matches spec.

**Alternatives considered**: Count only root file (rejected by clarification).

---

## Decision: Contract tests

**Decision**: Replace or supplement retired `make env-sync-contract` with **pytest** (or shell + `grep`) tests that: (1) no high-entropy secret patterns in tracked `*.env.example`; (2) subsidiary examples contain pointer phrase to root; (3) optional: parse root template for required key set vs allowlist.

**Update (post-analyze remediation)**: Subsidiary pointer text is **fixed** to the exact substring in `contracts/configuration-resolution.md` **C4b** so `backend/tests/unit/test_env_example_templates.py` can assert it deterministically. Legacy→canonical rows live in committed **`config/env_aliases.example.yaml`** and must stay aligned with `docs/environment-migration.md` (**T017**). **Second pass**: C4b **Also** covers **`/.env.local.example`** when pointer-only; contract **C3** requires **acceptance** (e.g. `AliasChoices` or bootstrap `os.environ` copy), not warnings alone (**T007**, **T012**, **T017**).

**Rationale**: Constitution “verifiable delivery”; offline-safe.

**Alternatives considered**: Pre-commit only (good addition but not sufficient as sole gate).
