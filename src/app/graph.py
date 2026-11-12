"""Builds the agent graph. Must match _docs/agentic/graph.md. Owner: architect.

Flow: START -> planner -> act -> (act again | finish) -> END
"""
from langgraph.graph import END, START, StateGraph

from app.llm import LLM
from app.nodes.act import make_act_node
from app.nodes.finish import make_finish_node
from app.nodes.planner import make_planner_node
from app.state import State
from app.tools import DEFAULT_TOOL_REGISTRY, Tool
from app.tracing import Tracer, wrap_node_with_tracing

DEFAULT_MAX_ITERATIONS = 5


def make_route_after_act(max_iterations: int):
    """Decide where to go after each act step: loop back to act, or move on to finish."""

    def route_after_act(state: State) -> str:
        model_said_done = bool(state.get("done"))
        reached_iteration_limit = state.get("iterations", 0) >= max_iterations
        if model_said_done or reached_iteration_limit:
            return "finish"
        return "act"

    return route_after_act


def build_agent_graph(
    llm: LLM,
    tool_registry: dict[str, Tool] | None = None,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    tracer: Tracer | None = None,
):
    if tool_registry is None:
        tool_registry = DEFAULT_TOOL_REGISTRY

    planner_node = make_planner_node(llm)
    act_node = make_act_node(llm, tool_registry)
    finish_node = make_finish_node(llm, max_iterations)

    graph_builder = StateGraph(State)
    graph_builder.add_node("planner", wrap_node_with_tracing(tracer, "planner", planner_node))
    graph_builder.add_node("act", wrap_node_with_tracing(tracer, "act", act_node))
    graph_builder.add_node("finish", wrap_node_with_tracing(tracer, "finish", finish_node))

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "act")
    graph_builder.add_conditional_edges(
        "act",
        make_route_after_act(max_iterations),
        {"act": "act", "finish": "finish"},
    )
    graph_builder.add_edge("finish", END)
    return graph_builder.compile()


def run_agent(llm: LLM, user_request: str, **graph_options) -> State:
    """Build the graph and run it once on one request. graph_options go to build_agent_graph."""
    agent_graph = build_agent_graph(llm, **graph_options)
    initial_state = {"input": user_request, "iterations": 0}

    # LangGraph's own safety net against infinite loops; our max_iterations normally stops first.
    langgraph_config = {"recursion_limit": 50}
    return agent_graph.invoke(initial_state, langgraph_config)
