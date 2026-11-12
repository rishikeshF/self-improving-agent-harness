"""The boundary between our code and the language model.

Nodes only depend on the LLM protocol below, so tests can pass in FakeLLM
and never call a real model.
"""
import json
import os
import re
from typing import Protocol


class LLM(Protocol):
    def complete(self, prompt: str, *, system: str | None = None) -> str: ...


class AnthropicLLM:
    """The real model. The anthropic SDK is imported inside __init__ so tests never need it installed."""

    def __init__(self, model_name: str | None = None, max_tokens: int = 1024, timeout_seconds: float = 30.0):
        import anthropic  # optional dependency: uv sync --extra llm

        self.anthropic_client = anthropic.Anthropic(timeout=timeout_seconds, max_retries=2)
        self.model_name = model_name or os.environ.get("APP_MODEL", "claude-sonnet-5-5")
        self.max_tokens = max_tokens

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        model_response = self.anthropic_client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )

        # The response is a list of content blocks; we only want the text ones.
        text_parts = []
        for content_block in model_response.content:
            if getattr(content_block, "type", "") == "text":
                text_parts.append(content_block.text)
        return "".join(text_parts)


def parse_json_object_from_model_reply(model_reply: str) -> dict | None:
    """Find the first JSON object in a model reply and return it as a dict.

    Models often wrap JSON in extra text or code fences, so we search for the
    outermost {...} instead of parsing the whole reply. Returns None when there
    is no valid JSON object, so callers can treat it as malformed output.
    """
    json_object_match = re.search(r"\{.*\}", model_reply, re.DOTALL)
    if json_object_match is None:
        return None

    try:
        parsed_json = json.loads(json_object_match.group(0))
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed_json, dict):
        return None
    return parsed_json
