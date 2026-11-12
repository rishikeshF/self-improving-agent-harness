# Graph contract

Owner: architect.

## Nodes
| Node | Reads | Writes | Uses LLM? | Uses tools? | File |
|---|---|---|---|---|---|
| `planner` | input, messages | plan, messages | yes | no | `src/app/nodes/planner.py` |
| `act` | plan, tool_results, iterations | tool_results, iterations, done, messages | yes | yes | `src/app/nodes/act.py` |
| `finish` | input, tool_results | final | yes | no | `src/app/nodes/finish.py` |

## Edges
```
START -> planner -> act -> route_after_act
route_after_act:
  "act"    if not done and iterations < MAX_ITERATIONS
  "finish" otherwise
finish -> END
```

## Limits and stop conditions
- `MAX_ITERATIONS = 5` (config)
- LLM call timeout: 30s, retries: 2 with backoff
- Tool failure: recorded in `tool_results` with `ok=False`, never raises out of the graph
- Hitting the limit sets `error` and still goes to `finish` (graceful partial answer)

## Human-in-the-loop points (if any)
- e.g. interrupt before a tool with side effects

## Diagram
Keep a mermaid copy here once the graph is real; README links to it.
