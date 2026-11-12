---
description: Open lane worktrees and run engineer -> QA loops in parallel. Usage /lanes tools:02 graph:03 evals:04
---

Arguments are `lane:issue` pairs: $ARGUMENTS

Precondition: issue 01 (contracts) is closed and merged. If not, stop and say so.

For each pair, in parallel:
1. Run `scripts/lane.sh <lane>` (idempotent; creates `.worktrees/<lane>` on branch `lane/<lane>` from main).
2. Launch an `engineer` subagent with: the issue file path and the worktree path `.worktrees/<lane>`. Launch all engineers in ONE message so they run concurrently.

As each engineer returns (do not wait for the others):
3. Launch a `qa` subagent for that issue with the same worktree path.
4. On FAIL: relaunch the `engineer` for that lane with the QA report. Max 3 rounds, then stop that lane and tell me.
5. On PASS: tell me it is ready to merge and show `git -C .worktrees/<lane> log --oneline main..HEAD`. Do not merge without my go-ahead unless I said "auto-merge".

Log every launch, verdict and retry in `_docs/agent-log.md`.
When I approve a merge: `scripts/merge-lane.sh <lane>`, then `make test` on main, then set the issue `Status: closed` and commit `NN: close`.
