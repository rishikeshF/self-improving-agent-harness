"""Finish node: writes the final answer from the tool results.

Also records an error if we got here because the iteration limit was hit,
rather than because the model said it was done.
"""
import json

from app.llm import LLM
from app.prompts import load_prompt
from app.state import State


def make_finish_node(llm: LLM, max_iterations: int):
    def finish_node(state: State) -> dict:
        model_said_done = bool(state.get("done"))
        reached_iteration_limit = state.get("iterations", 0) >= max_iterations
        stopped_because_of_limit = reached_iteration_limit and not model_said_done

        finish_prompt = load_prompt(
            "finish",
            input=state["input"],
            results=json.dumps(state.get("tool_results", []), default=str),
        )
        final_answer = llm.complete(finish_prompt).strip()

        state_update: dict = {"final": final_answer}
        if stopped_because_of_limit:
            state_update["error"] = f"stopped after {max_iterations} iterations"
        return state_update

    return finish_node
