# 01. Contracts and skeleton

Status: open
Lane: main
Depends on: none

## Goal
Freeze the shared contracts so lanes can work in parallel without colliding, and have an end-to-end graph that runs with a fake LLM.

## Acceptance criteria
- [ ] `_docs/agentic/state.md` filled: every state key, type, which node writes it, reducer
- [ ] `_docs/agentic/graph.md` filled: nodes, edges, routing conditions, stop conditions, limits
- [ ] `_docs/agentic/tools.md` filled: every tool with input/output schema, errors, side effects
- [ ] `src/app/state.py` matches `state.md`
- [ ] Every node and tool exists as a stub with the final signature
- [ ] `make test` passes, including one end-to-end test through the graph with `FakeLLM`

## Out of scope
- Real node logic, real prompts, real tool implementations (lane issues)

## Constraints
- Files: `_docs/agentic/*`, `src/app/**`, `tests/test_graph.py`
- Keep the LLM behind the `LLM` protocol in `src/app/llm.py`

## Done when
Criteria checked, merged to main, QA PASS.

## Notes
