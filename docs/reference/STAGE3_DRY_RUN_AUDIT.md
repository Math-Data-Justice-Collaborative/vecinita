# Stage 3 Dry-Run Audit (Root Manifests)

Date: 2026-02-27

Scope audited:

- root `package.json`
- root `package-lock.json`
- root `requirements.txt`

## Verdict Summary

| Manifest | Deprecation Notice | Physical Removal | Verdict |
|---|---|---|---|
| `package.json` (root) | GO | NO-GO | Keep during deprecation window |
| `package-lock.json` (root) | GO | NO-GO | Keep paired with root `package.json` |
| `requirements.txt` (root) | GO | NO-GO | Keep until external build/deploy usage is disproven |

## Evidence

### Frontend dependency consumption is service-local

- CI frontend jobs use `frontend/package-lock.json` cache and run in `frontend/`:
  - [.github/workflows/test.yml](../../.github/workflows/test.yml#L173)
  - [.github/workflows/test.yml](../../.github/workflows/test.yml#L176-L177)
  - [.github/workflows/test.yml](../../.github/workflows/test.yml#L195-L199)
- Frontend coverage workflow is also service-local:
  - [.github/workflows/frontend-coverage.yml](../../.github/workflows/frontend-coverage.yml#L29)
  - [.github/workflows/frontend-coverage.yml](../../.github/workflows/frontend-coverage.yml#L32-L33)
- Frontend Docker build uses local frontend manifests:
  - [frontend/Dockerfile](../../frontend/Dockerfile#L24-L27)

### Backend requirements consumption is service-local

- Backend scraper modal deployment installs from `backend/requirements.txt`:
  - [backend/src/services/scraper/modal_app.py](../../backend/src/services/scraper/modal_app.py#L21)

### Root manifests are still ambiguous for ad-hoc/external usage

- Root `package.json` is present and installable (contains dependencies):
  - [package.json](../../package.json)
- Root `requirements.txt` is present and installable:
  - [requirements.txt](../../requirements.txt)
- No mandatory in-repo workflow/script consumer was found that explicitly requires root manifests, but absence of in-repo references does not prove absence of external usage.

## Go/No-Go Rationale

### Root `package.json`

- GO for deprecation notice: in-repo CI/Docker usage is frontend-local.
- NO-GO for removal now: potential ad-hoc local commands from repo root remain plausible.

### Root `package-lock.json`

- GO for deprecation notice: no in-repo CI path depends on root lockfile.
- NO-GO for removal now: should be removed only with root `package.json` after notice period.

### Root `requirements.txt`

- GO for deprecation notice: backend automation references backend-local requirements.
- NO-GO for removal now: external build/deploy assumptions (`pip install -r requirements.txt` at repo root) cannot be ruled out from code search alone.

## Required Preconditions Before Any Removal PR

1. Add explicit deprecation notice in root docs for these three files.
2. Confirm with maintainers that no external platform or local SOP depends on root manifests.
3. Keep one release-cycle compatibility window.
4. Open dedicated removal PR with rollback note and full CI validation.
