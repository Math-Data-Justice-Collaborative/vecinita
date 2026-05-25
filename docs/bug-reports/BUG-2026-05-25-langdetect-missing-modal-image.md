# BUG-2026-05-25 — Modal data-management crash: langdetect not installed

> Status: **investigating**  
> Feature: **F19–F22** (corpus tagging / EV-001)  
> Component: `infra/modal/data_management_app.py`, `packages/tagging`

## Error description

The Modal `vecinita-data-management` app crashes on container startup with
`ModuleNotFoundError: No module named 'langdetect'`. The app has been fully down since
the EV-001 deploy (2026-05-25) — every request returns a runner exception.

## Error logs

```text
Runner failed with exception: ModuleNotFoundError("No module named 'langdetect'")
Traceback (most recent call last):
  File "/pkg/modal/_runtime/container_io_manager.py", line 906, in handle_user_exception
    yield
  File "/pkg/modal/_runtime/user_code_imports.py", line 180, in execution_context
    finalized_functions = self.get_finalized_functions(self.function_def, container_io_manager)
  File "/pkg/modal/_runtime/user_code_imports.py", line 294, in get_finalized_functions
    web_callable, lifespan_manager = construct_webhook_callable(...)
  File "/pkg/modal/_runtime/user_code_imports.py", line 208, in construct_webhook_callable
    return asgi.asgi_app_wrapper(user_defined_callable(), container_io_manager)
  File "/root/data_management_app.py", line 91, in fastapi_app
    from vecinita_data_management_backend.jobs import run_job
  File "/opt/vecinita/apps/data-management-backend/vecinita_data_management_backend/jobs.py", line 10
    from vecinita_data_management_backend.pipeline import run_ingest_job, run_retag_job
  File "/opt/vecinita/apps/data-management-backend/vecinita_data_management_backend/pipeline.py", line 20
    from vecinita_tagging.vocabulary import (
  File "/opt/vecinita/packages/tagging/vecinita_tagging/vocabulary.py", line 11
    import langdetect
ModuleNotFoundError: No module named 'langdetect'
```

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Error — container crash on startup (ModuleNotFoundError) |
| Where | Production — Modal vecinita-data-management |
| When | Since EV-001 deploy (2026-05-25) — never worked with tagging |
| Frequency | Every time (100% — app cannot start) |
| Repro env | Production only (container image issue) |
| Severity | Critical — data management app fully down |
| Evidence | Modal runner logs (repeated crash loop) |
| Tried | Nothing |

## Remediation path

**local-first** — fix image definition, deploy only after user approval.

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `langdetect` not in Modal image `pip_install()` | **Confirmed** — image installs fastapi, httpx, pydantic only; tagging package mounted via add_local_dir without its deps |

## Root cause

**Dependency issue.** The Modal image in `infra/modal/data_management_app.py` mounts
`packages/tagging` via `add_local_dir()` which copies source files but does not install
Python dependencies. The `vecinita-tagging` package declares `langdetect>=1.0.9` in its
`pyproject.toml`, but `langdetect` is never `pip_install()`ed in the Modal image definition.

Import chain: `fastapi_app()` → `jobs.py` → `pipeline.py` → `vecinita_tagging.vocabulary`
→ `import langdetect` → **ModuleNotFoundError**.

## Spec conformance

| Spec | Status |
|------|--------|
| `docs/feature-list.md` | F19–F22 (EV-001 tagging) — in scope |
| `docs/dependency-inventory.md` | `langdetect>=1.0.9` listed under vecinita-tagging |
| `docs/deployment-integration.md` | Modal data-management image must include all package deps |

No blocking drift — fix is adding the declared dependency to the image.

## Repro test

| File | Status |
|------|--------|
| `tests/bugs/test_bug_2026_05_25_langdetect_missing_modal_image.py` | RED before fix |

## TDD iteration log

| # | Action | Result |
|---|--------|--------|
| 1 | Write AST test checking pip_install includes langdetect | Expect RED |

## Verification plan

- **Success criterion:** Modal data-management app starts without ModuleNotFoundError
- **Layer 1:** Repro test green + full CI parity (local)
- **Layer 2:** Verify import chain works locally
- **Layer 3:** Modal deploy + app responds (user-approved)
- **Layer 4:** Production smoke POST /jobs (user-approved)

## Fix

Add `"langdetect>=1.0.9"` to the `pip_install()` chain in
`infra/modal/data_management_app.py`.

## Timeline

| Event | Date |
|-------|------|
| EV-001 deployed (introduced tagging) | 2026-05-25 |
| User reported crash | 2026-05-25 |
| Bug report opened | 2026-05-25 |

## Verification

### Layer 1 — Automated
- [ ] Repro test red before fix
- [ ] Repro test green after fix
- [ ] Full CI parity (local) pass

### Layer 2 — Reproduction
- [ ] Import chain `vecinita_tagging.vocabulary` succeeds locally

### Layer 3 — Pre-deploy smoke
- [ ] Modal deploy succeeds (user-approved)

### Layer 4 — Production
- [ ] App responds to requests post-deploy (user-approved)

## Prevention & countermeasures

_(Filled in Phase 5)_

## Cursor rule

_(Filled in Phase 5)_

## Follow-ups

_(Filled in Phase 5)_

## Regression prevention

- `tests/bugs/test_bug_2026_05_25_langdetect_missing_modal_image.py`
