"""End-to-end graph tests with FakeLLM: routing, stop conditions and failure modes."""
import json

from app.graph import build_agent_graph, run_agent
from app.tracing import Tracer
from tests.fakes import FakeLLM, make_replies_per_node

LOOKUP_CAPITAL_OF_FRANCE = '{"tool": "example_lookup", "args": {"key": "capital_of_france"}}'
MODEL_SAYS_DONE = '{"done": true}'


def test_happy_path_calls_tool_then_finishes():
    fake_llm = FakeLLM(make_replies_per_node(
        planner_reply="look up the capital",
        act_replies_in_order=[LOOKUP_CAPITAL_OF_FRANCE, MODEL_SAYS_DONE],
        finish_reply="Paris",
    ))

    final_state = run_agent(fake_llm, "capital of France?")

    first_tool_result = final_state["tool_results"][0]
    assert final_state["final"] == "Paris"
    assert first_tool_result["ok"] is True
    assert first_tool_result["output"]["value"] == "Paris"
    assert final_state["iterations"] == 2
    assert final_state.get("error") is None


def test_stops_at_max_iterations_and_records_error():
    fake_llm_that_never_finishes = FakeLLM(make_replies_per_node(
        planner_reply="loop forever",
        act_replies_in_order=['{"tool": "example_lookup", "args": {"key": "unknown_key"}}'],
        finish_reply="partial answer",
    ))

    final_state = run_agent(fake_llm_that_never_finishes, "never done", max_iterations=3)

    assert final_state["iterations"] == 3
    assert "3 iterations" in final_state["error"]
    assert final_state["final"] == "partial answer"


def test_malformed_model_output_is_recorded_not_raised():
    fake_llm = FakeLLM(make_replies_per_node(
        planner_reply="plan",
        act_replies_in_order=["not json at all", MODEL_SAYS_DONE],
        finish_reply="ok",
    ))

    final_state = run_agent(fake_llm, "anything")

    assert final_state["tool_results"][0]["error"] == "malformed model output"
    assert final_state["final"] == "ok"


def test_unknown_tool_and_raising_tool_do_not_crash_the_graph():
    def tool_that_always_raises(**_ignored_arguments):
        """Always fails, to check the graph survives broken tools."""
        raise RuntimeError("service down")

    fake_llm = FakeLLM(make_replies_per_node(
        planner_reply="plan",
        act_replies_in_order=[
            '{"tool": "tool_that_does_not_exist", "args": {}}',
            '{"tool": "tool_that_always_raises", "args": {}}',
            MODEL_SAYS_DONE,
        ],
        finish_reply="ok",
    ))

    final_state = run_agent(
        fake_llm,
        "anything",
        tool_registry={"tool_that_always_raises": tool_that_always_raises},
    )

    unknown_tool_result = final_state["tool_results"][0]
    raising_tool_result = final_state["tool_results"][1]
    assert "unknown tool 'tool_that_does_not_exist'" in unknown_tool_result["error"]
    assert "RuntimeError: service down" in raising_tool_result["error"]


def test_tracer_writes_one_line_per_node_call(tmp_path):
    fake_llm = FakeLLM(make_replies_per_node(
        planner_reply="plan",
        act_replies_in_order=[MODEL_SAYS_DONE],
        finish_reply="ok",
    ))
    tracer = Tracer(run_id="test-run", traces_directory=tmp_path)

    build_agent_graph(fake_llm, tracer=tracer).invoke({"input": "anything", "iterations": 0})

    trace_lines = tracer.trace_file_path.read_text().splitlines()
    traced_node_names = [json.loads(trace_line)["node"] for trace_line in trace_lines]
    assert traced_node_names == ["planner", "act", "finish"]
