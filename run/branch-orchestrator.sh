#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="${CONFIG_FILE:-$ROOT_DIR/run/branch-components.conf}"
STATE_FILE="${STATE_FILE:-$ROOT_DIR/.git/branch-orchestrator.state}"
FORCE="${FORCE:-0}"

usage() {
  cat <<'EOF'
Usage:
  branch-orchestrator.sh status
  branch-orchestrator.sh save
  branch-orchestrator.sh restore
  branch-orchestrator.sh switch <branch>
  branch-orchestrator.sh pull [branch]
  branch-orchestrator.sh sync-main

Environment variables:
  CONFIG_FILE=<path>  Component config (default: run/branch-components.conf)
  STATE_FILE=<path>   Save/restore state file (default: .git/branch-orchestrator.state)
  FORCE=1             Allow switching with dirty worktrees
EOF
}

fail() {
  echo "ERROR: $*" >&2
  exit 1
}

warn() {
  echo "WARN: $*" >&2
}

info() {
  echo "INFO: $*"
}

require_git() {
  command -v git >/dev/null 2>&1 || fail "git is required"
}

component_lines() {
  [[ -f "$CONFIG_FILE" ]] || fail "config file not found: $CONFIG_FILE"
  grep -vE '^\s*#|^\s*$' "$CONFIG_FILE" || true
}

