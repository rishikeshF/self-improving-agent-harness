# Evals

Two layers. Both must exist before you claim the agent works.

## 1. Deterministic tests (`make test`)
- Run with `FakeLLM` scripted responses. No network, no cost, seconds to run.
- Cover: routing (each edge taken), stop conditions (max iterations), tool errors, malformed LLM output.
- This is what the Stop hook and QA run on every change.

## 2. Behaviour evals (`make eval`)
- Golden set: `evals/golden.jsonl`, one case per line: `{"id", "input", "expected", "tags"}`.
  Aim for 10 to 20 cases, including edge cases and at least 3 adversarial ones.
- Graders, cheapest first:
  1. exact / contains / regex checks
  2. structural checks (valid JSON, required fields, tool called or not)
  3. LLM judge with a rubric in `evals/rubric.md` (score 1 to 5 plus reason)
- Output: `evals/results/<timestamp>.json` plus a summary table (pass rate per tag).
- Never change the agent and the golden set in the same commit.

## Hill-climbing loop
1. Run `make eval`, read failing traces in `traces/`.
2. Name the failure mode in `_docs/agent-log.md`.
3. Change one thing (prompt, tool description, routing) and commit.
4. Rerun `make eval`; keep only if pass rate did not drop on any tag.
