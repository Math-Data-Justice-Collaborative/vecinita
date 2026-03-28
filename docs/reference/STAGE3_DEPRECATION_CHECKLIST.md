# Stage 3 Deprecation Checklist (Root Manifests)

This checklist defines a low-risk path before deprecating or removing root-level dependency manifests:

- `package.json`
- `package-lock.json`
- `requirements.txt`

## Current State Summary

- Frontend CI and workflows install dependencies from `frontend/package-lock.json` using `npm ci`.
- Backend runtime and tests are standardized on `backend/pyproject.toml` with `uv` workflows.
- A backend-specific `backend/requirements.txt` exists and is used by backend-adjacent tooling.
- Root files still exist and may be used by ad-hoc local workflows; no move/removal should occur without deprecation gates.

## Deprecation Gates (Must Pass Before Any Move/Removal)

1. **Reference audit complete**
   - Search scripts, workflows, docs, and deployment configs for direct root-file usage.
   - Confirm no required production/deployment path depends on root files.

2. **Canonical replacements documented**
   - Frontend dependencies: `frontend/package.json` + `frontend/package-lock.json`.
   - Backend dependencies: `backend/pyproject.toml` (+ `uv.lock` if present) and `backend/requirements.txt` where explicitly needed.

3. **Compatibility window defined**
   - Decide deprecation period (for example, 1-2 release cycles).
   - Add warning notes in docs before physical removal.

4. **CI parity verified**
   - Confirm all CI jobs still pass without relying on root manifests.
   - Confirm local onboarding docs use service-local manifests only.

5. **Rollback plan prepared**
   - Keep a reversible commit for root-manifest changes.
   - Document exact restoration steps.

## File-by-File Low-Risk Plan

### `package.json` (root)

- **Risk:** medium (unknown ad-hoc local usage)
- **Pre-step:** inspect root npm script usage in team workflows.
- **Safe path:** mark as deprecated first; keep until confirmed unused.
- **Removal condition:** no CI/script/docs or team workflow depends on root npm commands.

### `package-lock.json` (root)

- **Risk:** medium (paired with root `package.json`)
- **Pre-step:** same gate outcome as root `package.json`.
- **Safe path:** deprecate alongside root `package.json`; remove together only.
- **Removal condition:** root `package.json` is removed or replaced with non-installable workspace metadata.

### `requirements.txt` (root)

- **Risk:** medium-high (Python install habits often default to root `requirements.txt`)
- **Pre-step:** verify no deployment/build tooling runs `pip install -r requirements.txt` from repo root.
- **Safe path:** deprecate with explicit migration note to backend dependency sources.
- **Removal condition:** all documented and automated Python install paths are backend-local (`uv` / `backend/requirements.txt`).

## Execution Order (When Approved)

1. Add deprecation notices in docs and README.
2. Keep root files in place during notice window.
3. Remove root files in a dedicated PR with CI + onboarding validation.
4. Update root-file organization policy status and changelog.
