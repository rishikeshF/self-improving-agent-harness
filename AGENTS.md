# AGENTS.md

Shared context for every agent (orchestrator and subagents). Keep it short. Correct it whenever a session needs the same correction twice, and commit that fix as `process: <what changed>`.

## Project
- What we are building: see `_docs/plan.md` (source of truth for scope).
- The exercise brief is `BRIEF.md`. If anything here conflicts with `BRIEF.md` or the kit `README.md`, they win.

## Commands
- Install: `uv sync`
- Fast tests (no network, fake LLM): `make test`
- One test file: `uv run pytest tests/test_x.py -q`
- Evals (may call a real model): `make eval`
- Lint: `make lint`

## Rules
- Python 3.11+. Dependencies go in `pyproject.toml`. Ask the orchestrator before adding one.
- Never call a real LLM in `make test`. Use `tests/fakes.py::FakeLLM`.
- Shared contracts (`src/app/state.py`, tool signatures in `_docs/agentic/tools.md`) change only through the architect. Engineers comment on the issue instead.
- Stay inside the files listed in your issue's Constraints.
- Commit small and often: `NN: <what>` where NN is the issue number.
- Do not touch `.interview/`, and do not disable anything in it.

## Code readability (IMPORTANT: clarity is the top priority)
A human reviewer with zero context must understand every line on first read. Clear beats clever, always.

Naming
- Be as clear and specific as possible with variable, function and class names. The name alone should tell a newcomer what it holds or does.
- Prefer longer names when they add clarity. No single-character or cryptic names, including loop variables, lambdas and exception handlers (`for issue_file in issue_files`, `except ValueError as parse_error`, not `for f in fs`, `except Exception as e`).
- Example: `original_question_last_answered_date`, not `orig_answered`.
- When passing arguments, keep the caller's variable name. If you have `current_tool_result`, pass `current_tool_result=current_tool_result`, not `result=` or `res=`.
- Functions are named for what they do: `parse_tool_call_from_model_reply`, not `parse` or `handle`.

Structure
- Write more lines if it makes the code easier to follow. No nested comprehensions, chained ternaries, clever one-liners, or `and`/`or` tricks for control flow.
- One function does one thing. If you need "and" to describe it, split it.
- Use intermediate variables to name steps instead of nesting calls.
- Plain functions and plain data first. No metaclasses, decorators, abstract base classes or extra layers unless the issue requires them. No speculative abstractions "for later".
- Type hints on every function signature.
- Early returns over deep `if` nesting.

Comments
- When a name cannot fully explain something, add a comment saying what happens and WHY (the reason, the edge case, the decision).
- Each module starts with a one-to-three-line docstring saying what it is for.
- Do not write comments that only repeat the code.

Before committing, reread your diff as a reviewer seeing it for the first time and rename anything unclear.

## Process
- How work flows, roles, lanes: `_docs/process.md`
- Issue format: `_docs/task-template.md`; issues live in `_docs/issues/`
- QA reports: `_docs/qa/NN.md`
- Retro proposals (self-improvement history): `_docs/retros/`

## Load when relevant
- Building or changing graph state, nodes or routing: read `_docs/agentic/state.md` and `_docs/agentic/graph.md`
- Building or changing a tool: read `_docs/agentic/tools.md`
- Writing evals or judging agent quality: read `_docs/agentic/evals.md`
- Making a non-obvious decision: add a line to `_docs/decisions.md`
