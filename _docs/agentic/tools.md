# Tool contract

Owner: architect. The tool description is a prompt: the model picks tools from it, so write it for the model.

## Template (copy per tool)
### `tool_name`
- Description (what the model sees): one or two sentences, when to use it and when not to.
- Input: `{field: type, ...}` (pydantic model in `src/app/tools/<name>.py`)
- Output: `{field: type, ...}`
- Errors: which ones, and what the tool returns instead of raising
- Side effects: none | writes X | calls external API Y
- Idempotent: yes/no (safe to retry?)
- Deterministic fake for tests: how `tests/fakes.py` stubs it

## Tools
### `example_lookup`
- Description: Look up a fact by key. Use when the plan needs a stored value. Do not use for computation.
- Input: `{key: str}`
- Output: `{found: bool, value: str | None}`
- Errors: unknown key returns `found=False`, never raises
- Side effects: none
- Idempotent: yes
