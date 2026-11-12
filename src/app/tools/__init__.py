"""Tool registry: the tools the agent may call, and the one safe way to call them.

Contract (see _docs/agentic/tools.md): a tool never crashes the graph. Any
failure comes back as a ToolResult with ok=False and an error message.
"""
from collections.abc import Callable

from app.state import ToolResult
from app.tools.example_lookup import example_lookup

Tool = Callable[..., object]

DEFAULT_TOOL_REGISTRY: dict[str, Tool] = {
    "example_lookup": example_lookup,
}


def describe_tools_for_prompt(tool_registry: dict[str, Tool]) -> str:
    """One line per tool: its name and the first line of its docstring.

    The first docstring line is what the model reads to choose a tool, so it
    must say when to use the tool (see _docs/agentic/tools.md).
    """
    tool_description_lines = []
    for tool_name, tool_function in tool_registry.items():
        docstring = (tool_function.__doc__ or "").strip()
        first_docstring_line = docstring.splitlines()[0] if docstring else "(no description)"
        tool_description_lines.append(f"- {tool_name}: {first_docstring_line}")
    return "\n".join(tool_description_lines)


def call_tool_safely(tool_registry: dict[str, Tool], tool_name: str, tool_arguments: dict) -> ToolResult:
    """Run one tool and always return a ToolResult, even if the tool is unknown or raises."""
    if tool_name not in tool_registry:
        return {
            "tool": tool_name,
            "args": tool_arguments,
            "ok": False,
            "output": None,
            "error": f"unknown tool {tool_name!r}",
        }

    tool_function = tool_registry[tool_name]
    try:
        tool_output = tool_function(**tool_arguments)
    except Exception as tool_exception:  # deliberately broad: a broken tool must not crash the graph
        return {
            "tool": tool_name,
            "args": tool_arguments,
            "ok": False,
            "output": None,
            "error": f"{type(tool_exception).__name__}: {tool_exception}",
        }

    return {"tool": tool_name, "args": tool_arguments, "ok": True, "output": tool_output, "error": None}
