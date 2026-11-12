#!/usr/bin/env bash
# Create (or refresh) a lane worktree INSIDE this folder: .worktrees/<lane> on branch lane/<lane>.
# Inside the folder on purpose: the interview recorder only captures this folder.
set -euo pipefail
lane="${1:?usage: scripts/lane.sh <lane>}"
root="$(git rev-parse --show-toplevel)"
base="$(git -C "$root" symbolic-ref --short HEAD)"
wt="$root/.worktrees/$lane"

if [ -d "$wt" ]; then
  if [ -z "$(git -C "$wt" status --porcelain)" ]; then
    git -C "$wt" rebase -q "$base" && echo "lane $lane: refreshed on $base"
  else
    echo "lane $lane: exists with uncommitted changes, not refreshed"
  fi
else
  mkdir -p "$root/.worktrees"
  if git -C "$root" show-ref --quiet "refs/heads/lane/$lane"; then
    git -C "$root" worktree add -q "$wt" "lane/$lane"
  else
    git -C "$root" worktree add -q -b "lane/$lane" "$wt" "$base"
  fi
  echo "lane $lane: created at .worktrees/$lane (branch lane/$lane from $base)"
fi

if [ -f "$wt/pyproject.toml" ] && command -v uv >/dev/null; then
  (cd "$wt" && uv sync -q) && echo "lane $lane: deps synced"
fi
