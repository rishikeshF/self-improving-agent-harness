"""Run the agent once from the terminal: uv run python -m app.cli "your request" """
import json
import sys

from app.graph import run_agent
from app.llm import AnthropicLLM
from app.tracing import Tracer


def main() -> None:
    command_line_request = " ".join(sys.argv[1:])
    user_request = command_line_request or "What is the capital of France?"

    tracer = Tracer()
    final_state = run_agent(AnthropicLLM(), user_request, tracer=tracer)

    run_summary = {
        "final": final_state.get("final"),
        "error": final_state.get("error"),
        "iterations": final_state.get("iterations"),
        "trace": str(tracer.trace_file_path),
    }
    print(json.dumps(run_summary, indent=2))


if __name__ == "__main__":
    main()
