# Runbook: timed build session (e.g. a 4-hour take-home)

## Windows setup (do this days before)
1. PowerShell as admin: `wsl --install -d Ubuntu`, reboot, create the Linux user.
2. In Ubuntu: `sudo apt update && sudo apt install -y git python3 python3-venv openssl make unzip`, then install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`.
3. Install Claude Code inside WSL and sign in (`claude`).
4. VS Code on Windows + the "WSL" extension + the Claude Code extension. Open folders from Ubuntu with `code .` so VS Code runs in WSL.
5. Keep projects in the Linux filesystem (`~/projects`), not `/mnt/c/...` (slow, and file watching breaks).
6. Turn off sleep for the session.

## Before the clock starts
1. Get the project folder ready (for a take-home kit: download it and run its setup until it says ready).
2. Install the harness: `python3 ~/harness/scripts/install.py <project folder>`. It never overwrites existing files, merges `.claude/settings.json`, and appends to `.gitignore`.
3. `uv sync && make test` (expect all tests passing), then commit: `git add -A && git commit -m "process: add agent harness"`.
4. If the work needs a real model: export `ANTHROPIC_API_KEY` and run `uv sync --extra llm`.

If the environment records only the project folder: keep lanes inside it (`.worktrees/`, already the default) and run all agents as subagents of one root Claude Code session, so every transcript is captured.

## Timeline (4 hours)
| Time | Do | Parallel? |
|---|---|---|
| 0:00-0:20 | Read the brief. Brainstorm with Claude one question at a time. Fill `_docs/plan.md`. Commit. If the brief is not a Python agentic system, delete the skeleton and keep the process. | no |
| 0:20-0:30 | Write 6 to 8 rough issues in `_docs/issues/` (01 is always contracts) | no |
| 0:30-0:40 | `/groom` | yes, PMs |
| 0:40-1:00 | "Use the architect subagent on issue 01." Review, merge, close. | no |
| 1:00-2:50 | `/lanes tools:02 graph:03 evals:04`, then next issues. Review diffs, approve merges. `/retro` after every 2 QA FAILs. | yes, engineers + QA |
| 2:50-3:30 | Integration on main. `/goal everything green \| make test && make eval-smoke \| 6`. `make eval` with the real model, then `/retro`. | partly |
| 3:30-3:50 | Write the project README from `_docs/agent-log.md` and `_docs/retros/`: how to run, design, tradeoffs, evals, "How I worked with agents". | no |
| 3:50 | Submit. 10 minutes of buffer. | |

## Rules of thumb
- Ask about anything ambiguous in the brief early, not at hour 3.
- Pause the clock for breaks if the session allows it; do no work while paused.
- When you correct an agent, log it in `_docs/agent-log.md`; `/retro` turns repeated corrections into permanent fixes.
- Say in the final README that the harness was prepared before the session.
