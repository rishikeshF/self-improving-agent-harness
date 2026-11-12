"""Loads prompt templates from prompts/*.md.

Prompts live in files (not in code) so changes to them show up as clear diffs
and can be evaluated on their own.
"""
import pathlib

PROMPTS_DIRECTORY = pathlib.Path(__file__).resolve().parents[2] / "prompts"


def load_prompt(prompt_name: str, **template_values: object) -> str:
    """Read prompts/<prompt_name>.md and replace each {{placeholder}} with its value."""
    prompt_text = (PROMPTS_DIRECTORY / f"{prompt_name}.md").read_text()

    for placeholder_name, placeholder_value in template_values.items():
        placeholder = "{{" + placeholder_name + "}}"
        prompt_text = prompt_text.replace(placeholder, str(placeholder_value))

    return prompt_text
