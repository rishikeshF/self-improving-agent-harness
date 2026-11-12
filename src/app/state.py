"""Graph state. Must match _docs/agentic/state.md exactly. Owner: architect."""
import operator
from typing import Annotated, TypedDict


class ToolResult(TypedDict):
    tool: str
    args: dict
    ok: bool
    output: object
    error: str | None


class State(TypedDict, total=False):
    input: str
    messages: Annotated[list[dict], operator.add]
    plan: list[str]
    tool_results: Annotated[list[ToolResult], operator.add]
    iterations: int
    done: bool
    final: str | None
    error: str | None
