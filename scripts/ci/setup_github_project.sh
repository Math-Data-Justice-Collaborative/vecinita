#!/usr/bin/env bash
# Configure Vecinita org project #3: Status options + README + repo labels.
# Requires: gh auth with read:project + project scopes.
set -euo pipefail

OWNER="Math-Data-Justice-Collaborative"
PROJECT_NUMBER=3
REPO="${OWNER}/vecinita"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

require_project_scope() {
  if ! gh auth status 2>&1 | rg -q 'project'; then
    echo "Missing project scope. Run:" >&2
    echo "  gh auth refresh -h github.com -s read:project,project" >&2
    exit 1
  fi
}

create_labels() {
  local spec name desc color rest
  for spec in \
    "evolve|Part of an evolve cycle|5319E7" \
    "hotfix|Production or staging regression|B60205" \
    "app:chat-rag|ChatRAG backend or frontend|1D76DB" \
    "app:admin|Data management / admin UI|0E8A16" \
    "app:infra|Modal, DO, CI, migrations|FBCA04" \
    "privacy|ADR-004 / no-PII impact|D93F0B" \
    "deploy|Requires staging smoke or production deploy|006B75" \
    "blocked|Explicit blocker|000000"; do
    name="${spec%%|*}"
    rest="${spec#*|}"
    desc="${rest%%|*}"
    color="${rest##*|}"
    gh label create "$name" -R "$REPO" -d "$desc" -c "$color" -f
  done
}

fetch_status_field_id() {
  gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json \
    --jq '.fields[] | select(.name == "Status") | .id'
}

update_status_options() {
  local field_id="$1"
  jq -n --arg fieldId "$field_id" '{
    query: "mutation($fieldId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]!) { updateProjectV2Field(input: { fieldId: $fieldId, singleSelectOptions: $options }) { projectV2Field { ... on ProjectV2SingleSelectField { name options { id name } } } } }",
    variables: {
      fieldId: $fieldId,
      options: [
        {name: "Backlog", color: "GRAY", description: "Groomed or deferred work"},
        {name: "Ready", color: "BLUE", description: "Specd and unblocked"},
        {name: "In progress", color: "YELLOW", description: "Active branch or draft PR"},
        {name: "In review", color: "PURPLE", description: "PR open awaiting review"},
        {name: "Blocked", color: "RED", description: "Waiting on decision or dependency"},
        {name: "Deploy / verify", color: "ORANGE", description: "Merged; staging smoke pending"},
        {name: "Done", color: "GREEN", description: "Merged, CI green, verified"}
      ]
    }
  }' | gh api graphql --input -
}

update_readme() {
  local project_id readme_file
  project_id="$(gh project view "$PROJECT_NUMBER" --owner "$OWNER" --format json --jq .id)"
  readme_file="${ROOT}/docs/project-board.md"
  jq -n --arg projectId "$project_id" --rawfile readme "$readme_file" '{
    query: "mutation($projectId: ID!, $readme: String!) { updateProjectV2(input: { projectId: $projectId, readme: $readme }) { projectV2 { id title } } }",
    variables: { projectId: $projectId, readme: $readme }
  }' | gh api graphql --input -
}

create_view() {
  local name="$1" layout="$2" filter="$3"
  jq -n --arg name "$name" --arg layout "$layout" --arg filter "$filter" \
    '{name: $name, layout: $layout, filter: $filter}' \
    | gh api -X POST -H "X-GitHub-Api-Version:2022-11-28" \
      "/orgs/${OWNER}/projectsV2/${PROJECT_NUMBER}/views" --input -
}

create_views() {
  local repo_filter="repo:${REPO}"
  # Idempotent: skip if a view with the same name already exists.
  local existing_names
  existing_names="$(gh api graphql -f query="
    query { organization(login: \"${OWNER}\") {
      projectV2(number: ${PROJECT_NUMBER}) {
        views(first: 30) { nodes { name } }
      }
    }}" --jq '.data.organization.projectV2.views.nodes[].name' 2>/dev/null || true)"

  create_view_if_missing() {
    local name="$1" layout="$2" filter="$3"
    if echo "$existing_names" | rg -qx "$name"; then
      echo "View exists, skipping: $name"
      return 0
    fi
    echo "Creating view: $name"
    create_view "$name" "$layout" "$filter" \
      | jq -r '"\(.name) → \(.html_url)"'
  }

  create_view_if_missing "Board" "board" "$repo_filter"
  create_view_if_missing "Active sprint" "board" 'status:"Ready","In progress","In review"'
  create_view_if_missing "Deploy queue" "table" 'status:"Deploy / verify"'
  create_view_if_missing "Deploy label" "table" 'label:deploy -status:Done'
  create_view_if_missing "By app" "table" 'label:app:chat-rag,app:admin,app:infra'
  create_view_if_missing "Evolve cycles" "table" "label:evolve"
  create_view_if_missing "Bugs" "table" "label:bug,hotfix"
  create_view_if_missing "Blocked" "board" "status:Blocked"
  create_view_if_missing "All items" "table" "$repo_filter"
}

main() {
  require_project_scope
  echo "Creating/updating repo labels..."
  create_labels
  echo "Linking repo to project..."
  gh project link "$PROJECT_NUMBER" --owner "$OWNER" --repo "$REPO" 2>/dev/null || true
  echo "Updating Status field options..."
  update_status_options "$(fetch_status_field_id)"
  echo "Updating project README..."
  update_readme
  echo "Creating project views (REST; group-by must be set in UI for Board)..."
  create_views
  echo "Done."
  gh project field-list "$PROJECT_NUMBER" --owner "$OWNER" --format json \
    --jq '.fields[] | select(.name == "Status")'
}

main "$@"
