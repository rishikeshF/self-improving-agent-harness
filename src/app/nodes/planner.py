"""Planner node: turns the user request into a short list of steps."""
from app.llm import LLM
from app.prompts import load_prompt
from app.state import State


def make_planner_node(llm: LLM):
    def planner_node(state: State) -> dict:
        user_request = state["input"]
        model_reply = llm.complete(load_prompt("planner", input=user_request))

        # The prompt asks for one step per line; strip bullet characters the model may add anyway.
        plan_steps = []
        for reply_line in model_reply.splitlines():
            cleaned_step = reply_line.strip().strip("-* ").strip()
            if cleaned_step:
                plan_steps.append(cleaned_step)

        # If the model returned nothing usable, fall back to the request itself as a single step.
        if not plan_steps:
            plan_steps = [user_request]

        return {
            "plan": plan_steps,
            "messages": [{"role": "planner", "content": model_reply}],
        }

    return planner_node
