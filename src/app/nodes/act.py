"""Act node: asks the model for the next tool call (or 'done'), then runs that tool.

Runs once per loop iteration. The router in graph.py decides whether to loop again.
"""
import json

from app.llm import LLM, parse_json_object_from_model_reply
from app.prompts import load_prompt
from app.state import State
from app.tools import Tool, call_tool_safely, describe_tools_for_prompt


def make_act_node(llm: LLM, tool_registry: dict[str, Tool]):
    def act_node(state: State) -> dict:
        iteration_count = state.get("iterations", 0) + 1

        act_prompt = load_prompt(
            "act",
            plan="\n".join(state.get("plan", [])),
            tools=describe_tools_for_prompt(tool_registry),
            results=json.dumps(state.get("tool_results", []), default=str),
        )
        model_reply = llm.complete(act_prompt)
        model_decision = parse_json_object_from_model_reply(model_reply)

        state_update: dict = {
            "iterations": iteration_count,
            "messages": [{"role": "act", "content": model_reply}],
        }

        # Malformed reply: record it as a failed step instead of raising,
        # so the loop can retry and the trace shows what went wrong.
        if model_decision is None:
            malformed_output_result = {
                "tool": "-",
                "args": {},
                "ok": False,
                "output": None,
                "error": "malformed model output",
            }
            state_update["tool_results"] = [malformed_output_result]
            return state_update

        if model_decision.get("done"):
            state_update["done"] = True
            return state_update

        requested_tool_name = str(model_decision.get("tool"))
        requested_tool_arguments = model_decision.get("args") or {}
        tool_result = call_tool_safely(tool_registry, requested_tool_name, requested_tool_arguments)
        state_update["tool_results"] = [tool_result]
        return state_update

    return act_node
