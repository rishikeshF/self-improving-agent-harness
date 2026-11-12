# Process

## Roles
| Role | Definition | Does | Never |
|---|---|---|---|
| Orchestrator | the main session | picks issues, launches subagents, merges lanes, closes issues | writes feature code, grooms, tests |
| PM | `.claude/agents/pm.md` | turns rough issues into checkable ones | writes code |
| Architect | `.claude/agents/architect.md` | freezes state, graph, tool contracts + skeleton | implements node logic |
| Engineer | `.claude/agents/engineer.md` | implements one groomed issue in its lane | edits criteria or shared contracts, closes issues |
| QA | `.claude/agents/qa.md` | verifies criteria, writes PASS/FAIL report | fixes code |
| Eval engineer | `.claude/agents/eval-engineer.md` | golden set, rubric, eval runner | changes the agent to pass evals |
| Retro | `.claude/agents/retro.md` | finds repeated failure modes, proposes up to 3 fixes | edits the files it proposes to change, weakens tests |

## Lifecycle (per issue)
1. Orchestrator picks the next open issue.
2. PM grooms it (never skipped; batch-groom in parallel at the start).
3. Engineer implements it in its lane worktree.
4. QA verifies it and writes `_docs/qa/NN.md`.
5. FAIL: back to step 3 with the QA report as input (max 3 rounds, then escalate to the human).
6. PASS: orchestrator merges the lane, runs `make test` on main, sets issue `Status: closed`.
7. Repeat until no open issues.

Graph: `PM -> Engineer -> QA`, with a FAIL edge back to Engineer.

## Phases in a timed session
| Phase | Parallel? | Output |
|---|---|---|
| 0. Read BRIEF, brainstorm, `_docs/plan.md` | no | plan + stack, committed |
| 1. Backlog: 6 to 8 issues | no | `_docs/issues/NN-*.md` |
| 2. Groom all issues | yes, one PM subagent per issue | groomed issues |
| 3. Contracts + skeleton (issue 01) | no, architect only | state, graph, tools docs + passing test, merged |
| 4. Lanes | yes, 2 to 3 engineer subagents | merged features |
| 5. Integration + evals | partly | green `make test`, `make eval` report |
| 6. README + submit | no | README "How I worked with agents" |

Rule: no lanes open before phase 3 is merged. Shared contracts first, then parallel work.

## Lanes (parallel engineers)
- One lane = one git worktree inside this folder at `.worktrees/<lane>` on branch `lane/<lane>`. Create with `scripts/lane.sh <lane>`.
- Each lane owns a disjoint set of files (write the ownership in the issue Constraints). Two lanes never edit the same file.
- Typical split for an agentic system:
  - lane `tools`: `src/app/tools/`
  - lane `graph`: `src/app/nodes/`, `src/app/graph.py`, `prompts/`
  - lane `evals`: `evals/`, `src/app/cli.py`
- Merge a lane with `scripts/merge-lane.sh <lane>` only after QA PASS. Merge one lane at a time, run `make test` after each.
- Max 3 lanes. The human reviewing diffs is the bottleneck, not the agents.

## Loops and stop conditions
- Agent loop: each subagent works until its issue's "Done when" holds.
- Verification loop: QA report gates every merge. The Stop hook (`.claude/hooks/goal_check.py`) blocks the orchestrator from stopping while the active goal's check command fails.
- Set a goal with `/goal <text> | <check command>`. Clear it with `/goal off`. Stop conditions must be checkable by a command, never "make it better".
- Hill-climbing (`/retro`): the `retro` subagent reads QA failures, the agent log, failing eval traces and past fixes (`scripts/collect_retro_evidence.py`), names repeated failure modes, and proposes up to 3 exact edits to `AGENTS.md`, subagent files, prompts or tool descriptions in `_docs/retros/`. The human approves each one. Prompt and tool changes are kept only if `scripts/compare_eval_runs.py` shows no regression; otherwise they are reverted and the rejection is recorded.
- Run `/retro` after every 2 QA FAILs, after each `make eval`, and before writing the final README.
- Manual corrections still count: when you correct an agent yourself, log it in `_docs/agent-log.md` so the next retro sees it.

```
event (QA FAIL / eval run)
  -> verification loop (QA, Stop hook) wraps the agent loop (each subagent)
  -> hill-climbing loop (/retro): evidence -> proposal -> human approval -> eval regression check -> commit or revert
```

## Evidence (what reviewers will see)
- `_docs/retros/` shows how the system improved itself, including rejected changes.
- `_docs/issues/` and `_docs/qa/` show the flow.
- Commits `NN: ...` and `process: ...` show the order of work and the learning loop.
- `_docs/agent-log.md` feeds the README section "How I worked with agents".
