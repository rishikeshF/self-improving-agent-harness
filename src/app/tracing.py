"""Minimal tracing: one JSON line per node call, in traces/<run_id>.jsonl.

Traces are what we read when an eval fails, to see which node went wrong and why.
"""
import json
import pathlib
import time
import uuid

TRACES_DIRECTORY = pathlib.Path(__file__).resolve().parents[2] / "traces"


class Tracer:
    def __init__(self, run_id: str | None = None, traces_directory: pathlib.Path = TRACES_DIRECTORY):
        self.run_id = run_id or time.strftime("%H%M%S-") + uuid.uuid4().hex[:6]
        traces_directory.mkdir(exist_ok=True)
        self.trace_file_path = traces_directory / f"{self.run_id}.jsonl"

    def record_node_call(
        self,
        node_name: str,
        state_before_node: dict,
        node_state_update: dict,
        duration_milliseconds: float,
        error_message: str | None = None,
    ) -> None:
        trace_line = {
            "node": node_name,
            "ms": round(duration_milliseconds, 1),
            "in": state_before_node,
            "out": node_state_update,
            "error": error_message,
        }
        with self.trace_file_path.open("a") as trace_file:
            trace_file.write(json.dumps(trace_line, default=str) + "\n")


def wrap_node_with_tracing(tracer: Tracer | None, node_name: str, node_function):
    """Return node_function unchanged if there is no tracer, otherwise a version that records each call."""
    if tracer is None:
        return node_function

    def traced_node_function(state):
        start_time = time.perf_counter()
        try:
            node_state_update = node_function(state)
        except Exception as node_exception:
            elapsed_milliseconds = (time.perf_counter() - start_time) * 1000
            tracer.record_node_call(node_name, dict(state), {}, elapsed_milliseconds, repr(node_exception))
            raise

        elapsed_milliseconds = (time.perf_counter() - start_time) * 1000
        tracer.record_node_call(node_name, dict(state), node_state_update, elapsed_milliseconds)
        return node_state_update

    return traced_node_function
