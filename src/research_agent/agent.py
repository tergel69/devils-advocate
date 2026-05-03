"""LangGraph agent definition - the multi-step research workflow."""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, StateGraph

from research_agent.nodes.planner import plan_research
from research_agent.nodes.reader import read_sources
from research_agent.nodes.searcher import execute_search
from research_agent.nodes.synthesizer import synthesize_findings
from research_agent.nodes.writer import write_report
from research_agent.state import AgentState


def should_continue_after_write(state: AgentState) -> Literal["plan", "end"]:
    """Decide whether to iterate or finish after writing."""
    status = state.get("status", "")
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 2)

    if status == "needs_improvement" and iteration < max_iterations:
        return "plan"
    return "end"


def should_continue_after_plan(state: AgentState) -> Literal["search", "end"]:
    """Decide whether to proceed with search or stop on error."""
    if state.get("status") == "error":
        return "end"
    return "search"


def build_research_graph() -> StateGraph:
    """Build the LangGraph research workflow.

    The workflow follows this pipeline:
        plan -> search -> read -> synthesize -> write -> (iterate or end)

    If the report quality is insufficient, the agent loops back to planning
    with refined queries for up to max_iterations cycles.
    """
    graph = StateGraph(AgentState)

    graph.add_node("plan", plan_research)
    graph.add_node("search", execute_search)
    graph.add_node("read", read_sources)
    graph.add_node("synthesize", synthesize_findings)
    graph.add_node("write", write_report)

    graph.set_entry_point("plan")

    graph.add_conditional_edges(
        "plan",
        should_continue_after_plan,
        {"search": "search", "end": END},
    )
    graph.add_edge("search", "read")
    graph.add_edge("read", "synthesize")
    graph.add_edge("synthesize", "write")

    graph.add_conditional_edges(
        "write",
        should_continue_after_write,
        {"plan": "plan", "end": END},
    )

    return graph


def create_agent():
    """Create and compile the research agent graph."""
    graph = build_research_graph()
    return graph.compile()
