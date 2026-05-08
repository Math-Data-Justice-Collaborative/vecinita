---
name: schemathesis-api-tests
description: Develop, run, and debug Schemathesis API tests with a CLI-first workflow. Use when working on API contract/property testing, especially for OpenAPI-driven endpoints and CI failures involving API test checks.
disable-model-invocation: true
---

# Schemathesis API Tests

## Goal

Use this skill to create and maintain Schemathesis tests from an API schema with a repeatable CLI-first loop:

1. Identify schema and target base URL.
2. Run bounded Schemathesis checks.
3. Reproduce and isolate failures.
4. Apply minimal root-cause fixes.
5. Re-run focused checks, then broader checks for confidence.

## Default Workflow (Checklist)

Copy this checklist and track progress:

```md
Schemathesis Task Progress
- [ ] Locate API schema path and target base URL
- [ ] Run a fast bounded Schemathesis command
- [ ] Capture failing operation, seed, and reproduction command
- [ ] Fix root cause (not workaround-only)
- [ ] Re-run focused command to verify fix
- [ ] Run broader Schemathesis sweep for regression confidence
- [ ] Integrate/confirm CI command and limits
```

## Step 1: Locate schema and runtime target

- Prefer local schema file path (for example: `openapi.json`, `openapi.yaml`).
- Set an explicit base URL with `--url` when schema host differs from runtime target.
- Keep test budget bounded while iterating.

## Step 2: Run fast bounded checks first

Use a short exploratory command before wider coverage:

```bash
st run ./openapi.yaml --url http://localhost:8000 --checks all --max-examples 25
```

If needed, scope to one endpoint during debug:

```bash
st run ./openapi.yaml --url http://localhost:8000 --include-path "/api/v1/items" --max-examples 25
```

## Step 3: Reproduce failures exactly

When a failure appears, preserve:

- operation/path
- random seed (if shown)
- failing payload / response snippet
- exact command used

Re-run with the same filters and seed to confirm determinism before editing code.

## Step 4: Fix root cause with minimal blast radius

- Prefer correcting schema drift, validation logic, status-code behavior, or serialization mismatches at the true source.
- Avoid broad exception masking or generic "return 200" workarounds.
- Keep code changes surgical and directly tied to the failing property/check.

## Step 5: Verify in expanding rings

1. Repeat the focused reproducer.
2. Re-run the related endpoint/tag slice.
3. Re-run a broader suite command.

Example progression:

```bash
# focused
st run ./openapi.yaml --url http://localhost:8000 --include-path "/api/v1/items" --max-examples 25

# broader
st run ./openapi.yaml --url http://localhost:8000 --checks all --max-examples 100
```

## CI Guidance

- Keep CI commands explicit and stable (schema path, base URL/source app fixture, max examples).
- Use a bounded example budget in CI to control runtime and noise.
- Prefer deterministic retry/debug path by recording command + filters from CI failures.

## Quick Command Templates

```bash
# Basic run
st run <schema-path> --url <base-url>

# Bounded run for local iteration
st run <schema-path> --url <base-url> --checks all --max-examples 25

# Scope by path during debugging
st run <schema-path> --url <base-url> --include-path "<path-fragment>" --max-examples 25
```

## Done Criteria

- Failure is reproducible before the fix.
- Root cause is fixed (not just hidden).
- Focused and broader Schemathesis commands pass.
- Any contract/schema-related tests affected by the change are updated in the same task.
