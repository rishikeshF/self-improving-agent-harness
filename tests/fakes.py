"""Deterministic stand-ins for the real model. make test must never call a real LLM."""
from collections.abc import Callable

ACT_PROMPT_OPENING = "You are executing a plan"
PLANNER_PROMPT_OPENING = "Break the request"


class FakeLLM:
    """A scripted model.

    FakeLLM(["first reply", "second reply"])
        returns the replies in order; the last reply repeats once the list runs out.
    FakeLLM(reply_function)
        calls reply_function(prompt, system) to compute each reply.
    received_prompts records every prompt, so tests can assert on what the model was asked.
    """

    def __init__(self, scripted_replies: list[str] | Callable[[str, str | None], str]):
        self.scripted_replies = scripted_replies
        self.received_prompts: list[str] = []

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        self.received_prompts.append(prompt)

        if callable(self.scripted_replies):
            return self.scripted_replies(prompt, system)

        number_of_calls_so_far = len(self.received_prompts)
        reply_index = min(number_of_calls_so_far - 1, len(self.scripted_replies) - 1)
        return self.scripted_replies[reply_index]


def make_replies_per_node(
    planner_reply: str,
    act_replies_in_order: list[str],
    finish_reply: str,
) -> Callable[[str, str | None], str]:
    """Build a reply function that answers differently depending on which node is asking.

    The node is recognised by the opening words of its prompt (see prompts/*.md).
    Act replies are used in order; the last one repeats once the list runs out.
    """
    remaining_act_replies = list(act_replies_in_order)
    last_act_reply = act_replies_in_order[-1] if act_replies_in_order else '{"done": true}'

    def reply_for_prompt(prompt: str, _system: str | None) -> str:
        nonlocal last_act_reply

        if prompt.startswith(PLANNER_PROMPT_OPENING):
            return planner_reply

        if prompt.startswith(ACT_PROMPT_OPENING):
            if remaining_act_replies:
                last_act_reply = remaining_act_replies.pop(0)
            return last_act_reply

        return finish_reply

    return reply_for_prompt
