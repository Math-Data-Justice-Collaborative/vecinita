# Contract: Required-checks manifest

**Feature**: 019-contract-ci-json-gate  
**Artifact**: committed `.ci/required-checks.json` (path fixed at implementation time; must match validator and docs).

## Purpose

Defines the authoritative set of checks (**FR-001**) that must each appear in `.ci/ci-attestation.json` with `status: passed` for the merge gate to succeed.

## File shape (JSON)

Top-level object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manifest_version` | integer | yes | Starts at `1`. Bump when breaking manifest shape. |
| `checks` | array | yes | Non-empty list of check objects. |

Each **check** object:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Stable slug; must match `^[a-z0-9][a-z0-9-]*$`. |
| `title` | string | yes | Short human title. |
| `description` | string | no | Optional longer text. |
| `command` | string | yes | Shell command from repo root (generator executes in a shell with `set -euo pipefail` behavior—implementation detail). |

## Invariants

1. **Unique ids**: No duplicate `id` within `checks`.
2. **Constitutional bar**: The manifest **MUST** include a check whose `command` runs `make ci` at repository root (see plan `research.md` R-008), with a stable `id` (e.g. `make-ci`).
3. **Attestation alignment**: For every manifest `id` **m**, there MUST be exactly one attestation entry in `checks` with the same `id` and `status: passed` for merge.

## Example (illustrative)

```json
{
  "manifest_version": 1,
  "checks": [
    {
      "id": "make-ci",
      "title": "Full local CI",
      "description": "Constitution merge-ready bar.",
      "command": "make ci"
    }
  ]
}
```

Extending the manifest (e.g. split lint vs test) is allowed as long as ids remain stable and documentation is updated.