parse_line() {
  local line="$1"
  IFS='|' read -r name rel_path fallback <<<"$line"

  name="${name//[$'\t\r\n ']/}"
  rel_path="$(echo "$rel_path" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  fallback="${fallback//[$'\t\r\n ']/}"

  [[ -n "$name" ]] || return 1
  [[ -n "$rel_path" ]] || return 1
  [[ -n "$fallback" ]] || fallback="main"

  local abs_path="$ROOT_DIR/$rel_path"
  echo "$name|$abs_path|$fallback"
}

collect_components() {
  local line parsed
  while IFS= read -r line; do
    parsed="$(parse_line "$line" || true)"
    if [[ -n "$parsed" ]]; then
      echo "$parsed"
    fi
  done < <(component_lines)
}

is_git_repo() {
  local path="$1"
  git -C "$path" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

current_branch() {
  local path="$1"
  git -C "$path" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown"
}

dirty_state() {
  local path="$1"
  if [[ -n "$(git -C "$path" status --porcelain 2>/dev/null)" ]]; then
    echo "dirty"
  else
    echo "clean"
  fi
}

branch_exists_local() {
  local path="$1"
  local branch="$2"
  git -C "$path" show-ref --verify --quiet "refs/heads/$branch"
}

branch_exists_remote_tracking() {
  local path="$1"
  local branch="$2"
  git -C "$path" show-ref --verify --quiet "refs/remotes/origin/$branch"
}

checkout_branch() {
  local path="$1"
  local branch="$2"

  if branch_exists_local "$path" "$branch"; then
    git -C "$path" checkout "$branch" >/dev/null
    return 0
  fi

  if branch_exists_remote_tracking "$path" "$branch"; then
    git -C "$path" checkout -b "$branch" --track "origin/$branch" >/dev/null
    return 0
  fi

  return 1
}

do_status() {
  local has_rows=0
  printf "%-24s %-8s %-8s %s\n" "component" "exists" "state" "branch"
  printf "%-24s %-8s %-8s %s\n" "------------------------" "------" "------" "------"

  while IFS= read -r item; do
    IFS='|' read -r name path fallback <<<"$item"
    if [[ -d "$path" ]] && is_git_repo "$path"; then
      printf "%-24s %-8s %-8s %s\n" "$name" "yes" "$(dirty_state "$path")" "$(current_branch "$path")"
    else
      printf "%-24s %-8s %-8s %s\n" "$name" "no" "n/a" "n/a"
    fi
    has_rows=1
  done < <(collect_components)

  [[ "$has_rows" -eq 1 ]] || fail "no components found in $CONFIG_FILE"
}

do_save() {
  : > "$STATE_FILE"
  while IFS= read -r item; do
    IFS='|' read -r name path fallback <<<"$item"
    if [[ -d "$path" ]] && is_git_repo "$path"; then
      echo "$name|$path|$(current_branch "$path")" >> "$STATE_FILE"
    fi
  done < <(collect_components)
  info "saved branch state to $STATE_FILE"
}

do_restore() {
  [[ -f "$STATE_FILE" ]] || fail "state file not found: $STATE_FILE"

  local line name path branch
  local failures=0
  while IFS= read -r line; do
    IFS='|' read -r name path branch <<<"$line"
    [[ -n "$name" && -n "$path" && -n "$branch" ]] || continue

    if [[ ! -d "$path" ]] || ! is_git_repo "$path"; then
      warn "$name missing or not a git repo: $path"
      failures=$((failures + 1))
      continue
    fi

    local current
    current="$(current_branch "$path")"

    if [[ "$current" == "$branch" ]]; then
      info "$name already on $branch"
      continue
    fi

    if [[ "$FORCE" != "1" && "$(dirty_state "$path")" == "dirty" ]]; then
      warn "$name has uncommitted changes; skipping (set FORCE=1 to override)"
      failures=$((failures + 1))
      continue
    fi

    if checkout_branch "$path" "$branch"; then
      info "$name -> $branch"
    else
      warn "$name could not restore branch '$branch'"
      failures=$((failures + 1))
    fi
  done < "$STATE_FILE"

  [[ "$failures" -eq 0 ]] || fail "restore completed with $failures issue(s)"
}

do_switch() {
  local target_branch="$1"
  [[ -n "$target_branch" ]] || fail "switch requires a target branch"

  local switched=0
  local skipped=0
  local missing=0

  while IFS= read -r item; do
    IFS='|' read -r name path fallback <<<"$item"

    if [[ ! -d "$path" ]] || ! is_git_repo "$path"; then
      warn "$name missing or not a git repo: $path"
      missing=$((missing + 1))
      continue
    fi

    local current
    current="$(current_branch "$path")"

    if [[ "$current" == "$target_branch" ]]; then
      info "$name already on $target_branch"
      switched=$((switched + 1))
      continue
    fi

    if [[ "$FORCE" != "1" && "$(dirty_state "$path")" == "dirty" ]]; then
      warn "$name has uncommitted changes; skipping (set FORCE=1 to override)"
      skipped=$((skipped + 1))
      continue
    fi

    if checkout_branch "$path" "$target_branch"; then
      info "$name -> $target_branch"
      switched=$((switched + 1))
      continue
    fi

    if checkout_branch "$path" "$fallback"; then
      info "$name -> $fallback (fallback)"
      switched=$((switched + 1))
      continue
    fi

    warn "$name could not switch to '$target_branch' or fallback '$fallback'"
    skipped=$((skipped + 1))
  done < <(collect_components)

  info "switch summary: switched=$switched skipped=$skipped missing=$missing"
  [[ "$switched" -gt 0 ]] || fail "no components switched"
}

do_pull() {
  local requested_branch="${1:-}"
  local updated=0
  local skipped=0
  local missing=0

  while IFS= read -r item; do
    IFS='|' read -r name path fallback <<<"$item"

    if [[ ! -d "$path" ]] || ! is_git_repo "$path"; then
      warn "$name missing or not a git repo: $path"
      missing=$((missing + 1))
      continue
    fi

    if [[ "$FORCE" != "1" && "$(dirty_state "$path")" == "dirty" ]]; then
      warn "$name has uncommitted changes; skipping pull (set FORCE=1 to override)"
      skipped=$((skipped + 1))
      continue
    fi

    local branch
    branch="$(current_branch "$path")"

    if [[ "$branch" == "HEAD" ]]; then
      warn "$name is in detached HEAD; skipping"
      skipped=$((skipped + 1))
      continue
    fi

    if [[ -n "$requested_branch" && "$branch" != "$requested_branch" ]]; then
      if checkout_branch "$path" "$requested_branch"; then
        branch="$requested_branch"
        info "$name switched to $branch before pull"
      else
        warn "$name could not switch to requested branch '$requested_branch'; skipping"
        skipped=$((skipped + 1))
        continue
      fi
    fi

    git -C "$path" fetch --prune origin >/dev/null

    if branch_exists_remote_tracking "$path" "$branch"; then
      if git -C "$path" pull --ff-only origin "$branch" >/dev/null; then
        info "$name pulled origin/$branch"
        updated=$((updated + 1))
      else
        warn "$name pull failed on $branch"
        skipped=$((skipped + 1))
      fi
    else
      warn "$name has no origin/$branch; skipping"
      skipped=$((skipped + 1))
    fi
  done < <(collect_components)

  info "pull summary: updated=$updated skipped=$skipped missing=$missing"
  [[ "$updated" -gt 0 ]] || fail "no components pulled"
}

main() {
  require_git

  local cmd="${1:-}"
  case "$cmd" in
    status)
      do_status
      ;;
    save)
      do_save
      ;;
    restore)
      do_restore
      ;;
    switch)
      do_switch "${2:-}"
      ;;
    pull)
      do_pull "${2:-}"
      ;;
    sync-main)
      do_switch "main"
      ;;
    -h|--help|help|"")
      usage
      ;;
    *)
      fail "unknown command: $cmd"
      ;;
  esac
}

main "$@"
