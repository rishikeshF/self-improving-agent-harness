"""Example tool. Replace it with the real tools from the brief."""

STORED_FACTS_BY_KEY = {"capital_of_france": "Paris"}


def example_lookup(key: str) -> dict:
    """Look up a stored fact by key. Use when the plan needs a stored value; not for computation."""
    stored_value = STORED_FACTS_BY_KEY.get(key)
    was_found = stored_value is not None
    return {"found": was_found, "value": stored_value}
