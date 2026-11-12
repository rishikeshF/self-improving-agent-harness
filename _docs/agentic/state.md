# State contract

Owner: architect. Engineers read this; they do not change it (comment on the issue instead).
`src/app/state.py` must match this table exactly.

## Keys
| Key | Type | Written by | Reducer | Notes |
|---|---|---|---|---|
| `input` | `str` | entry | overwrite | raw user request |
| `messages` | `list[dict]` | any node | append (`operator.add`) | `{role, content}` |
| `plan` | `list[str]` | `planner` | overwrite | |
| `tool_results` | `list[dict]` | `act` | append | `{tool, args, ok, output, error}` |
| `iterations` | `int` | `act` | overwrite (+1) | used by stop condition |
| `done` | `bool` | `act` | overwrite | model says no more tool calls needed |
| `final` | `str \| None` | `finish` | overwrite | the answer / artifact |
| `error` | `str \| None` | any node | overwrite | set when giving up |

## Invariants
- `iterations <= MAX_ITERATIONS` (see `graph.md`)
- Nodes return partial updates only (the keys they own), never the full state.
- No node reads a key it does not list as an input in `graph.md`.

## Change log
`HH:MM | change | why`
