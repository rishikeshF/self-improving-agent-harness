#!/usr/bin/env bash
# Merge a QA-passed lane into the main checkout, run tests, refresh the lane on the new main.
set -euo pipefail
lane="${1:?usage: scripts/merge-lane.sh <lane>}"
root="$(git rev-parse --show-toplevel)"
base="$(git -C "$root" symbolic-ref --short HEAD)"
cd "$root"

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "main checkout has uncommitted changes; commit first" >&2
  exit 1
fi

git merge --no-ff -q "lane/$lane" -m "merge lane/$lane"
echo "merged lane/$lane into $base"

if [ -f Makefile ]; then
  if make -s test; then echo "tests on $base: PASS"; else echo "tests on $base: FAIL (fix before merging more lanes)" >&2; exit 1; fi
fi

wt="$root/.worktrees/$lane"
[ -d "$wt" ] && [ -z "$(git -C "$wt" status --porcelain)" ] && git -C "$wt" rebase -q "$base" && echo "lane $lane refreshed on $base"
