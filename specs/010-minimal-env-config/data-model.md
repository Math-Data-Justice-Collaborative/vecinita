# Data model: Minimal environment configuration

Logical model for settings resolution, documentation, and migration—not a new database schema.

## Entity: `EnvironmentSetting`

| Attribute | Description |
|-----------|-------------|
| `name` | Canonical env name (e.g. `SUPABASE_URL`). |
| `description` | Short plain-language purpose for templates/docs. |
| `class` | `required_default_local` \| `optional_profile` |
| `profile` | When optional: profile id (e.g. `modal`, `langsmith`, `render_hooks`). |
| `sensitivity` | `secret` \| `non_secret` |
| `source` | Where default non-secret value comes from: `config_file` \| `env_only` \| `derived` |
| `derivation` | If `derived`: rule reference (e.g. `from_database_url_host`) or human doc step. |
| `aliases` | Legacy names accepted during transition (soft deprecation). |

**Validation rules**

- `secret` MUST NOT appear in committed config files—only in env or secret store.
- `required_default_local` MUST appear in root template with placeholder or empty value as appropriate.
- `aliases` MUST be listed in migration documentation with end-of-support date.

## Entity: `CapabilityProfile`

| Attribute | Description |
|-----------|-------------|
| `id` | Stable slug (`modal`, `tavily`, …). |
| `title` | Human title for docs. |
| `setting_names` | List of `EnvironmentSetting.name` unlocked by this profile. |
| `doc_anchor` | Link target inside migration or README section. |

**Relationships**

- **1:N** — Profile → many optional `EnvironmentSetting` rows.

## Entity: `CanonicalTemplate`

| Attribute | Description |
|-----------|-------------|
| `path` | Repo-root file path (e.g. `.env.example`). |
| `sections` | Ordered groups: `required`, then per-profile blocks. |
| `format` | `dotenv` key=value with comments. |

**Relationships**

- **1:N** — Template section lines map to `EnvironmentSetting`.

## Entity: `SubsidiaryExample`

| Attribute | Description |
|-----------|-------------|
| `path` | e.g. `frontend/.env.example`. |
| `pointer_text` | Required phrase pointing readers to root `CanonicalTemplate`. |
| `allowed_keys` | Minimal `VITE_*` or service-local-only keys not duplicated at root. |

## Entity: `DeprecationNotice`

Emitted at runtime when an alias is used (not persisted).

| Attribute | Description |
|-----------|-------------|
| `legacy_name` | Which alias was read. |
| `canonical_name` | Replacement. |
| `channel` | `logging` / `warnings` — must not include secret values. |
| `removal_date` | From migration documentation. |

## Entity: `MigrationDocumentation`

| Attribute | Description |
|-----------|-------------|
| `dedicated_path` | File under `docs/` (exact path in tasks). |
| `baseline_method` | Text: union of examples + prior guide. |
| `baseline_required_count` | Integer “before”. |
| `target_required_count` | Integer “after” (post-change). |
| `mapping_table` | Old → new name rows, profile, removal dates. |

**State**

- Draft → Published with repo release (process only).
