# BUG-2026-08-28 — Modal crash-loop: No module named 'infra'

## Error description

`vecinita-embedding` and `vecinita-data-management` containers repeatedly fail to start:

```text
ModuleNotFoundError: No module named 'infra'
Function … is crash-looping: containers are repeatedly failing to start.
```

Top-level `from infra.modal.repo_paths import resolve_repo_root` runs at container hydrate, but those app images did not mount `infra/` or put `/root` on `PYTHONPATH` (unlike `llm_app.py`).

## Error logs

Modal CLI (`modal app logs vecinita-embedding`, 2026-08-28):

```text
File "/root/embedding_app.py", line 18, in <module>
    from infra.modal.repo_paths import resolve_repo_root
ModuleNotFoundError: No module named 'infra'
Runner failed with exception: ModuleNotFoundError("No module named 'infra'")
```

Same pattern every ~10 minutes for embedding + data-management.

## Investigation

1. PR #280 merge CI/CD green on `main`.
2. Modal CLI already authenticated (`modal` 1.5.4).
3. Confirmed crash-loop on embedding + data-management; llm mounts `/root/infra` correctly.
4. Root cause: missing `.add_local_dir(…/infra, remote_path="/root/infra")` + `/root` on `PYTHONPATH`.

## Repro test

`tests/bugs/test_bug_2026_08_28_modal_infra_mount_crash_loop.py` — asserts embedding / data-management / rerank images mount infra.

## Fix

Mount `infra` → `/root/infra` and prepend `/root` to `PYTHONPATH` in embedding, data-management, and rerank Modal apps. Redeploy those apps after merge.
